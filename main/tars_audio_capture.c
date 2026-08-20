#include "tars_audio_capture.h"

#include <inttypes.h>
#include <math.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdint.h>

#include "bsp/esp32_p4_platform.h"
#include "esp_codec_dev.h"
#include "esp_err.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sdkconfig.h"

#include "tars_audio_frame.h"
#include "tars_audio_ring.h"

#define TARS_AUDIO_REPORT_FRAMES (1000U / TARS_AUDIO_FRAME_MS)
#define TARS_AUDIO_CAPTURE_CORE 1
#define TARS_AUDIO_DIAGNOSTIC_CORE 0
#define TARS_AUDIO_CAPTURE_PRIORITY 20
#define TARS_AUDIO_DIAGNOSTIC_PRIORITY 5
#define TARS_AUDIO_CAPTURE_STACK_BYTES 4096
#define TARS_AUDIO_DIAGNOSTIC_STACK_BYTES 4096
#define TARS_AUDIO_CLIP_LEVEL 32760

static const char *TAG = "tars_audio";

typedef struct {
    esp_codec_dev_handle_t codec;
    TaskHandle_t capture_task;
    TaskHandle_t diagnostic_task;
    tars_audio_ring_t ring;
    uint64_t read_errors;
    uint32_t next_sequence;
} tars_audio_context_t;

static tars_audio_context_t s_audio;

static void tars_audio_capture_task(void *argument)
{
    tars_audio_context_t *context = (tars_audio_context_t *)argument;
    tars_audio_frame_t frame = {0};

    while (true) {
        const int result = esp_codec_dev_read(context->codec, frame.samples,
                                              sizeof(frame.samples));
        if (result != ESP_CODEC_DEV_OK) {
            context->read_errors++;
            ESP_LOGE(TAG, "Microphone read failed: 0x%x (errors=%" PRIu64 ")",
                     result, context->read_errors);
            vTaskDelay(pdMS_TO_TICKS(TARS_AUDIO_FRAME_MS));
            continue;
        }

        frame.sequence = context->next_sequence++;
        frame.timestamp_us = esp_timer_get_time();
        if (!tars_audio_ring_push_latest(&context->ring, &frame)) {
            ESP_LOGE(TAG, "Audio queue rejected frame sequence=%" PRIu32,
                     frame.sequence);
        }
    }
}

static void tars_audio_diagnostic_task(void *argument)
{
    tars_audio_context_t *context = (tars_audio_context_t *)argument;
    tars_audio_frame_t frame;
    uint64_t sum_squares = 0;
    uint32_t sample_count = 0;
    uint32_t clipped_samples = 0;
    int32_t peak = 0;
    uint32_t report_frames = 0;
    uint32_t sequence_gaps = 0;
    uint32_t expected_sequence = 0;
    bool have_sequence = false;

    while (true) {
        if (!tars_audio_ring_pop(&context->ring, &frame, pdMS_TO_TICKS(1000))) {
            continue;
        }

        if (have_sequence && frame.sequence != expected_sequence) {
            sequence_gaps += frame.sequence - expected_sequence;
        }
        expected_sequence = frame.sequence + 1U;
        have_sequence = true;
        report_frames++;

        for (size_t index = 0; index < TARS_AUDIO_SAMPLES_PER_FRAME; ++index) {
            const int32_t sample = frame.samples[index];
            const int32_t magnitude = sample == INT16_MIN ? 32768 : abs(sample);
            if (magnitude > peak) {
                peak = magnitude;
            }
            if (magnitude >= TARS_AUDIO_CLIP_LEVEL) {
                clipped_samples++;
            }
            sum_squares += (uint64_t)(sample * sample);
            sample_count++;
        }

        if (report_frames >= TARS_AUDIO_REPORT_FRAMES) {
            tars_audio_ring_stats_t ring_stats = {0};
            tars_audio_ring_get_stats(&context->ring, &ring_stats);
            const double rms = sample_count > 0
                                   ? sqrt((double)sum_squares / (double)sample_count)
                                   : 0.0;
            const double peak_dbfs = peak > 0
                                         ? 20.0 * log10((double)peak / 32768.0)
                                         : -INFINITY;
            const double rms_dbfs = rms > 0.0
                                        ? 20.0 * log10(rms / 32768.0)
                                        : -INFINITY;
            const double clipped_percent = sample_count > 0
                                               ? ((double)clipped_samples * 100.0) /
                                                     (double)sample_count
                                               : 0.0;

            ESP_LOGI(TAG,
                     "capture frames=%" PRIu64 " queue=%u/%u dropped=%" PRIu64
                     " gaps=%u peak=%.1f dBFS rms=%.1f dBFS clipped=%.4f%% "
                     "stack_free=%u",
                     ring_stats.pushed, (unsigned)ring_stats.depth,
                     (unsigned)ring_stats.capacity, ring_stats.dropped_oldest,
                     sequence_gaps, peak_dbfs, rms_dbfs, clipped_percent,
                     (unsigned)uxTaskGetStackHighWaterMark(NULL));

            sum_squares = 0;
            sample_count = 0;
            clipped_samples = 0;
            peak = 0;
            report_frames = 0;
        }
    }
}

