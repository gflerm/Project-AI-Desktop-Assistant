#include "james_ptt_client.h"

#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "driver/gpio.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_timer.h"
#include "esp_websocket_client.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/task.h"
#include "sdkconfig.h"

#include "james_audio_capture.h"
#include "james_audio_frame.h"
#include "james_audio_ring.h"
#include "james_private_config.h"

#define JAMES_PROTOCOL_VERSION 1
#define JAMES_HEADER_BYTES 24
#define JAMES_KIND_MICROPHONE 1
#define JAMES_KIND_TTS 2
#define JAMES_FRAMES_PER_CHUNK 5
#define JAMES_PCM_BYTES_PER_CHUNK \
    (JAMES_FRAMES_PER_CHUNK * JAMES_AUDIO_BYTES_PER_FRAME)
#define JAMES_WS_READY_BIT BIT0
#define JAMES_WS_SPEAKING_BIT BIT1
#define JAMES_WS_BUFFER_BYTES 8192
#define JAMES_PTT_TASK_STACK 10240
#define JAMES_PTT_TASK_PRIORITY 10
#define JAMES_PTT_TASK_CORE 0
#define JAMES_BUTTON_DEBOUNCE_MS 30
#define JAMES_SEND_TIMEOUT_MS 3000

static const char *TAG = "james_ptt";

typedef struct {
    esp_websocket_client_handle_t websocket;
    EventGroupHandle_t events;
    TaskHandle_t task;
    uint32_t message_id;
    uint32_t utterance_id;
    char session_id[24];
    char headers[192];
    uint8_t receive[JAMES_WS_BUFFER_BYTES];
    size_t receive_length;
    int receive_opcode;
} james_ptt_context_t;

static james_ptt_context_t s_ptt;

static void write_be16(uint8_t *target, uint16_t value)
{
    target[0] = (uint8_t)(value >> 8);
    target[1] = (uint8_t)value;
}

static void write_be32(uint8_t *target, uint32_t value)
{
    target[0] = (uint8_t)(value >> 24);
    target[1] = (uint8_t)(value >> 16);
    target[2] = (uint8_t)(value >> 8);
    target[3] = (uint8_t)value;
}

static uint16_t read_be16(const uint8_t *source)
{
    return ((uint16_t)source[0] << 8) | source[1];
}

static uint32_t next_message_id(void)
{
    return ++s_ptt.message_id;
}

static int send_text(const char *text)
{
    if (!esp_websocket_client_is_connected(s_ptt.websocket)) {
        return -1;
    }
    return esp_websocket_client_send_text(
        s_ptt.websocket, text, strlen(text),
        pdMS_TO_TICKS(JAMES_SEND_TIMEOUT_MS));
}

static void send_hello(void)
{
    char json[320];
    snprintf(json, sizeof(json),
             "{\"v\":1,\"type\":\"hello\",\"session_id\":\"%s\","
             "\"message_id\":%" PRIu32 ",\"device_id\":\"project-james-p4\","
             "\"firmware_version\":\"ptt-prototype-1\"}",
             s_ptt.session_id, next_message_id());
    if (send_text(json) < 0) {
        ESP_LOGE(TAG, "Could not send protocol hello");
    }
}

static bool json_string_value(const char *json, const char *key, char *output,
                              size_t output_bytes)
{
    char needle[48];
    snprintf(needle, sizeof(needle), "\"%s\"", key);
    const char *cursor = strstr(json, needle);
    if (cursor == NULL || (cursor = strchr(cursor + strlen(needle), ':')) == NULL) {
        return false;
    }
    cursor++;
    while (*cursor == ' ' || *cursor == '\t') {
        cursor++;
    }
    if (*cursor++ != '\"') {
        return false;
    }
    size_t written = 0;
    while (*cursor && *cursor != '\"' && written + 1 < output_bytes) {
        if (*cursor == '\\' && cursor[1] != '\0') {
            cursor++;
        }
        output[written++] = *cursor++;
    }
    output[written] = '\0';
    return *cursor == '\"';
}

