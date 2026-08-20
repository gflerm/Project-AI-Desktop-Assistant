# Project TARS --- P4 Voice Activity Detection Plan

**Status:** Version 0.2 --- Implementation and training-workflow alignment\
**Date:** 2026-08-20\
**Document role:** ESP32-P4 voice activity detection, endpointing, audio
buffering, FreeRTOS integration, tuning and test plan\
**Companion to:** `P4-FreeRTOS-Execution-Plan.md`,
`Speech-and-AI-Runtime-Evaluation.md`, `VAD-Implementation-TODO.md`,
`../VED Training/README.md` and
`../VED Training/docs/Voice-Corpus-and-Speaker-Enrollment-Test-Plan.md`

---

# 1. Objective

Voice activity detection (VAD) answers one narrow question:

> Does the current microphone audio contain human speech?

Project TARS uses that answer to:

- react visually as soon as speech begins;
- decide when to start sending useful audio to Pi 5 STT;
- decide when an utterance has ended;
- avoid streaming endless room silence;
- support interruption/barge-in later;
- retain push-to-talk as a deterministic fallback.

VAD does **not** determine what was said, identify the speaker, replace a wake
word, or decide whether a command is authorized.

## 1.1 What “VAD training” means in this project

The project does not train VAD to recognize the operator. The P4 VAD remains
speaker-independent. Its recorded corpus is used to:

- validate speech/no-speech decisions;
- select supported sensitivity/mode settings;
- tune endpoint start confirmation, pre-roll and end hangover;
- measure false activations, missed speech and clipped words;
- compare standalone ESP-SR VAD with AFE/VADNet using identical audio.

Operator recognition is a separate Pi 5 speaker-enrollment task using a
pretrained speaker-embedding model. The beginner PC recording workflow and
private corpus layout are in `../VED Training/README.md`. The executable
firmware/test sequence is tracked in `VAD-Implementation-TODO.md`.

---

# 2. Recommended Architecture

Use a staged implementation:

1. **Push-to-talk baseline** proves microphone, Wi-Fi and Pi 5 STT without VAD
   ambiguity.
2. **Standalone ESP-SR VAD** proves frame sizing, pre-roll, start/end events and
   tuning with the smallest software surface.
3. **ESP-SR Audio Front End (AFE) with VADNet** becomes the intended production
   path and can later combine VAD with noise suppression, acoustic echo
   cancellation and WakeNet.
4. **P4 low-power hardware VAD** is evaluated only for sleep/wake operation
   after the ES8311/LP-I2S clock and signal routing are physically verified.

```text
ES8311 / I2S DMA
        |
        v
audio_rx_task --- raw pre-roll ring (PSRAM)
        |
        v
AFE feed / fetch on Core 1
        |
        +---- processed PCM ----> utterance ring ----> Core 0 audio uplink
        |
        +---- VAD state --------> endpoint state machine
                                      |
                                      +--> UI LISTENING / HEARD events
                                      +--> STREAM_START
                                      +--> STREAM_END
```

The P4 is the primary endpointing authority because it has the original audio
and can respond without network latency. Pi 5 STT may run a secondary endpoint
detector as a safety check, but it must not silently discard P4 turn events.

---

# 3. Technology Choice

## 3.1 Production recommendation: ESP-SR AFE + VADNet

Espressif's AFE supports VAD, AEC, noise suppression, automatic gain control
and WakeNet in one audio-front-end pipeline. VADNet returns a speech/silence
state through the AFE fetch result and provides a VAD cache to recover audio
from before the detection trigger.

Use the official `espressif/esp-sr` component and pin an exact version after the
first verified build. At the time this plan was written, the component registry
reported 2.4.7 as the latest stable release; do not use an unbounded `*`
dependency in reproducible firmware.

References:

