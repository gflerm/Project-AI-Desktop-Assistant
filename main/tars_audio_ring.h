#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"

#include "tars_audio_frame.h"

typedef struct {
    QueueHandle_t queue;
    portMUX_TYPE lock;
    UBaseType_t capacity;
    uint64_t pushed;
    uint64_t popped;
    uint64_t dropped_oldest;
} tars_audio_ring_t;

typedef struct {
    uint64_t pushed;
    uint64_t popped;
    uint64_t dropped_oldest;
    UBaseType_t depth;
    UBaseType_t capacity;
} tars_audio_ring_stats_t;

esp_err_t tars_audio_ring_init(tars_audio_ring_t *ring, UBaseType_t capacity);

/**
 * Add a frame without blocking capture. If full, discard exactly one oldest
 * frame and retain the newest audio. Returns false only if the queue cannot be
 * recovered after that bounded operation.
 */
bool tars_audio_ring_push_latest(tars_audio_ring_t *ring,
                                 const tars_audio_frame_t *frame);

bool tars_audio_ring_pop(tars_audio_ring_t *ring, tars_audio_frame_t *frame,
                         TickType_t wait_ticks);

void tars_audio_ring_get_stats(const tars_audio_ring_t *ring,
                               tars_audio_ring_stats_t *stats);