static void handle_text_message(uint8_t *message, size_t length)
{
    if (length >= JAMES_WS_BUFFER_BYTES) {
        return;
    }
    message[length] = '\0';
    char name[32];
    if (!json_string_value((const char *)message, "type", name, sizeof(name))) {
        ESP_LOGE(TAG, "Invalid JSON from gateway");
        return;
    }

    if (strcmp(name, "hello.ack") == 0) {
        xEventGroupSetBits(s_ptt.events, JAMES_WS_READY_BIT);
        ESP_LOGI(TAG, "Gateway ready. Hold BOOT to talk; release to send.");
    } else if (strcmp(name, "stt.final") == 0) {
        char transcript[512];
        const bool found = json_string_value((const char *)message, "text",
                                             transcript, sizeof(transcript)) ||
                           json_string_value((const char *)message, "transcript",
                                             transcript, sizeof(transcript));
        ESP_LOGI(TAG, "You: %s", found ? transcript : "(no text)");
    } else if (strcmp(name, "assistant.text") == 0) {
        char reply[1024];
        const bool found = json_string_value((const char *)message, "text",
                                             reply, sizeof(reply));
        ESP_LOGI(TAG, "James: %s", found ? reply : "(no text)");
    } else if (strcmp(name, "tts.start") == 0) {
        if (james_audio_playback_begin() == ESP_OK) {
            xEventGroupSetBits(s_ptt.events, JAMES_WS_SPEAKING_BIT);
            ESP_LOGI(TAG, "James speaking");
        }
    } else if (strcmp(name, "tts.end") == 0) {
        james_audio_playback_end();
        xEventGroupClearBits(s_ptt.events, JAMES_WS_SPEAKING_BIT);
        ESP_LOGI(TAG, "James finished. Hold BOOT for the next question.");
    } else if (strcmp(name, "error") == 0) {
        char code[64];
        char detail[256];
        const bool have_code = json_string_value((const char *)message, "code",
                                                 code, sizeof(code));
        const bool have_detail = json_string_value((const char *)message, "detail",
                                                   detail, sizeof(detail));
        ESP_LOGE(TAG, "Gateway error %s: %s", have_code ? code : "unknown",
                 have_detail ? detail : "no detail");
        james_audio_playback_end();
        xEventGroupClearBits(s_ptt.events, JAMES_WS_SPEAKING_BIT);
    }
}

static void handle_binary_message(const uint8_t *message, size_t length)
{
    if (length < JAMES_HEADER_BYTES || memcmp(message, "JAM1", 4) != 0 ||
        message[4] != JAMES_PROTOCOL_VERSION || message[5] != JAMES_KIND_TTS ||
        read_be16(message + 6) != JAMES_HEADER_BYTES) {
        ESP_LOGE(TAG, "Rejected invalid TTS binary header");
        return;
    }
    const uint16_t payload_bytes = read_be16(message + 22);
    if ((size_t)payload_bytes + JAMES_HEADER_BYTES != length ||
        payload_bytes == 0 || payload_bytes % JAMES_AUDIO_BYTES_PER_FRAME != 0) {
        ESP_LOGE(TAG, "Rejected invalid TTS payload length");
        return;
    }
    const esp_err_t result = james_audio_playback_write(
        message + JAMES_HEADER_BYTES, payload_bytes);
    if (result != ESP_OK) {
        ESP_LOGE(TAG, "Speaker write failed: %s", esp_err_to_name(result));
    }
}

static void websocket_event(void *argument, esp_event_base_t base, int32_t id,
                            void *event_data)
{
    (void)argument;
    (void)base;
    esp_websocket_event_data_t *event = event_data;
    if (id == WEBSOCKET_EVENT_CONNECTED) {
        ESP_LOGI(TAG, "Connected to Titanium gateway");
        send_hello();
    } else if (id == WEBSOCKET_EVENT_DISCONNECTED) {
        xEventGroupClearBits(s_ptt.events,
                             JAMES_WS_READY_BIT | JAMES_WS_SPEAKING_BIT);
        james_audio_playback_end();
        ESP_LOGW(TAG, "Gateway disconnected; client will reconnect");
    } else if (id == WEBSOCKET_EVENT_ERROR) {
        ESP_LOGE(TAG, "WebSocket transport error");
    } else if (id == WEBSOCKET_EVENT_DATA && event->data_len > 0) {
        if (event->payload_offset == 0) {
            s_ptt.receive_length = 0;
            s_ptt.receive_opcode = event->op_code;
        }
        if (event->payload_len >= JAMES_WS_BUFFER_BYTES ||
            s_ptt.receive_length + event->data_len >= JAMES_WS_BUFFER_BYTES) {
            ESP_LOGE(TAG, "Gateway message exceeds receive buffer");
            s_ptt.receive_length = 0;
            return;
        }
        memcpy(s_ptt.receive + s_ptt.receive_length, event->data_ptr,
               event->data_len);
        s_ptt.receive_length += event->data_len;
        if (event->payload_offset + event->data_len == event->payload_len) {
            if (s_ptt.receive_opcode == 0x1) {
                handle_text_message(s_ptt.receive, s_ptt.receive_length);
            } else if (s_ptt.receive_opcode == 0x2) {
                handle_binary_message(s_ptt.receive, s_ptt.receive_length);
            }
            s_ptt.receive_length = 0;
        }
    }
}

