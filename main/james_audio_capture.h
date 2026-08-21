#pragma once

#include "esp_err.h"
#include "freertos/FreeRTOS.h"

#include "james_audio_frame.h"
#include "james_audio_ring.h"

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
esp_err_t james_audio_capture_start(void);

bool james_audio_capture_read(james_audio_frame_t *frame, TickType_t timeout);
void james_audio_capture_flush(void);
void james_audio_capture_stats(james_audio_ring_stats_t *stats);

esp_err_t james_audio_playback_begin(void);
esp_err_t james_audio_playback_write(const void *pcm, size_t bytes);
void james_audio_playback_end(void);

#ifdef __cplusplus
}
#endif
