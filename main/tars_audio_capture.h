#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Start the bounded Core 1 microphone capture diagnostic.
 *
 * The diagnostic configures the board ES8311/I2S input for signed 16-bit,
 * 16 kHz mono PCM and logs aggregate signal/health statistics. It does not
 * retain, save, or transmit captured audio.
 */
esp_err_t tars_audio_capture_start(void);

#ifdef __cplusplus
}
#endif
