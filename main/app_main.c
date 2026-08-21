#include <stdio.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_heap_caps.h"
#include "esp_log.h"
#include "nvs_flash.h"

#include "james_audio_capture.h"
#include "james_endpoint.h"
#include "james_ptt_client.h"
#include "james_wifi.h"

static const char *TAG = "james";

static void log_runtime_memory(void)
{
    const size_t internal_total = heap_caps_get_total_size(MALLOC_CAP_INTERNAL);
    const size_t internal_free = heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
    const size_t psram_total = heap_caps_get_total_size(MALLOC_CAP_SPIRAM);
    const size_t psram_free = heap_caps_get_free_size(MALLOC_CAP_SPIRAM);

    ESP_LOGI(TAG,
             "Memory: internal used=%u free=%u total=%u; "
             "PSRAM heap used=%u free=%u total=%u bytes",
             (unsigned)(internal_total - internal_free), (unsigned)internal_free,
             (unsigned)internal_total,
             (unsigned)(psram_total - psram_free), (unsigned)psram_free,
             (unsigned)psram_total);
}

void app_main(void)
{
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    ESP_LOGI(TAG, "Project James firmware starting on ESP32-P4 (ESP-IDF)");

    if (!james_endpoint_self_test()) {
        ESP_LOGE(TAG, "Endpoint state-machine self-test failed");
    } else {
        ESP_LOGI(TAG, "Endpoint state-machine self-test passed");
    }

#if CONFIG_JAMES_AUDIO_CAPTURE_DIAGNOSTIC
    ret = james_audio_capture_start();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Audio capture diagnostic did not start: %s", esp_err_to_name(ret));
        return;
    }
#else
    ESP_LOGI(TAG, "Audio capture diagnostic is disabled in project configuration");
#endif

#if CONFIG_JAMES_PTT_PROTOTYPE
    ret = james_wifi_start();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Wi-Fi did not start: %s", esp_err_to_name(ret));
        return;
    }
    ret = james_ptt_client_start();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "BOOT-button PTT client did not start: %s", esp_err_to_name(ret));
        return;
    }
#else
    ESP_LOGI(TAG, "BOOT-button PTT prototype is disabled");
#endif

    uint32_t seconds = 0;
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(1000));
        if (++seconds == 20 || seconds % 60 == 0) {
            log_runtime_memory();
        }
    }
}