- [ESP-SR AFE documentation for ESP32-P4](https://docs.espressif.com/projects/esp-sr/en/latest/esp32p4/audio_front_end/README.html)
- [ESP-SR VADNet documentation](https://docs.espressif.com/projects/esp-sr/en/latest/esp32p4/vadnet/README.html)
- [ESP-SR component registry](https://components.espressif.com/components/espressif/esp-sr)
- [ESP-SR ESP32-P4 benchmark](https://docs.espressif.com/projects/esp-sr/en/latest/esp32p4/benchmark/README.html)

## 3.2 Standalone software VAD

The standalone API is useful for the first integration because it accepts
16-bit audio frames and returns `VAD_SPEECH` or `VAD_SILENCE`. It supports 8,
16 and 32 kHz audio and 10, 20 or 30 ms frames.

The first prototype should use:

```text
sample rate:       16,000 Hz
sample format:     signed 16-bit mono PCM
frame duration:    20 ms
samples per frame: 320
bytes per frame:   640
```

This aligns with the initial P4-to-Pi speech transport and gives sufficiently
fine timing without excessive task/queue overhead.

Reference: [ESP-SR `esp_vad.h` API](https://github.com/espressif/esp-sr/blob/master/include/esp32p4/esp_vad.h).

## 3.3 Low-power hardware VAD

ESP32-P4 also has a hardware VAD block associated with LP I2S. This may later
wake the device from a low-power state without continuously running VADNet.
However, LP I2S operates as a slave and the current board audio path uses the
ES8311 with clocks normally supplied by the P4. Treat this as a separate
hardware experiment, not the first conversational endpoint detector.

Reference: [ESP-IDF P4 hardware VAD documentation](https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/peripherals/vad.html).

---

# 4. Audio Front-End Modes

## 4.1 First VAD build: microphone only

Use one microphone input channel:

```text
input format: M
pipeline: microphone -> optional NS -> VADNet
```

This is sufficient while Project TARS is not listening during speaker
playback.

## 4.2 Later full-duplex build: microphone plus playback reference

Use an interleaved microphone and playback-reference input:

```text
input format: MR
M = microphone sample captured from ES8311
R = exact speaker PCM sample sent toward playback
pipeline: AEC -> optional NS -> VADNet -> optional WakeNet
```

The reference must be derived from the audio actually being sent to the
speaker path, with its timing preserved. Sending arbitrary TTS data or a
misaligned reference will weaken AEC and can make VAD trigger on Project TARS's
own voice.

Start half-duplex. Enable barge-in only after the `MR` path passes recorded
echo tests at representative speaker volumes.

---

# 5. FreeRTOS Task Design

The VAD path belongs to the P4 peripheral/media side and initially runs on Core
1.

| Task | Affinity | Responsibility |
|---|---:|---|
| `audio_rx_task` | Core 1 | Drain I2S DMA and construct exact audio frames |
| `afe_feed_task` | Core 1 | Interleave `M`/`R` when required and call AFE `feed()` |
| `afe_fetch_task` | Core 1 | Call AFE `fetch()`, consume processed PCM, VAD state and VAD cache |
| `endpoint_task` | Core 1 initially | Apply hysteresis, pre/post-roll and maximum-turn rules |
| `audio_uplink_task` | Core 0 | Send framed utterance audio/events to the Pi 5 |
| `state_task` | Core 0 | Convert endpoint events into visible companion states |

`audio_rx_task`, `afe_feed_task` and `afe_fetch_task` must block when waiting
for DMA/data. They must not poll in tight loops or perform network operations.

If AFE load delays display/audio I/O, leave the I2S task pinned to Core 1 and
benchmark moving `afe_fetch_task` or `endpoint_task` to no affinity. Do not
change affinity based on intuition alone.

---

# 6. Buffer Design

VAD is always delayed by at least some frames. Without pre-roll the first word
or consonant can be clipped.

Use two mechanisms:

1. preserve the official AFE `vad_cache` whenever returned;
2. maintain a project-owned raw/processed circular pre-roll buffer as a
   defensive mechanism and for diagnostics.

Initial bounded buffer proposal:

| Buffer | Initial duration | Memory at 16 kHz/16-bit mono | Location |
|---|---:|---:|---|
| I2S active DMA | Driver-sized | Small | Internal DMA-capable RAM |
| Frame staging | 2--4 frames | 1.25--2.5 KB | Internal RAM |
| Pre-roll | 500 ms | 16 KB | PSRAM |
| Post-roll/hangover | 800 ms maximum | 25.6 KB | PSRAM/streamed |
| Uplink jitter queue | 0.5--1.0 s | 16--32 KB | PSRAM |
| Diagnostic capture | Optional/bounded | Configuration-dependent | PSRAM or storage task |

The AFE determines its required feed and fetch chunk sizes. Query those sizes
at runtime; never assume the AFE chunk equals the chosen 20 ms transport frame.

On `SILENCE -> SPEECH`:

1. publish `STREAM_START`;
2. prepend the AFE VAD cache if present;
3. prepend only the additional project pre-roll needed to reach the configured
   target, avoiding duplicate samples;
4. continue streaming processed speech frames.

---

# 7. Endpoint State Machine

Do not map one VAD result directly to one network event. Use hysteresis and
turn rules.

```text
DISARMED
   |
   | push-to-talk / wake / tap
   v
ARMED_SILENCE
   |
   | stable speech >= start threshold
   v
IN_SPEECH
   |
   | silence begins
   v
HANGOVER
   |        |
   | speech | stable silence >= end threshold
   | returns| or maximum turn reached
   v        v
IN_SPEECH  COMPLETE
              |
              v
        ARMED_SILENCE or DISARMED
```

Initial parameters for bench testing:

```text
vad_mode:                 VAD_MODE_1
minimum speech trigger:   128 ms
AFE VAD delay/cache:      128 ms
project pre-roll target:  500 ms
minimum accepted turn:    250 ms
end-of-speech silence:    700 ms
maximum utterance:        20 s
post-roll after endpoint: 100--200 ms
```

These are starting points, not final product constants. Make them runtime
configuration values and tune them using recorded test audio.

## 7.1 Event contract

```c
typedef enum {
    TARS_VAD_SPEECH_START,
    TARS_VAD_SPEECH_CONTINUE,
    TARS_VAD_SPEECH_END,
    TARS_VAD_TIMEOUT,
    TARS_VAD_CANCELLED,
    TARS_VAD_OVERRUN,
} tars_vad_event_type_t;

typedef struct {
    tars_vad_event_type_t type;
    uint32_t utterance_id;
    int64_t timestamp_us;
    uint32_t audio_sequence;
    uint32_t buffered_preroll_bytes;
} tars_vad_event_t;
```

Every utterance receives a monotonically increasing ID. Audio chunks sent to
the Pi include that ID and a sequence number so reconnects, cancellation and
missing chunks are observable.

---

# 8. Coding Work Required

Yes, project-specific coding is required around the Espressif detector. The
model supplies frame-level speech/silence results; Project TARS must still
implement audio capture, buffering, endpointing, state events, Pi streaming,
metrics and failure recovery.

## 8.1 Component dependency

After selecting and verifying a compatible release, add an explicit dependency
to `main/idf_component.yml`, for example:

```yaml
dependencies:
  espressif/esp-sr:
    version: "2.4.7"
```

Keep the existing `esp_codec_dev` dependency for ES8311 audio. The first build
must verify compatibility with the project's ESP-IDF 6.0.2 baseline before the
version is adopted permanently.

## 8.2 Standalone VAD proof-of-concept structure

The exact include paths and signatures must be checked against the pinned
ESP-SR version. The intended structure is:

```c
#include "esp_vad.h"

#define VAD_SAMPLE_RATE_HZ 16000
#define VAD_FRAME_MS       20
#define VAD_SAMPLES        (VAD_SAMPLE_RATE_HZ * VAD_FRAME_MS / 1000)

static void vad_task(void *arg)
{
    int16_t frame[VAD_SAMPLES];
    vad_handle_t vad = vad_create_with_param(
        VAD_MODE_1,
        VAD_SAMPLE_RATE_HZ,
        VAD_FRAME_MS,
        128,   /* minimum speech duration */
        700);  /* minimum silence/noise duration */

    configASSERT(vad != NULL);

    for (;;) {
        /* Blocks until exactly one frame is available. */
        if (!audio_frame_receive(frame, sizeof(frame), portMAX_DELAY)) {
            continue;
        }

        vad_state_t state = vad_process_with_trigger(vad, frame);
        endpoint_process_frame(state, frame, VAD_SAMPLES);
    }
}
```

The production implementation must not place a large automatic buffer on a
task stack without checking the stack high-water mark. Prefer a startup-allocated
internal buffer where appropriate.

## 8.3 AFE/VADNet production structure

The AFE path should follow Espressif's documented handle/configuration model:

```c
srmodel_list_t *models = esp_srmodel_init("model");
afe_config_t *cfg = afe_config_init(
    "M",                 /* change to MR when AEC reference is ready */
    models,
    AFE_TYPE_SR,
    AFE_MODE_LOW_COST);

cfg->vad_init = true;
cfg->vad_mode = VAD_MODE_1;
cfg->vad_min_speech_ms = 128;
cfg->vad_min_noise_ms = 700;
cfg->vad_delay_ms = 128;

const esp_afe_sr_iface_t *afe = esp_afe_handle_from_config(cfg);
esp_afe_sr_data_t *afe_data = afe->create_from_config(cfg);
```

At runtime:

```c
/* Feed task: obtains the exact feed size requested by AFE. */
int feed_samples = afe->get_feed_chunksize(afe_data);
int feed_channels = afe->get_feed_channel_num(afe_data);
afe->feed(afe_data, interleaved_feed_buffer);

/* Fetch task: blocks for processed data and VAD result. */
afe_fetch_result_t *result = afe->fetch(afe_data);
if (result == NULL) {
    report_afe_failure();
    continue;
}

if (result->vad_cache_size > 0) {
    endpoint_prepend_vad_cache(result->vad_cache, result->vad_cache_size);
}

endpoint_process_afe_result(
    result->vad_state,
    result->data,
    result->data_size);
```

This is architectural scaffolding, not a blind copy-paste patch. Member names,
model partition configuration and result fields must be compiled against the
selected ESP-SR release and adapted from its current official example.

## 8.4 Module boundaries

Proposed firmware layout:

```text
main/
  audio/
    tars_audio_codec.c/.h       ES8311 and amplifier control
    tars_audio_capture.c/.h     I2S RX and frame creation
    tars_audio_playback.c/.h    I2S TX and playback reference
    tars_audio_ring.c/.h        bounded audio rings
  vad/
    tars_vad_backend.h          replaceable backend interface
    tars_vad_standalone.c       initial ESP-SR standalone backend
    tars_vad_afe.c              AFE/VADNet production backend
    tars_endpoint.c/.h          hysteresis and utterance boundaries
    tars_vad_metrics.c/.h       counters and latency measurements
  transport/
    tars_audio_uplink.c/.h      Pi stream protocol
```

Backend contract:

```c
typedef struct {
    esp_err_t (*start)(void);
    esp_err_t (*process)(const int16_t *pcm, size_t samples);
    esp_err_t (*reset)(void);
    esp_err_t (*stop)(void);
} tars_vad_backend_t;
```

Keep endpoint policy outside the VAD backend. This allows VADNet, standalone
ESP VAD, WebRTC VAD or a deterministic test double to be compared without
rewriting the conversation pipeline.

---

# 9. Pi 5 Streaming Protocol

The P4 should send explicit turn events rather than only an undifferentiated
PCM socket.

```text
AUDIO_START  utterance_id, format, sample_rate, channels, timestamp
AUDIO_CHUNK  utterance_id, sequence, timestamp, PCM bytes
AUDIO_END    utterance_id, last_sequence, reason
AUDIO_CANCEL utterance_id, reason
```

Valid end reasons include:

```text
vad_silence
push_to_talk_release
maximum_duration
user_cancel
audio_overrun
network_failure
speaker_interruption
```

The Pi must acknowledge `AUDIO_START`, reject unknown formats explicitly and
make duplicate/missing sequence numbers visible in metrics.

---

# 10. VAD and Visible Face States

| Endpoint event | Display state |
|---|---|
| Armed, silence | `ATTENTIVE` or low-motion `LISTENING` |
| Speech starts | `LISTENING` immediately |
| Speech continues | `LISTENING` pulse driven locally |
| Endpoint detected | Brief `HEARD` |
| Audio sent/finalizing | `THINKING` |
| False trigger rejected | Settle gently to prior state |
| Timeout | `UNCERTAIN` with retry affordance |
| Audio overrun | `ERROR`, then recover |

The UI must not wait for Pi 5 confirmation before showing `LISTENING`.

---

# 11. Tuning Strategy

Do not tune VAD by speaking at the device a few times and selecting values that
"feel right." Build a labeled corpus from the actual enclosure and room.

Record examples of:

- quiet room silence;
- HVAC/fan/printer noise;
- keyboard and mouse sounds;
- chair movement and desk impacts;
- speech at near, normal desk and far distances;
- soft, normal and loud speech;
- short acknowledgements such as "yes" and "no";
- speech with pauses;
- speaker playback at several volumes;
- overlapping user speech and speaker playback;
- different device orientations and enclosure prototypes.

Label speech start/end times and evaluate:

```text
false activations per hour
missed utterance rate
first-speech clipping in milliseconds
end-of-speech latency
short-utterance rejection rate
speaker-echo activation rate
CPU use per core
internal RAM and PSRAM use
audio overrun/underrun count
```

Maintain separate profiles if necessary:

```text
quiet_room
normal_desk
noisy_room
speaker_active
```

Prefer one robust default over many fragile automatic modes.

---

# 12. Test Plan

## V0 --- Deterministic endpoint unit tests

- feed synthetic VAD state sequences into `tars_endpoint`;
- verify start debounce, hangover, timeout, cancellation and utterance IDs;
- verify no duplicate `START`/`END` events;
- verify queue-full and overrun behavior.

**Exit:** endpoint policy is fully testable without a microphone or model.

## V1 --- Recorded-file standalone VAD

- process known 16 kHz mono WAV fixtures;
- compare detected boundaries to labels;
- verify the first phoneme is retained through pre-roll;
- record CPU and memory use.

## V2 --- Live onboard microphone

- run standalone VAD with the ES8311 capture path;
- log speech/silence transitions and levels;
- test room noise and desk sounds;
- tune only configuration, not code structure.

## V3 --- AFE/VADNet

- enable the pinned ESP-SR model partition;
- compare VADNet against standalone results on the same corpus;
- validate AFE VAD cache handling;
- select low-cost versus high-performance mode from measurements.

## V4 --- Pi 5 streaming

- prepend pre-roll correctly;
- verify chunk sequence and turn boundaries;
- measure speech start to first uplink audio;
- measure end-of-speech to Pi STT finalization.

## V5 --- Playback and AEC

- add the synchronized playback reference;
- use `MR` AFE input;
- test speaker echo at representative volumes;
- do not enable barge-in until false triggers are acceptable.

## V6 --- Long-running stress

- run display animation, Wi-Fi, microphone, VAD and playback together;
- execute at least a four-hour soak test;
- require zero unexplained audio overruns, memory growth or watchdog events.

---

# 13. Failure Handling

| Failure | Required behavior |
|---|---|
| VAD backend fails to initialize | Fall back to push-to-talk |
| Model partition missing/corrupt | Report fault; keep microphone diagnostic available |
| Audio ring overrun | End/cancel current turn, reset VAD and recover |
| Network unavailable | Do not accumulate unbounded speech; end turn locally |
| Maximum utterance reached | Close stream explicitly and ask user to continue if needed |
| Repeated false activations | Increase logging, use stricter profile or fall back to push-to-talk |
| Speaker echo triggers VAD | Disable barge-in; repair reference/AEC/acoustics before retrying |
| PSRAM pressure | Reduce diagnostic history before reducing real-time buffers |

---

# 14. Security and Privacy

- show a visible microphone/listening state whenever voice audio is processed;
- provide a physical or clearly accessible microphone mute mechanism;
- do not stream audio before push-to-talk/wake/armed policy permits it;
- discard bounded pre-roll continuously unless a legitimate speech turn starts;
- make diagnostic audio recording opt-in and time-limited;
- never place captured audio in ordinary logs;
- authenticate the Pi 5 endpoint even on the trusted LAN;
- expose whether processing is P4-local, Pi-local or cloud-routed.

---

# 15. Decisions

## VAD001 --- P4 owns primary VAD and endpointing

**Status:** Adopted baseline.

This provides immediate response and avoids network dependence for turn
boundaries.

## VAD002 --- Push-to-talk precedes automatic VAD

**Status:** Adopted implementation order.

The deterministic path isolates audio/network faults before VAD tuning begins.

## VAD003 --- ESP-SR AFE/VADNet is the production candidate

**Status:** Candidate pending P4 benchmarks.

It provides a path to VAD, VAD cache, AEC, noise suppression and WakeNet within
one supported Espressif framework.

## VAD004 --- Endpoint policy is separate from detector implementation

**Status:** Architectural requirement.

Detector backends produce frame state; Project TARS owns buffering, hysteresis,
turn boundaries and events.

## VAD005 --- Preserve speech with VAD cache and bounded pre-roll

**Status:** Architectural requirement.

The first word must not be clipped merely because a detector requires several
frames to trigger.

## VAD006 --- Barge-in requires a verified playback reference and AEC

**Status:** Safety/quality gate.

Do not treat the companion's own speaker output as user speech.

## VAD007 --- Hardware LP VAD is a later low-power experiment

**Status:** Deferred pending ES8311/LP-I2S compatibility verification.

---

# 16. Immediate Next Actions

1. Complete ES8311 16 kHz mono capture and save a bounded diagnostic WAV.
2. Implement `tars_endpoint` with synthetic unit tests before adding ESP-SR.
3. Add a pinned `esp-sr` dependency and compile the standalone VAD API.
4. Feed recorded WAV frames through standalone VAD and measure boundaries.
5. Add the 500 ms pre-roll ring and verify the first word is intact.
6. Publish visible `LISTENING`, `HEARD` and timeout events.
7. Stream explicit `AUDIO_START/CHUNK/END` messages to a Pi test receiver.
8. Integrate AFE/VADNet and compare against the same labeled corpus.
9. Add `MR` playback reference/AEC only after half-duplex is stable.
10. Evaluate low-power hardware VAD only after the conversational path works.

The operator recording matrix, private corpus layout, VAD/STT scoring and
speaker-enrollment workflow are specified in `../VED Training/`. PC recordings
first prove the workflow, but final VAD acceptance must use recordings captured
through the deployed P4 microphone path. Progress and exit evidence must be
recorded against `VAD-Implementation-TODO.md`.
