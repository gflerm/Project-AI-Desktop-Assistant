idf_component_register(SRCS "app_main.c"
                       INCLUDE_DIRS "."
                       REQUIRES esp_psram esp_wifi esp_netif esp_event nvs_flash
                                esp_http_server esp_driver_jpeg espressif__esp_video
                                espressif__esp_codec_dev waveshare__esp32_p4_platform)