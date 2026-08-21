#include "tars_wifi.h"

#include <stdbool.h>
#include <string.h>

#include "esp_check.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "sdkconfig.h"
#include "tars_private_config.h"

#define TARS_WIFI_CONNECTED_BIT BIT0
#define TARS_WIFI_INITIAL_TIMEOUT_MS 30000

static const char *TAG = "tars_wifi";
static EventGroupHandle_t s_events;

static void tars_wifi_event(void *argument, esp_event_base_t base, int32_t id,
                            void *data)
{
    (void)argument;
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED) {
        xEventGroupClearBits(s_events, TARS_WIFI_CONNECTED_BIT);
        const wifi_event_sta_disconnected_t *event =
            (const wifi_event_sta_disconnected_t *)data;
        ESP_LOGW(TAG, "Wi-Fi disconnected (reason=%u); reconnecting",
                 event != NULL ? (unsigned)event->reason : 0U);
        esp_wifi_connect();
    } else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        const ip_event_got_ip_t *event = (const ip_event_got_ip_t *)data;
        ESP_LOGI(TAG, "Wi-Fi connected, address " IPSTR,
                 IP2STR(&event->ip_info.ip));
        xEventGroupSetBits(s_events, TARS_WIFI_CONNECTED_BIT);
    }
}

esp_err_t tars_wifi_start(void)
{
    if (TARS_PRIVATE_WIFI_SSID[0] == '\0') {
        ESP_LOGE(TAG, "Private Wi-Fi SSID is empty");
        return ESP_ERR_INVALID_STATE;
    }

    s_events = xEventGroupCreate();
    if (s_events == NULL) {
        return ESP_ERR_NO_MEM;
    }

    ESP_RETURN_ON_ERROR(esp_netif_init(), TAG, "esp_netif_init failed");
    esp_err_t result = esp_event_loop_create_default();
    if (result != ESP_OK && result != ESP_ERR_INVALID_STATE) {
        return result;
    }
    if (esp_netif_create_default_wifi_sta() == NULL) {
        return ESP_FAIL;
    }

    wifi_init_config_t init = WIFI_INIT_CONFIG_DEFAULT();
    ESP_RETURN_ON_ERROR(esp_wifi_init(&init), TAG, "esp_wifi_init failed");
    ESP_RETURN_ON_ERROR(
        esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID,
                                   tars_wifi_event, NULL),
        TAG, "Wi-Fi event registration failed");
    ESP_RETURN_ON_ERROR(
        esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP,
                                   tars_wifi_event, NULL),
        TAG, "IP event registration failed");

    wifi_config_t config = {0};
    strlcpy((char *)config.sta.ssid, TARS_PRIVATE_WIFI_SSID,
            sizeof(config.sta.ssid));
    strlcpy((char *)config.sta.password, TARS_PRIVATE_WIFI_PASSWORD,
            sizeof(config.sta.password));
    config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;
    config.sta.sae_pwe_h2e = WPA3_SAE_PWE_BOTH;

    ESP_RETURN_ON_ERROR(esp_wifi_set_mode(WIFI_MODE_STA), TAG,
                        "Wi-Fi station mode failed");
    ESP_RETURN_ON_ERROR(esp_wifi_set_config(WIFI_IF_STA, &config), TAG,
                        "Wi-Fi configuration failed");
    ESP_RETURN_ON_ERROR(esp_wifi_start(), TAG, "Wi-Fi start failed");

    const EventBits_t connected = xEventGroupWaitBits(
        s_events, TARS_WIFI_CONNECTED_BIT, pdFALSE, pdTRUE,
        pdMS_TO_TICKS(TARS_WIFI_INITIAL_TIMEOUT_MS));
    if (!(connected & TARS_WIFI_CONNECTED_BIT)) {
        ESP_LOGE(TAG, "No IP address after %d seconds",
                 TARS_WIFI_INITIAL_TIMEOUT_MS / 1000);
        return ESP_ERR_TIMEOUT;
    }
    return ESP_OK;
}

bool tars_wifi_is_connected(void)
{
    return s_events != NULL &&
           (xEventGroupGetBits(s_events) & TARS_WIFI_CONNECTED_BIT) != 0;
}
