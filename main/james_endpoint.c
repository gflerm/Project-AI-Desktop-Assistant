#include "james_endpoint.h"

#include <stddef.h>
#include <string.h>

static uint32_t frames_for_ms(uint32_t duration_ms, uint16_t frame_ms)
{
    return (duration_ms + frame_ms - 1U) / frame_ms;
}

static void clear_turn_counters(james_endpoint_t *endpoint)
{
    endpoint->armed_frames = 0;
    endpoint->speech_candidate_frames = 0;
    endpoint->utterance_frames = 0;
    endpoint->silence_frames = 0;
}

bool james_endpoint_init(james_endpoint_t *endpoint,
                        const james_endpoint_config_t *config)
{
    if (endpoint == NULL || config == NULL || config->frame_ms == 0 ||
        config->start_confirmation_ms == 0 || config->end_silence_ms == 0 ||
        config->no_speech_timeout_ms == 0 ||
        config->maximum_utterance_ms == 0) {
        return false;
    }

    memset(endpoint, 0, sizeof(*endpoint));
    endpoint->config = *config;
    endpoint->state = JAMES_ENDPOINT_DISARMED;
    return true;
}

void james_endpoint_arm(james_endpoint_t *endpoint)
{
    if (endpoint == NULL) {
        return;
    }
    clear_turn_counters(endpoint);
    endpoint->state = JAMES_ENDPOINT_ARMED_SILENCE;
}

void james_endpoint_disarm(james_endpoint_t *endpoint)
{
    if (endpoint == NULL) {
        return;
    }
    clear_turn_counters(endpoint);
    endpoint->state = JAMES_ENDPOINT_DISARMED;
}

james_endpoint_event_t james_endpoint_process(james_endpoint_t *endpoint,
                                            bool speech_detected)
{
    if (endpoint == NULL || endpoint->state == JAMES_ENDPOINT_DISARMED ||
        endpoint->state == JAMES_ENDPOINT_COMPLETE) {
        return JAMES_ENDPOINT_EVENT_NONE;
    }

    if (endpoint->state == JAMES_ENDPOINT_ARMED_SILENCE ||
        endpoint->state == JAMES_ENDPOINT_STARTING) {
        endpoint->armed_frames++;
        if (speech_detected) {
            endpoint->speech_candidate_frames++;
            endpoint->state = JAMES_ENDPOINT_STARTING;
            if (endpoint->speech_candidate_frames >= frames_for_ms(
                    endpoint->config.start_confirmation_ms,
                    endpoint->config.frame_ms)) {
                endpoint->utterance_id++;
                endpoint->utterance_frames = endpoint->speech_candidate_frames;
                endpoint->silence_frames = 0;
                endpoint->state = JAMES_ENDPOINT_IN_SPEECH;
                return JAMES_ENDPOINT_EVENT_SPEECH_START;
            }
        } else {
            endpoint->speech_candidate_frames = 0;
            endpoint->state = JAMES_ENDPOINT_ARMED_SILENCE;
        }

        if (endpoint->armed_frames >= frames_for_ms(
                endpoint->config.no_speech_timeout_ms,
                endpoint->config.frame_ms)) {
            endpoint->state = JAMES_ENDPOINT_COMPLETE;
            return JAMES_ENDPOINT_EVENT_NO_SPEECH_TIMEOUT;
        }
        return JAMES_ENDPOINT_EVENT_NONE;
    }

    endpoint->utterance_frames++;
    if (endpoint->utterance_frames >= frames_for_ms(
            endpoint->config.maximum_utterance_ms,
            endpoint->config.frame_ms)) {
        endpoint->state = JAMES_ENDPOINT_COMPLETE;
        return JAMES_ENDPOINT_EVENT_MAX_UTTERANCE;
    }

    if (speech_detected) {
        endpoint->silence_frames = 0;
        endpoint->state = JAMES_ENDPOINT_IN_SPEECH;
        return JAMES_ENDPOINT_EVENT_NONE;
    }

    endpoint->silence_frames++;
    endpoint->state = JAMES_ENDPOINT_HANGOVER;
    if (endpoint->silence_frames >= frames_for_ms(
            endpoint->config.end_silence_ms, endpoint->config.frame_ms)) {
        endpoint->state = JAMES_ENDPOINT_COMPLETE;
        return JAMES_ENDPOINT_EVENT_SPEECH_END;
    }
    return JAMES_ENDPOINT_EVENT_NONE;
}

