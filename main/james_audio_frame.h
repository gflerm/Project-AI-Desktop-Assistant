#pragma once

#include <stdint.h>

#define JAMES_AUDIO_SAMPLE_RATE_HZ 16000U
#define JAMES_AUDIO_BITS_PER_SAMPLE 16U
#define JAMES_AUDIO_CHANNELS 1U
#define JAMES_AUDIO_FRAME_MS 20U
#define JAMES_AUDIO_SAMPLES_PER_FRAME \
    ((JAMES_AUDIO_SAMPLE_RATE_HZ * JAMES_AUDIO_FRAME_MS) / 1000U)
#define JAMES_AUDIO_BYTES_PER_FRAME \
    (JAMES_AUDIO_SAMPLES_PER_FRAME * (JAMES_AUDIO_BITS_PER_SAMPLE / 8U))

typedef struct {
    uint32_t sequence;
    int64_t timestamp_us;
    int16_t samples[JAMES_AUDIO_SAMPLES_PER_FRAME];
} james_audio_frame_t;
