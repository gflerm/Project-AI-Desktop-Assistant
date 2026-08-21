#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

esp_err_t james_wifi_start(void);
bool james_wifi_is_connected(void);

#ifdef __cplusplus
}
#endif
