#pragma once

#include <stdint.h>

#define TARS_AUDIO_SAMPLE_RATE_HZ 16000U
#define TARS_AUDIO_BITS_PER_SAMPLE 16U
#define TARS_AUDIO_CHANNELS 1U
#define TARS_AUDIO_FRAME_MS 20U
#define TARS_AUDIO_SAMPLES_PER_FRAME \
    ((TARS_AUDIO_SAMPLE_RATE_HZ * TARS_AUDIO_FRAME_MS) / 1000U)

typedef struct {
    uint32_t sequence;
    int64_t timestamp_us;
    int16_t samples[TARS_AUDIO_SAMPLES_PER_FRAME];
} tars_audio_frame_t;
