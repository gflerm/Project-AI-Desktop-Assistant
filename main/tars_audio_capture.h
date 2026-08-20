#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Start the bounded two-core microphone capture diagnostic.
 *
 * The diagnostic configures the board ES8311/I2S input for signed 16-bit,
 * 16 kHz mono PCM. Core 1 publishes fixed frames into a bounded queue and a
 * Core 0 diagnostic consumer logs aggregate signal/health statistics. It does
 * not save or transmit captured audio.
 */
esp_err_t tars_audio_capture_start(void);

#ifdef __cplusplus
}
#endif
