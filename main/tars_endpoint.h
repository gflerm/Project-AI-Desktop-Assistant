#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    TARS_ENDPOINT_DISARMED = 0,
    TARS_ENDPOINT_ARMED_SILENCE,
    TARS_ENDPOINT_STARTING,
    TARS_ENDPOINT_IN_SPEECH,
    TARS_ENDPOINT_HANGOVER,
    TARS_ENDPOINT_COMPLETE,
} tars_endpoint_state_t;

typedef enum {
    TARS_ENDPOINT_EVENT_NONE = 0,
    TARS_ENDPOINT_EVENT_SPEECH_START,
    TARS_ENDPOINT_EVENT_SPEECH_END,
    TARS_ENDPOINT_EVENT_NO_SPEECH_TIMEOUT,
    TARS_ENDPOINT_EVENT_MAX_UTTERANCE,
    TARS_ENDPOINT_EVENT_CANCELLED,
    TARS_ENDPOINT_EVENT_OVERRUN,
} tars_endpoint_event_t;

typedef struct {
    uint16_t frame_ms;
    uint16_t start_confirmation_ms;
    uint16_t end_silence_ms;
    uint32_t no_speech_timeout_ms;
    uint32_t maximum_utterance_ms;
} tars_endpoint_config_t;

typedef struct {
    tars_endpoint_config_t config;
    tars_endpoint_state_t state;
    uint32_t utterance_id;
    uint32_t armed_frames;
    uint32_t speech_candidate_frames;
    uint32_t utterance_frames;
    uint32_t silence_frames;
} tars_endpoint_t;

bool tars_endpoint_init(tars_endpoint_t *endpoint,
                        const tars_endpoint_config_t *config);
void tars_endpoint_arm(tars_endpoint_t *endpoint);
void tars_endpoint_disarm(tars_endpoint_t *endpoint);
tars_endpoint_event_t tars_endpoint_process(tars_endpoint_t *endpoint,
                                            bool speech_detected);
tars_endpoint_event_t tars_endpoint_cancel(tars_endpoint_t *endpoint);
tars_endpoint_event_t tars_endpoint_report_overrun(tars_endpoint_t *endpoint);

/** Run deterministic transition checks against the production state machine. */
bool tars_endpoint_self_test(void);
