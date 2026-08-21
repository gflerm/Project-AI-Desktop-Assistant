#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"

#include "james_audio_frame.h"

typedef struct {
    QueueHandle_t queue;
    portMUX_TYPE lock;
    UBaseType_t capacity;
    uint64_t pushed;
    uint64_t popped;
    uint64_t dropped_oldest;
} james_audio_ring_t;

typedef struct {
    uint64_t pushed;
    uint64_t popped;
    uint64_t dropped_oldest;
    UBaseType_t depth;
    UBaseType_t capacity;
} james_audio_ring_stats_t;

esp_err_t james_audio_ring_init(james_audio_ring_t *ring, UBaseType_t capacity);

/**
 * Add a frame without blocking capture. If full, discard exactly one oldest
 * frame and retain the newest audio. Returns false only if the queue cannot be
 * recovered after that bounded operation.
 */
bool james_audio_ring_push_latest(james_audio_ring_t *ring,
                                 const james_audio_frame_t *frame);

bool james_audio_ring_pop(james_audio_ring_t *ring, james_audio_frame_t *frame,
                         TickType_t wait_ticks);

void james_audio_ring_get_stats(const james_audio_ring_t *ring,
                               james_audio_ring_stats_t *stats);
