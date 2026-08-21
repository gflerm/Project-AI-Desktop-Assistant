#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    JAMES_ENDPOINT_DISARMED = 0,
    JAMES_ENDPOINT_ARMED_SILENCE,
    JAMES_ENDPOINT_STARTING,
    JAMES_ENDPOINT_IN_SPEECH,
    JAMES_ENDPOINT_HANGOVER,
    JAMES_ENDPOINT_COMPLETE,
} james_endpoint_state_t;

typedef enum {
    JAMES_ENDPOINT_EVENT_NONE = 0,
    JAMES_ENDPOINT_EVENT_SPEECH_START,
    JAMES_ENDPOINT_EVENT_SPEECH_END,
    JAMES_ENDPOINT_EVENT_NO_SPEECH_TIMEOUT,
    JAMES_ENDPOINT_EVENT_MAX_UTTERANCE,
    JAMES_ENDPOINT_EVENT_CANCELLED,
    JAMES_ENDPOINT_EVENT_OVERRUN,
} james_endpoint_event_t;

typedef struct {
    uint16_t frame_ms;
    uint16_t start_confirmation_ms;
    uint16_t end_silence_ms;
    uint32_t no_speech_timeout_ms;
    uint32_t maximum_utterance_ms;
} james_endpoint_config_t;

typedef struct {
    james_endpoint_config_t config;
    james_endpoint_state_t state;
    uint32_t utterance_id;
    uint32_t armed_frames;
    uint32_t speech_candidate_frames;
    uint32_t utterance_frames;
    uint32_t silence_frames;
} james_endpoint_t;

bool james_endpoint_init(james_endpoint_t *endpoint,
                        const james_endpoint_config_t *config);
void james_endpoint_arm(james_endpoint_t *endpoint);
void james_endpoint_disarm(james_endpoint_t *endpoint);
james_endpoint_event_t james_endpoint_process(james_endpoint_t *endpoint,
                                            bool speech_detected);
james_endpoint_event_t james_endpoint_cancel(james_endpoint_t *endpoint);
james_endpoint_event_t james_endpoint_report_overrun(james_endpoint_t *endpoint);

/** Run deterministic transition checks against the production state machine. */
bool james_endpoint_self_test(void);