static bool ptt_pressed(void)
{
    return gpio_get_level((gpio_num_t)CONFIG_JAMES_PTT_GPIO) == 0;
}

static bool wait_for_stable_button(bool expected)
{
    vTaskDelay(pdMS_TO_TICKS(JAMES_BUTTON_DEBOUNCE_MS));
    return ptt_pressed() == expected;
}

static bool send_audio_chunk(uint32_t utterance_id, uint32_t sequence,
                             const james_audio_frame_t *frames, size_t count)
{
    uint8_t packet[JAMES_HEADER_BYTES + JAMES_PCM_BYTES_PER_CHUNK];
    const uint16_t payload_bytes = count * JAMES_AUDIO_BYTES_PER_FRAME;
    memcpy(packet, "JAM1", 4);
    packet[4] = JAMES_PROTOCOL_VERSION;
    packet[5] = JAMES_KIND_MICROPHONE;
    write_be16(packet + 6, JAMES_HEADER_BYTES);
    write_be32(packet + 8, utterance_id);
    write_be32(packet + 12, sequence);
    write_be32(packet + 16, (uint32_t)(frames[0].timestamp_us / 1000));
    write_be16(packet + 20, count);
    write_be16(packet + 22, payload_bytes);
    for (size_t index = 0; index < count; ++index) {
        memcpy(packet + JAMES_HEADER_BYTES +
                   index * JAMES_AUDIO_BYTES_PER_FRAME,
               frames[index].samples, JAMES_AUDIO_BYTES_PER_FRAME);
    }
    return esp_websocket_client_send_bin(
               s_ptt.websocket, (const char *)packet,
               JAMES_HEADER_BYTES + payload_bytes,
               pdMS_TO_TICKS(JAMES_SEND_TIMEOUT_MS)) >= 0;
}

static void send_cancel(uint32_t utterance_id, const char *reason)
{
    char json[256];
    snprintf(json, sizeof(json),
             "{\"v\":1,\"type\":\"audio.cancel\",\"session_id\":\"%s\","
             "\"message_id\":%" PRIu32 ",\"utterance_id\":%" PRIu32 ","
             "\"reason\":\"%s\"}",
             s_ptt.session_id, next_message_id(), utterance_id, reason);
    send_text(json);
}

static void run_utterance(void)
{
    const uint32_t utterance_id = ++s_ptt.utterance_id;
    char json[384];
    snprintf(json, sizeof(json),
             "{\"v\":1,\"type\":\"audio.start\",\"session_id\":\"%s\","
             "\"message_id\":%" PRIu32 ",\"utterance_id\":%" PRIu32 ","
             "\"timestamp_us\":%" PRIu64 ",\"sample_rate_hz\":16000,"
             "\"sample_bits\":16,\"channels\":1,\"preroll_frames\":0}",
             s_ptt.session_id, next_message_id(), utterance_id,
             (uint64_t)esp_timer_get_time());
    if (send_text(json) < 0) {
        ESP_LOGE(TAG, "Could not start utterance");
        return;
    }

    james_audio_capture_flush();
    james_audio_ring_stats_t before = {0};
    james_audio_capture_stats(&before);
    james_audio_frame_t frames[JAMES_FRAMES_PER_CHUNK];
    size_t buffered = 0;
    uint32_t sequence = 0;
    uint32_t total_frames = 0;
    bool send_failed = false;
    const int64_t deadline = esp_timer_get_time() +
                             (int64_t)CONFIG_JAMES_PTT_MAX_SECONDS * 1000000;
    ESP_LOGI(TAG, "Listening... keep holding BOOT");

    while (ptt_pressed() && esp_timer_get_time() < deadline) {
        if (!james_audio_capture_read(&frames[buffered], pdMS_TO_TICKS(100))) {
            continue;
        }
        buffered++;
        total_frames++;
        if (buffered == JAMES_FRAMES_PER_CHUNK) {
            if (!send_audio_chunk(utterance_id, sequence++, frames, buffered)) {
                send_failed = true;
                break;
            }
            buffered = 0;
        }
    }
    if (buffered && !send_failed) {
        send_failed = !send_audio_chunk(utterance_id, sequence++, frames, buffered);
    }

    james_audio_ring_stats_t after = {0};
    james_audio_capture_stats(&after);
    const uint64_t dropped = after.dropped_oldest - before.dropped_oldest;
    if (send_failed || dropped > 0 || total_frames == 0) {
        const char *reason = send_failed ? "network_send_failed" :
                             dropped ? "capture_overrun" : "empty_utterance";
        ESP_LOGE(TAG, "PTT cancelled: %s", reason);
        send_cancel(utterance_id, reason);
        return;
    }

    snprintf(json, sizeof(json),
             "{\"v\":1,\"type\":\"audio.end\",\"session_id\":\"%s\","
             "\"message_id\":%" PRIu32 ",\"utterance_id\":%" PRIu32 ","
             "\"end_reason\":\"push_to_talk_release\","
             "\"last_sequence\":%" PRIu32 ",\"frame_count\":%" PRIu32 ","
             "\"dropped_frames\":0}",
             s_ptt.session_id, next_message_id(), utterance_id,
             sequence - 1, total_frames);
    if (send_text(json) < 0) {
        ESP_LOGE(TAG, "Could not finish utterance");
    } else {
        ESP_LOGI(TAG, "Sent %.2f seconds; waiting for James",
                 total_frames * JAMES_AUDIO_FRAME_MS / 1000.0);
    }
}

