#include "tars_audio_ring.h"

#include <stddef.h>

esp_err_t tars_audio_ring_init(tars_audio_ring_t *ring, UBaseType_t capacity)
{
    if (ring == NULL || capacity == 0 || ring->queue != NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    ring->queue = xQueueCreate(capacity, sizeof(tars_audio_frame_t));
    if (ring->queue == NULL) {
        return ESP_ERR_NO_MEM;
    }

    portMUX_INITIALIZE(&ring->lock);
    ring->capacity = capacity;
    ring->pushed = 0;
    ring->popped = 0;
    ring->dropped_oldest = 0;
    return ESP_OK;
}

bool tars_audio_ring_push_latest(tars_audio_ring_t *ring,
                                 const tars_audio_frame_t *frame)
{
    if (ring == NULL || ring->queue == NULL || frame == NULL) {
        return false;
    }

    if (xQueueSend(ring->queue, frame, 0) == pdTRUE) {
        portENTER_CRITICAL(&ring->lock);
        ring->pushed++;
        portEXIT_CRITICAL(&ring->lock);
        return true;
    }

    tars_audio_frame_t discarded;
    if (xQueueReceive(ring->queue, &discarded, 0) == pdTRUE) {
        portENTER_CRITICAL(&ring->lock);
        ring->dropped_oldest++;
        portEXIT_CRITICAL(&ring->lock);
    }

    if (xQueueSend(ring->queue, frame, 0) == pdTRUE) {
        portENTER_CRITICAL(&ring->lock);
        ring->pushed++;
        portEXIT_CRITICAL(&ring->lock);
        return true;
    }

    return false;
}

bool tars_audio_ring_pop(tars_audio_ring_t *ring, tars_audio_frame_t *frame,
                         TickType_t wait_ticks)
{
    if (ring == NULL || ring->queue == NULL || frame == NULL) {
        return false;
    }

    if (xQueueReceive(ring->queue, frame, wait_ticks) != pdTRUE) {
        return false;
    }

    portENTER_CRITICAL(&ring->lock);
    ring->popped++;
    portEXIT_CRITICAL(&ring->lock);
    return true;
}

void tars_audio_ring_get_stats(const tars_audio_ring_t *ring,
                               tars_audio_ring_stats_t *stats)
{
    if (ring == NULL || stats == NULL || ring->queue == NULL) {
        return;
    }

    tars_audio_ring_t *mutable_ring = (tars_audio_ring_t *)ring;
    portENTER_CRITICAL(&mutable_ring->lock);
    stats->pushed = ring->pushed;
    stats->popped = ring->popped;
    stats->dropped_oldest = ring->dropped_oldest;
    portEXIT_CRITICAL(&mutable_ring->lock);
    stats->depth = uxQueueMessagesWaiting(ring->queue);
    stats->capacity = ring->capacity;
}