esp_err_t tars_audio_capture_start(void)
{
    if (s_audio.capture_task != NULL || s_audio.codec != NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    const i2s_std_config_t i2s_config = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(TARS_AUDIO_SAMPLE_RATE_HZ),
        .slot_cfg = I2S_STD_PHILIP_SLOT_DEFAULT_CONFIG(
            I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO),
        .gpio_cfg = {
            .mclk = BSP_I2S_MCLK,
            .bclk = BSP_I2S_SCLK,
            .ws = BSP_I2S_LCLK,
            .dout = BSP_I2S_DOUT,
            .din = BSP_I2S_DSIN,
            .invert_flags = {
                .mclk_inv = false,
                .bclk_inv = false,
                .ws_inv = false,
            },
        },
    };

    esp_err_t result = bsp_i2c_init();
    if (result != ESP_OK) {
        ESP_LOGE(TAG, "Board I2C initialization failed: %s", esp_err_to_name(result));
        return result;
    }

    result = bsp_audio_init(&i2s_config);
    if (result != ESP_OK) {
        ESP_LOGE(TAG, "Board I2S initialization failed: %s", esp_err_to_name(result));
        return result;
    }

    s_audio.codec = bsp_audio_codec_microphone_init();
    if (s_audio.codec == NULL) {
        ESP_LOGE(TAG, "ES8311 microphone device creation failed");
        return ESP_FAIL;
    }

    esp_codec_dev_sample_info_t format = {
        .bits_per_sample = TARS_AUDIO_BITS_PER_SAMPLE,
        .channel = TARS_AUDIO_CHANNELS,
        .channel_mask = 0,
        .sample_rate = TARS_AUDIO_SAMPLE_RATE_HZ,
        .mclk_multiple = 0,
    };

    result = esp_codec_dev_open(s_audio.codec, &format);
    if (result != ESP_CODEC_DEV_OK) {
        ESP_LOGE(TAG, "ES8311 microphone open failed: 0x%x", result);
        esp_codec_dev_delete(s_audio.codec);
        s_audio.codec = NULL;
        return result;
    }

    result = esp_codec_dev_set_in_gain(s_audio.codec, CONFIG_TARS_AUDIO_MIC_GAIN_DB);
    if (result != ESP_CODEC_DEV_OK) {
        ESP_LOGE(TAG, "ES8311 microphone gain configuration failed: 0x%x", result);
        esp_codec_dev_close(s_audio.codec);
        esp_codec_dev_delete(s_audio.codec);
        s_audio.codec = NULL;
        return result;
    }

    result = tars_audio_ring_init(&s_audio.ring, CONFIG_TARS_AUDIO_RING_FRAMES);
    if (result != ESP_OK) {
        ESP_LOGE(TAG, "Audio queue allocation failed: %s", esp_err_to_name(result));
        esp_codec_dev_close(s_audio.codec);
        esp_codec_dev_delete(s_audio.codec);
        s_audio.codec = NULL;
        return result;
    }

    const BaseType_t created = xTaskCreatePinnedToCore(
        tars_audio_capture_task,
        "audio_rx_task",
        TARS_AUDIO_CAPTURE_STACK_BYTES,
        &s_audio,
        TARS_AUDIO_CAPTURE_PRIORITY,
        &s_audio.capture_task,
        TARS_AUDIO_CAPTURE_CORE);
    if (created != pdPASS) {
        ESP_LOGE(TAG, "Failed to create audio_rx_task");
        esp_codec_dev_close(s_audio.codec);
        esp_codec_dev_delete(s_audio.codec);
        s_audio.codec = NULL;
        vQueueDelete(s_audio.ring.queue);
        s_audio.ring.queue = NULL;
        return ESP_ERR_NO_MEM;
    }

    const BaseType_t diagnostic_created = xTaskCreatePinnedToCore(
        tars_audio_diagnostic_task,
        "audio_diag_task",
        TARS_AUDIO_DIAGNOSTIC_STACK_BYTES,
        &s_audio,
        TARS_AUDIO_DIAGNOSTIC_PRIORITY,
        &s_audio.diagnostic_task,
        TARS_AUDIO_DIAGNOSTIC_CORE);
    if (diagnostic_created != pdPASS) {
        ESP_LOGE(TAG, "Failed to create audio_diag_task");
        vTaskDelete(s_audio.capture_task);
        s_audio.capture_task = NULL;
        esp_codec_dev_close(s_audio.codec);
        esp_codec_dev_delete(s_audio.codec);
        s_audio.codec = NULL;
        vQueueDelete(s_audio.ring.queue);
        s_audio.ring.queue = NULL;
        return ESP_ERR_NO_MEM;
    }

    ESP_LOGI(TAG,
             "Microphone diagnostic started: %u Hz, %u-bit, mono, %u ms frames, "
             "gain=%d dB, capture_core=%d, diagnostic_core=%d, queue=%d frames",
             TARS_AUDIO_SAMPLE_RATE_HZ, TARS_AUDIO_BITS_PER_SAMPLE,
             TARS_AUDIO_FRAME_MS, CONFIG_TARS_AUDIO_MIC_GAIN_DB,
             TARS_AUDIO_CAPTURE_CORE, TARS_AUDIO_DIAGNOSTIC_CORE,
             CONFIG_TARS_AUDIO_RING_FRAMES);
    return ESP_OK;
}