james_endpoint_event_t james_endpoint_cancel(james_endpoint_t *endpoint)
{
    if (endpoint == NULL || endpoint->state == JAMES_ENDPOINT_DISARMED ||
        endpoint->state == JAMES_ENDPOINT_COMPLETE) {
        return JAMES_ENDPOINT_EVENT_NONE;
    }
    endpoint->state = JAMES_ENDPOINT_COMPLETE;
    return JAMES_ENDPOINT_EVENT_CANCELLED;
}

james_endpoint_event_t james_endpoint_report_overrun(james_endpoint_t *endpoint)
{
    if (endpoint == NULL || endpoint->state == JAMES_ENDPOINT_DISARMED ||
        endpoint->state == JAMES_ENDPOINT_COMPLETE) {
        return JAMES_ENDPOINT_EVENT_NONE;
    }
    endpoint->state = JAMES_ENDPOINT_COMPLETE;
    return JAMES_ENDPOINT_EVENT_OVERRUN;
}

bool james_endpoint_self_test(void)
{
    const james_endpoint_config_t config = {
        .frame_ms = 20,
        .start_confirmation_ms = 60,
        .end_silence_ms = 100,
        .no_speech_timeout_ms = 200,
        .maximum_utterance_ms = 300,
    };
    james_endpoint_t endpoint;
    if (!james_endpoint_init(&endpoint, &config)) {
        return false;
    }

    james_endpoint_arm(&endpoint);
    if (james_endpoint_process(&endpoint, true) != JAMES_ENDPOINT_EVENT_NONE ||
        james_endpoint_process(&endpoint, false) != JAMES_ENDPOINT_EVENT_NONE) {
        return false;
    }
    for (int index = 0; index < 2; ++index) {
        if (james_endpoint_process(&endpoint, true) != JAMES_ENDPOINT_EVENT_NONE) {
            return false;
        }
    }
    if (james_endpoint_process(&endpoint, true) !=
            JAMES_ENDPOINT_EVENT_SPEECH_START ||
        endpoint.state != JAMES_ENDPOINT_IN_SPEECH || endpoint.utterance_id != 1) {
        return false;
    }
    for (int index = 0; index < 4; ++index) {
        if (james_endpoint_process(&endpoint, false) != JAMES_ENDPOINT_EVENT_NONE) {
            return false;
        }
    }
    if (james_endpoint_process(&endpoint, false) !=
            JAMES_ENDPOINT_EVENT_SPEECH_END ||
        endpoint.state != JAMES_ENDPOINT_COMPLETE) {
        return false;
    }

    james_endpoint_arm(&endpoint);
    for (int index = 0; index < 2; ++index) {
        if (james_endpoint_process(&endpoint, true) != JAMES_ENDPOINT_EVENT_NONE) {
            return false;
        }
    }
    if (james_endpoint_process(&endpoint, true) !=
        JAMES_ENDPOINT_EVENT_SPEECH_START) {
        return false;
    }
    for (int index = 0; index < 3; ++index) {
        if (james_endpoint_process(&endpoint, false) != JAMES_ENDPOINT_EVENT_NONE) {
            return false;
        }
    }
    if (james_endpoint_process(&endpoint, true) != JAMES_ENDPOINT_EVENT_NONE ||
        endpoint.state != JAMES_ENDPOINT_IN_SPEECH) {
        return false;
    }

    james_endpoint_arm(&endpoint);
    for (int index = 0; index < 9; ++index) {
        if (james_endpoint_process(&endpoint, false) != JAMES_ENDPOINT_EVENT_NONE) {
            return false;
        }
    }
    if (james_endpoint_process(&endpoint, false) !=
        JAMES_ENDPOINT_EVENT_NO_SPEECH_TIMEOUT) {
        return false;
    }

    james_endpoint_arm(&endpoint);
    for (int index = 0; index < 2; ++index) {
        if (james_endpoint_process(&endpoint, true) != JAMES_ENDPOINT_EVENT_NONE) {
            return false;
        }
    }
    if (james_endpoint_process(&endpoint, true) !=
        JAMES_ENDPOINT_EVENT_SPEECH_START) {
        return false;
    }
    for (int index = 0; index < 11; ++index) {
        if (james_endpoint_process(&endpoint, true) != JAMES_ENDPOINT_EVENT_NONE) {
            return false;
        }
    }
    if (james_endpoint_process(&endpoint, true) !=
        JAMES_ENDPOINT_EVENT_MAX_UTTERANCE) {
        return false;
    }

    james_endpoint_arm(&endpoint);
    if (james_endpoint_cancel(&endpoint) != JAMES_ENDPOINT_EVENT_CANCELLED) {
        return false;
    }
    james_endpoint_arm(&endpoint);
    return james_endpoint_report_overrun(&endpoint) == JAMES_ENDPOINT_EVENT_OVERRUN;
}
