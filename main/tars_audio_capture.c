#include "tars_audio_capture.h"

#include <inttypes.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>

#include "bsp/esp32_p4_platform.h"
#include "esp_codec_dev.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sdkconfig.h"

#define TARS_AUDIO_REPORT_FRAMES (1000U / TARS_AUDIO_FRAME_MS)
#define TARS_AUDIO_CAPTURE_CORE 1
#define TARS_AUDIO_CAPTURE_PRIORITY 20
#define TARS_AUDIO_CAPTURE_STACK_BYTES 4096
#define TARS_AUDIO_CLIP_LEVEL 32760

static const char *TAG = "tars_audio";

typedef struct {
    esp_codec_dev_handle_t input_codec;
    esp_codec_dev_handle_t output_codec;
    TaskHandle_t capture_task;
    tars_audio_ring_t ring;
    volatile bool playback_active;
    uint64_t read_errors;
    uint32_t next_sequence;
} tars_audio_context_t;

static tars_audio_context_t s_audio;

static void tars_audio_capture_task(void *argument)
{
    tars_audio_context_t *context = (tars_audio_context_t *)argument;
    tars_audio_frame_t frame = {0};
    uint64_t sum_squares = 0;
    uint32_t sample_count = 0;
    uint32_t clipped_samples = 0;
    int32_t peak = 0;
    uint32_t report_frames = 0;

    while (true) {
        if (context->playback_active) {
            vTaskDelay(pdMS_TO_TICKS(TARS_AUDIO_FRAME_MS));
            continue;
        }
        const int result = esp_codec_dev_read(context->input_codec, frame.samples,
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
        for (size_t index = 0; index < TARS_AUDIO_SAMPLES_PER_FRAME; ++index) {
            const int32_t sample = frame.samples[index];
            const int32_t magnitude = sample == INT16_MIN ? 32768 : abs(sample);
            peak = magnitude > peak ? magnitude : peak;
            clipped_samples += magnitude >= TARS_AUDIO_CLIP_LEVEL;
            sum_squares += (uint64_t)(sample * sample);
            sample_count++;
        }
        report_frames++;

        if (report_frames >= TARS_AUDIO_REPORT_FRAMES) {
            tars_audio_ring_stats_t stats = {0};
            tars_audio_ring_get_stats(&context->ring, &stats);
            const double rms = sample_count
                                   ? sqrt((double)sum_squares / sample_count)
                                   : 0.0;
            const double peak_dbfs = peak
                                         ? 20.0 * log10((double)peak / 32768.0)
                                         : -INFINITY;
            const double rms_dbfs = rms
                                        ? 20.0 * log10(rms / 32768.0)
                                        : -INFINITY;
            const double clipped = sample_count
                                       ? (double)clipped_samples * 100.0 / sample_count
                                       : 0.0;
            ESP_LOGI(TAG,
                     "capture queue=%u/%u dropped=%" PRIu64
                     " peak=%.1f dBFS rms=%.1f dBFS clipped=%.4f%%",
                     (unsigned)stats.depth, (unsigned)stats.capacity,
                     stats.dropped_oldest, peak_dbfs, rms_dbfs, clipped);
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
    if (s_audio.capture_task != NULL || s_audio.input_codec != NULL ||
        s_audio.output_codec != NULL) {
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
            .invert_flags = {0},
        },
    };

    ESP_RETURN_ON_ERROR(bsp_i2c_init(), TAG, "Board I2C initialization failed");
    ESP_RETURN_ON_ERROR(bsp_audio_init(&i2s_config), TAG,
                        "Board I2S initialization failed");

    s_audio.input_codec = bsp_audio_codec_microphone_init();
    s_audio.output_codec = bsp_audio_codec_speaker_init();
    if (s_audio.input_codec == NULL || s_audio.output_codec == NULL) {
        return ESP_FAIL;
    }
    esp_codec_dev_sample_info_t format = {
        .bits_per_sample = TARS_AUDIO_BITS_PER_SAMPLE,
        .channel = TARS_AUDIO_CHANNELS,
        .channel_mask = 0,
        .sample_rate = TARS_AUDIO_SAMPLE_RATE_HZ,
        .mclk_multiple = 0,
    };
    ESP_RETURN_ON_ERROR(esp_codec_dev_open(s_audio.input_codec, &format), TAG,
                        "ES8311 microphone open failed");
    ESP_RETURN_ON_ERROR(esp_codec_dev_open(s_audio.output_codec, &format), TAG,
                        "ES8311 speaker open failed");
    ESP_RETURN_ON_ERROR(
        esp_codec_dev_set_in_gain(s_audio.input_codec,
                                  CONFIG_TARS_AUDIO_MIC_GAIN_DB),
        TAG, "Microphone gain configuration failed");
    ESP_RETURN_ON_ERROR(
        esp_codec_dev_set_out_vol(s_audio.output_codec,
                                  CONFIG_TARS_AUDIO_SPEAKER_VOLUME),
        TAG, "Speaker volume configuration failed");
    ESP_RETURN_ON_ERROR(
        tars_audio_ring_init(&s_audio.ring, CONFIG_TARS_AUDIO_RING_FRAMES),
        TAG, "Audio queue allocation failed");

    if (xTaskCreatePinnedToCore(tars_audio_capture_task, "audio_rx_task",
                                TARS_AUDIO_CAPTURE_STACK_BYTES, &s_audio,
                                TARS_AUDIO_CAPTURE_PRIORITY,
                                &s_audio.capture_task,
                                TARS_AUDIO_CAPTURE_CORE) != pdPASS) {
        return ESP_ERR_NO_MEM;
    }
    ESP_LOGI(TAG,
             "Audio ready: %u Hz, %u-bit mono, mic gain=%d dB, speaker=%d%%",
             TARS_AUDIO_SAMPLE_RATE_HZ, TARS_AUDIO_BITS_PER_SAMPLE,
             CONFIG_TARS_AUDIO_MIC_GAIN_DB,
             CONFIG_TARS_AUDIO_SPEAKER_VOLUME);
    return ESP_OK;
}

bool tars_audio_capture_read(tars_audio_frame_t *frame, TickType_t timeout)
{
    return s_audio.ring.queue != NULL &&
           tars_audio_ring_pop(&s_audio.ring, frame, timeout);
}

void tars_audio_capture_flush(void)
{
    if (s_audio.ring.queue != NULL) {
        xQueueReset(s_audio.ring.queue);
    }
}

void tars_audio_capture_stats(tars_audio_ring_stats_t *stats)
{
    if (stats != NULL) {
        tars_audio_ring_get_stats(&s_audio.ring, stats);
    }
}

esp_err_t tars_audio_playback_begin(void)
{
    if (s_audio.output_codec == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    s_audio.playback_active = true;
    tars_audio_capture_flush();
    return ESP_OK;
}

esp_err_t tars_audio_playback_write(const void *pcm, size_t bytes)
{
    if (!s_audio.playback_active || pcm == NULL || bytes == 0) {
        return ESP_ERR_INVALID_STATE;
    }
    return esp_codec_dev_write(s_audio.output_codec, (void *)pcm, bytes);
}

void tars_audio_playback_end(void)
{
    s_audio.playback_active = false;
    tars_audio_capture_flush();
}
