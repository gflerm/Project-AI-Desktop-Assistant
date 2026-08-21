#pragma once

#include "esp_err.h"
#include "freertos/FreeRTOS.h"

#include "tars_audio_frame.h"
#include "tars_audio_ring.h"

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

bool tars_audio_capture_read(tars_audio_frame_t *frame, TickType_t timeout);
void tars_audio_capture_flush(void);
void tars_audio_capture_stats(tars_audio_ring_stats_t *stats);

esp_err_t tars_audio_playback_begin(void);
esp_err_t tars_audio_playback_write(const void *pcm, size_t bytes);
void tars_audio_playback_end(void);

#ifdef __cplusplus
}
#endif