static void ptt_task(void *argument)
{
    (void)argument;
    bool previous = ptt_pressed();
    while (true) {
        const bool current = ptt_pressed();
        if (current && !previous && wait_for_stable_button(true)) {
            const EventBits_t state = xEventGroupGetBits(s_ptt.events);
            if (!(state & JAMES_WS_READY_BIT)) {
                ESP_LOGW(TAG, "Gateway is not ready yet");
            } else if (state & JAMES_WS_SPEAKING_BIT) {
                ESP_LOGW(TAG, "Wait until James finishes speaking");
            } else {
                run_utterance();
            }
        }
        previous = current;
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

esp_err_t james_ptt_client_start(void)
{
    if (JAMES_PRIVATE_GATEWAY_TOKEN[0] == '\0') {
        ESP_LOGE(TAG, "Private gateway token is empty");
        return ESP_ERR_INVALID_STATE;
    }
    s_ptt.events = xEventGroupCreate();
    if (s_ptt.events == NULL) {
        return ESP_ERR_NO_MEM;
    }
    uint8_t mac[6];
    ESP_RETURN_ON_ERROR(esp_efuse_mac_get_default(mac), TAG,
                        "Could not read P4 factory MAC");
    snprintf(s_ptt.session_id, sizeof(s_ptt.session_id),
             "p4-%02x%02x%02x-%08" PRIx32, mac[3], mac[4], mac[5],
             (uint32_t)esp_timer_get_time());
    snprintf(s_ptt.headers, sizeof(s_ptt.headers), "X-James-Token: %s\r\n",
             JAMES_PRIVATE_GATEWAY_TOKEN);

    const gpio_config_t button = {
        .pin_bit_mask = 1ULL << CONFIG_JAMES_PTT_GPIO,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_RETURN_ON_ERROR(gpio_config(&button), TAG,
                        "BOOT button configuration failed");

    const esp_websocket_client_config_t config = {
        .uri = CONFIG_JAMES_GATEWAY_URI,
        .headers = s_ptt.headers,
        .buffer_size = 4096,
        .network_timeout_ms = 10000,
        .reconnect_timeout_ms = 3000,
    };
    s_ptt.websocket = esp_websocket_client_init(&config);
    if (s_ptt.websocket == NULL) {
        return ESP_ERR_NO_MEM;
    }
    ESP_RETURN_ON_ERROR(
        esp_websocket_register_events(s_ptt.websocket, WEBSOCKET_EVENT_ANY,
                                      websocket_event, NULL),
        TAG, "WebSocket event registration failed");
    ESP_RETURN_ON_ERROR(esp_websocket_client_start(s_ptt.websocket), TAG,
                        "WebSocket client start failed");

    if (xTaskCreatePinnedToCore(ptt_task, "ptt_task", JAMES_PTT_TASK_STACK,
                                NULL, JAMES_PTT_TASK_PRIORITY, &s_ptt.task,
                                JAMES_PTT_TASK_CORE) != pdPASS) {
        return ESP_ERR_NO_MEM;
    }
    ESP_LOGI(TAG,
             "BOOT PTT enabled on GPIO%d (runtime only; do not hold during reset)",
             CONFIG_JAMES_PTT_GPIO);
    return ESP_OK;
}
