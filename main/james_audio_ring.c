#include "james_audio_ring.h"

#include <stddef.h>

esp_err_t james_audio_ring_init(james_audio_ring_t *ring, UBaseType_t capacity)
{
    if (ring == NULL || capacity == 0 || ring->queue != NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    ring->queue = xQueueCreate(capacity, sizeof(james_audio_frame_t));
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

bool james_audio_ring_push_latest(james_audio_ring_t *ring,
                                 const james_audio_frame_t *frame)
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

    james_audio_frame_t discarded;
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

bool james_audio_ring_pop(james_audio_ring_t *ring, james_audio_frame_t *frame,
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

void james_audio_ring_get_stats(const james_audio_ring_t *ring,
                               james_audio_ring_stats_t *stats)
{
    if (ring == NULL || stats == NULL || ring->queue == NULL) {
        return;
    }

    james_audio_ring_t *mutable_ring = (james_audio_ring_t *)ring;
    portENTER_CRITICAL(&mutable_ring->lock);
    stats->pushed = ring->pushed;
    stats->popped = ring->popped;
    stats->dropped_oldest = ring->dropped_oldest;
    portEXIT_CRITICAL(&mutable_ring->lock);
    stats->depth = uxQueueMessagesWaiting(ring->queue);
    stats->capacity = ring->capacity;
}
