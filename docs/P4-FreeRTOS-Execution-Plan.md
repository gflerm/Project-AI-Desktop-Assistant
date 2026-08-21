# Project James --- P4 FreeRTOS Execution Plan

**Status:** Version 0.3 --- Initial PTT firmware built\
**Date:** 2026-08-21\
**Document role:** ESP32-P4 task architecture, core affinity, memory use,
audio/network pipeline and staged implementation plan\
**Companion to:** `Hardware-Architecture-and-Inventory.md`,
`Firmware-Software-Roadmap.md` and `P4-Voice-Activity-Detection-Plan.md`

> 🟢 **AUDIO PROTOTYPE ACTIVE — 2026-08-21:** The user resumed a bounded P4
> microphone/speaker pass. GPIO35 BOOT is temporary PTT. Camera, displays,
> motion, automatic VAD and wake word stay disabled until this round trip is
> physically proven.

---

# 1. Short Answer

Yes. The P4 can handle the physical companion workload when the compute split
is kept clear:

- the **P4** owns the displays, sensors, future motion, microphone capture,
  speaker playback, immediate interaction state and the Wi-Fi session;
- the onboard **ESP32-C6** performs the Wi-Fi radio work and exposes it to the
  P4 through ESP-Hosted over SDIO;
- the **Raspberry Pi 5** performs normal STT, LLM inference and TTS;
- the P4 streams captured audio to the Pi 5 and receives synthesized audio for
  playback, plus text and control metadata for display/logging purposes.

The P4 should not normally run a modern STT model, general-purpose LLM or
high-quality neural TTS locally. It can run wake-word detection, VAD, audio
conditioning and limited offline commands if benchmarks justify them.

The two high-performance P4 cores are symmetric. There is no intrinsically
special "main" application core. This plan uses **Core 0 as the service/control
core** and **Core 1 as the real-time peripheral/media core** as a project
convention, while allowing selected non-critical tasks to remain unpinned so
FreeRTOS SMP can balance them.

---

# 2. Verified Hardware Basis

The Waveshare ESP32-P4-WIFI6 Kit A provides:

- two 360 MHz high-performance RISC-V cores used by ESP-IDF FreeRTOS SMP;
- a separate low-power RISC-V core, which is not counted as a third general
  high-performance application core in this plan;
- 32 MB in-package PSRAM and 32 MB NOR flash;
- an ESP32-C6 Wi-Fi 6/BLE coprocessor connected over SDIO;
- an onboard SMD microphone;
- an ES8311 audio codec;
- an NS4150B power amplifier;
- a connector supporting an external 8 ohm, 2 W speaker;
- MIPI-CSI/ISP, JPEG and H.264 hardware useful for later camera work.

The board audio wiring documented by Waveshare is:

| Signal | P4 GPIO |
|---|---:|
| ES8311 I2C SDA | GPIO7 |
| ES8311 I2C SCL | GPIO8 |
| I2S data to codec / DSDIN | GPIO9 |
| I2S word select / LRCK | GPIO10 |
| I2S data from codec / ASDOUT | GPIO11 |
| I2S bit clock / SCLK | GPIO12 |
| I2S master clock / MCLK | GPIO13 |
| NS4150B amplifier enable | GPIO53 |
| Temporary BOOT PTT input | GPIO35, active-low |

References:

- [Waveshare ESP32-P4-WIFI6 board documentation](https://www.waveshare.com/wiki/ESP32-P4-WIFI6)
- [ESP-IDF FreeRTOS SMP overview for ESP32-P4](https://docs.espressif.com/projects/esp-idf/en/latest/esp32p4/api-reference/system/freertos.html)
- [ESP-IDF ESP32-P4 I2S documentation and ES8311 example](https://docs.espressif.com/projects/esp-idf/en/release-v5.5/esp32p4/api-reference/peripherals/i2s.html)
- [Espressif `esp_codec_dev` component](https://components.espressif.com/components/espressif/esp_codec_dev)
- [Espressif `esp_wifi_remote` component](https://components.espressif.com/components/espressif/esp_wifi_remote)

---

# 3. Core-Allocation Principle

Do not divide the firmware into two monolithic loops. Use small blocking tasks,
queues, ring buffers and event groups. Pin only tasks whose latency or hardware
ownership benefits from affinity.

```text
CORE 0 --- SERVICE / CONTROL             CORE 1 --- PERIPHERAL / MEDIA

Pi 5 session and protocol                I2S microphone capture
audio uplink/downlink packetization      I2S speaker playback
conversation state machine               three SPI LCD flushes
commands and response metadata           touch and sensor collection
health supervision                       future motor safety/control
OTA/configuration                        future camera acquisition
         |                                         |
         +---------- queues/ring buffers ---------+
```

This is an initial testable allocation, not an irreversible hardware rule.
Core assignment must remain configuration-driven and may change after runtime
measurements.

---

# 4. Initial FreeRTOS Task Map

Priorities below are relative starting points. They must be reconciled with the
actual ESP-IDF system-task priorities in the selected IDF version and tuned from
measurements. Every task must block on a queue, notification, event or DMA
operation when idle.

| Task | Initial affinity | Relative priority | Responsibility |
|---|---:|---:|---|
| `audio_rx_task` | Core 1 | Highest application | Drain microphone/I2S DMA into bounded audio blocks |
| `audio_tx_task` | Core 1 | Highest application | Feed speaker/I2S DMA without underruns |
| `motion_safety_task` | Core 1 | High | Future hard limits, stop conditions and actuator deadlines |
| `camera_capture_task` | Core 1 | High | Future CSI/ISP acquisition only; disabled initially |
| `display_flush_task` | Core 1 | Medium-high | Serialize SPI transactions to the three LCDs |
| `sensor_task` | Core 1 | Medium | Poll/receive touch and environmental sensors |
| `pi_session_task` | Core 0 | High | Maintain authenticated Pi 5 connection, heartbeat and reconnect |
| `audio_uplink_task` | Core 0 | High | Send captured audio blocks to Pi 5 STT service |
| `audio_downlink_task` | Core 0 | High | Receive synthesized audio and place it in playback buffer |
| `protocol_task` | Core 0 | Medium-high | Parse commands, partial text, final text and tool/state events |
| `state_task` | Core 0 | Medium | Own the companion state machine and publish display/audio events |
| `animation_task` | Unpinned initially | Medium-low | Select gesture frames and build lightweight display updates |
| `health_task` | Unpinned | Low | Record watermarks, latency, task runtime and subsystem health |
| `storage_task` | Core 0 | Low | Deferred NVS/config/log writes; never block real-time tasks |

## 4.1 Why audio I/O is on the peripheral core

Audio capture and playback have hard service deadlines. Moving bytes between
I2S DMA and bounded ring buffers is peripheral work and belongs on Core 1.
Encoding, networking and response interpretation are separate tasks on Core 0.
This prevents a slow socket or Pi response from causing an I2S underrun or
microphone overrun.

## 4.2 Why networking is on the service core

The ESP32-C6 offloads the Wi-Fi radio and Wi-Fi protocol implementation, but the
P4 still runs the host transport, network stack and Project James application
protocol. Core 0 owns the project-level session and packet flow. ESP-IDF system
tasks must retain their configured affinities; the project should not attempt
to repin private ESP-IDF or ESP-Hosted tasks without a measured reason.

## 4.3 Why not pin everything

ESP-IDF uses dual-core SMP. Unpinned low-criticality work can run wherever
capacity exists. Excessive pinning can leave one core overloaded while the other
is idle, and can increase lock contention. Start with affinity only for hardware
ownership and deadline-sensitive tasks.

## 4.4 First implemented PTT slice

The initial firmware pins the continuous 20 ms microphone producer to Core 1.
The PTT/WebSocket state machine runs on Core 0, batches five frames per network
message and never becomes the capture producer. Speaker playback uses a
separate output handle for the same ES8311 codec and deliberately gates
microphone capture, so this test is half-duplex and cannot self-trigger from
James's voice.

The current audio memory path remains internal-RAM-first: a 25-frame queue
stores 500 ms/16,400 bytes of captured PCM, capture and PTT task stacks are
4 KiB and 10 KiB, and the PTT task reuses five-frame/100 ms staging. Returned
TTS chunks pass from the 8 KiB WebSocket assembly buffer directly to ES8311/I2S;
there is no whole-reply playback buffer. PSRAM remains available for future
pre-roll/history and display/camera assets rather than time-critical DMA.

Physical startup on 2026-08-21 verified separate ES8311 microphone and speaker
handles at 16 kHz and live, unclipped microphone samples. The first LAN attempt
could not associate because the configured/visible `WETOHOST5.8` SSID is 5 GHz;
the ESP32-C6 requires a 2.4 GHz access point. After switching to
`WETOHOST2.4`, the P4 received `192.168.8.131`, authenticated to Titanium and
reached the BOOT-PTT ready state. The subsequent physical turn captured 2.50
seconds of speech without clipping, transcribed “Who are you and what do you
do?” exactly, received the deterministic James identity response and completed
speaker playback. ES8311 output was then tuned from 65% through 90% to **95%**;
the user confirmed the raised level was much better. The NS4150B gain remains
fixed in hardware and GPIO53 remains enable-only.

---

# 5. Voice and Conversation Data Flow

## 5.1 Recommended normal path

```text
ONBOARD MICROPHONE
  -> ES8311 ADC / I2S DMA
  -> P4 audio_rx_task
  -> optional P4 filtering / VAD / wake word
  -> bounded PSRAM audio history + internal DMA blocks
  -> Wi-Fi through ESP32-C6
  -> Pi 5 STT
  -> Pi 5 local/cloud LLM routing
  -> Pi 5 TTS
  -> streamed audio + text/state metadata
  -> Wi-Fi through ESP32-C6
  -> P4 audio_downlink_task
  -> P4 audio_tx_task
  -> ES8311 DAC -> NS4150B -> 8 ohm speaker
```

The visible `LISTENING`, `HEARD` and `THINKING` states must be triggered locally
before a network round trip completes.

## 5.2 Initial audio format

Start with simple, measurable audio:

- microphone: 16 kHz, 16-bit, mono PCM for speech;
- raw rate: approximately 32 KB/s before protocol overhead;
- audio block duration: 10--20 ms;
- packet aggregation: 20--100 ms, chosen from latency/jitter tests;
- playback: use the TTS service's native rate where supported, otherwise agree
  one PCM format between P4 and Pi 5.

Raw speech PCM is small relative to normal Wi-Fi throughput and avoids adding a
codec during the first integration. Add Opus or another compressed transport
only if measurements show a need.

## 5.3 Text versus audio return

The Pi 5 should return both:

- text and state metadata for logging, display and conversation history;
- streamed synthesized audio for immediate speaker playback.

Receiving text and then performing high-quality TTS on the P4 is not the
baseline. A small local phrase bank or lightweight fallback synthesizer may be
added later for offline acknowledgements, alarms and degraded operation.

## 5.4 Full-duplex limitation

The board provides the required capture and playback hardware, but this does
not automatically solve acoustic echo. Early prototypes should support:

1. half-duplex or push-to-talk;
2. mute microphone capture during speaker playback when necessary;
3. a playback-reference stream for later acoustic echo cancellation;
4. barge-in only after echo, gain and physical speaker/microphone placement are
   measured.

---

# 6. Memory Plan

The 32 MB PSRAM is valuable, but it does not make all memory equally fast.

## 6.1 Keep in internal RAM

- I2S DMA descriptors and active DMA buffers;
- SPI/LCD DMA buffers required by the selected driver;
- interrupt data and short real-time queues;
- critical task stacks and task-control structures;
- small frequently accessed state objects;
- data needed while flash/cache access is unavailable.

## 6.2 Place in PSRAM where supported

- gesture and animation source/frame caches;
- one or more LCD frame buffers if the driver supports the memory path;
- microphone pre-roll and jitter buffers;
- received TTS jitter buffer beyond the active DMA window;
- camera frames and encoded image/video buffers;
- larger network message bodies and diagnostic history;
- optional model data for measured lightweight wake/VAD functions.

## 6.3 Rules

- allocate bounded buffers at startup where practical;
- avoid allocation/free operations in the real-time audio path;
- use watermarks and counters for every ring buffer;
- reserve internal RAM for DMA and latency-critical use;
- do not assume task stacks belong in PSRAM by default;
- test PSRAM bandwidth contention between displays, audio and future camera
  capture.

---

# 7. Inter-Core Contracts

Tasks must exchange ownership through explicit queues or ring buffers rather
than shared mutable globals.

Minimum contracts:

| Contract | Producer | Consumer | Backpressure policy |
|---|---|---|---|
| `mic_audio_ring` | `audio_rx_task` | `audio_uplink_task` | Drop oldest only after recording overrun metric |
| `tts_audio_ring` | `audio_downlink_task` | `audio_tx_task` | Pause network reads or reject stream before underrun cascade |
| `display_event_queue` | `state_task` | `animation_task` | Coalesce obsolete state/animation events |
| `display_frame_queue` | `animation_task` | `display_flush_task` | Keep newest frame; do not build an unbounded backlog |
| `sensor_event_queue` | `sensor_task` | `state_task` | Debounce and timestamp at source |
| `motion_command_queue` | `state_task` | `motion_safety_task` | Validate limits; safe stop wins over all other commands |
| `health_event_queue` | all tasks | `health_task` | Lossy for repetitive telemetry, lossless for faults where possible |

---

# 8. Display, Sensors and Future Motion

The three auxiliary LCDs remain Core 1 peripherals. `display_flush_task` must
be the single owner of the SPI devices. Other tasks request state/frames; they
must never write directly to an LCD driver.

Future motion must use a dedicated safety task and hardware-appropriate PWM,
MCPWM, RMT or motor-controller peripherals. Network commands may request
movement but must not directly drive motors. Local limits, current/temperature
faults and an emergency stop must take precedence over conversational logic.

Sensor drivers should timestamp and normalize data on Core 1, then publish
small events to Core 0. Avoid continuous high-rate polling when an interrupt or
peripheral DMA path is available.

---

# 9. Future Vision

Vision should not simply be placed on the peripheral core as one large task.
Split it into stages:

```text
Core 1 / hardware: CSI capture -> ISP -> JPEG/H.264 encode
Core 0 / service:  frame selection -> upload -> result handling
Pi 5 / Jetson:     object detection, recognition and heavy inference
```

The P4 may later perform low-cost frame selection, motion/change detection,
privacy masking, resizing or hardware-assisted encoding. Heavy vision models
should remain on the Pi 5, Jetson or cloud unless a benchmark proves a specific
P4 model useful without damaging audio/display responsiveness.

Enable camera work only after display, audio and Wi-Fi meet their latency and
stability targets.

---

# 10. Failure and Degraded Modes

| Failure | Required P4 behavior |
|---|---|
| Pi 5 unavailable | Remain responsive; show offline/degraded state; allow local controls |
| Wi-Fi unavailable | Retry with backoff; keep display, sensors and local gestures operational |
| STT timeout | Stop capture cleanly; report timeout; allow retry |
| TTS stream stalls | Avoid repeating stale audio; return to a clear state |
| Microphone overrun | Increment metric, reset cleanly and preserve UI responsiveness |
| Speaker underrun | Record metric, insert silence and recover without reboot |
| Display bus fault | Isolate/reinitialize display path without stopping audio/network tasks |
| Sensor fault | Mark sensor unhealthy; do not block the event/state system |
| Motor fault | Immediate local safe stop independent of Pi 5 or network state |
| PSRAM allocation failure | Reject optional feature; preserve core audio/control operation |

---

# 11. Implementation Phases

## P0 --- Runtime instrumentation

- create task registry and common health metrics;
- record CPU utilization per core, stack high-water marks and heap state;
- expose internal/PSRAM free space and largest-block metrics;
- add queue/ring-buffer watermarks and watchdog coverage.

**Exit:** empty supervised tasks run for 24 hours without watchdog or memory
growth.

## P1 --- Board audio loopback

- initialize I2C, ES8311, I2S and GPIO53 amplifier control;
- capture onboard microphone audio;
- play a known PCM sample through an attached 8 ohm, 2 W speaker;
- implement controlled microphone-to-speaker echo test;
- measure DMA stability and audio latency.

**Exit:** continuous capture and playback have no unexplained overrun/underrun
over a one-hour stress test.

## P2 --- Wi-Fi and Pi 5 session

- initialize ESP-Hosted/`esp_wifi_remote` over SDIO;
- connect to trusted Wi-Fi;
- discover or configure the Pi 5 endpoint;
- add heartbeat, reconnect with backoff and versioned message envelopes;
- measure round-trip latency, throughput and packet loss.

**Exit:** the P4 reconnects automatically after AP and Pi restarts.

## P3 --- Streaming microphone to Pi 5 STT

- add bounded PCM uplink;
- implement push-to-talk first;
- add speaker-independent P4 VAD after the fixed path is reliable;
- keep VAD backend processing and endpoint/pre-roll policy separate;
- calibrate and evaluate VAD with the private `VED Training` corpus;
- display listening/heard/thinking locally;
- receive partial/final transcription metadata.

**Exit:** repeated utterances reach the Pi 5 without audio loss and produce
stable transcription latency.

## P4 --- Pi 5 LLM and streamed TTS

- send final text to the Pi orchestration service;
- receive partial/final response text;
- stream Pi-generated TTS audio to the P4;
- drive speaking gestures from playback amplitude;
- support cancellation and interruption.

**Exit:** a full listen -> STT -> LLM -> TTS -> playback cycle runs repeatedly
without display stalls or audio faults.

**Baseline evidence (2026-08-21):** one complete physical PTT cycle passed.
Repeated-turn, timing-distribution, reconnect and soak evidence remain required
for the phase exit.

## P5 --- Three LCDs and concurrent stress

- integrate gesture assets and independent chip-select control;
- run animation during simultaneous audio and network traffic;
- measure SPI utilization, frame pacing and both-core load;
- tune task affinity and priorities from evidence.

**Exit:** representative conversation plus animation remains responsive for a
four-hour soak test.

## P6 --- Sensors and motion foundation

- add normalized sensor events;
- define motion command and safety contracts;
- implement safe-stop behavior before physical movement;
- add only one actuator class at a time.

## P7 --- Vision experiment

- add camera capture and hardware encoding;
- benchmark PSRAM bandwidth and audio/display interference;
- upload selected frames to Pi 5 or Jetson inference;
- retain vision only if the measured interaction quality remains acceptable.

---

# 12. Acceptance Metrics

Record at minimum:

```text
Core 0 and Core 1 utilization and worst-case saturation
minimum task stack high-water mark
internal heap and PSRAM free/largest blocks
microphone overruns and speaker underruns
audio capture-to-uplink latency
Pi response round-trip latency
TTS time to first audio
network reconnect time
LCD frame time and dropped/coalesced frames
queue and ring-buffer high-water marks
watchdog events
temperature during sustained operation
```

Initial targets should be established after the first working baseline. Do not
invent hard numbers before the audio, display and network drivers run together.

---

# 13. Decisions

## P4E001 --- Use ESP-IDF FreeRTOS SMP

**Status:** Adopted.

The P4 runs ESP-IDF/FreeRTOS and uses both high-performance cores.

## P4E002 --- Core 0 is the initial service/control core

**Status:** Provisional; benchmark-driven.

It owns Project James networking, Pi session, protocol and state orchestration.

## P4E003 --- Core 1 is the initial peripheral/media core

**Status:** Provisional; benchmark-driven.

It owns time-sensitive audio I/O, LCD flush, sensors and future actuator safety.

## P4E004 --- Pi 5 owns normal STT, LLM and TTS

**Status:** Adopted baseline.

The P4 captures/plays audio and maintains immediate interaction; the Pi 5
performs the heavier speech and inference workloads.

## P4E005 --- Use PSRAM for capacity, internal RAM for deadlines

**Status:** Architectural rule.

Large caches and history may use PSRAM. DMA, critical stacks and short
real-time data stay in suitable internal memory unless a driver explicitly
supports otherwise.

## P4E006 --- Pin selectively, measure, then revise

**Status:** Architectural rule.

Affinity is a tool for latency and ownership, not a permanent division that
prevents FreeRTOS SMP from using available CPU capacity.

---

# 14. Immediate Next Actions

1. Confirm the attached speaker is 8 ohm and no more than 2 W.
2. Port the Waveshare/ESP-IDF ES8311 echo example into a small board-audio
   diagnostic.
3. Add runtime metrics before adding production tasks.
4. Bring up ESP-Hosted Wi-Fi and a Pi 5 heartbeat service.
5. Stream fixed 16 kHz mono PCM from the microphone to a Pi test receiver.
6. Return a known PCM response stream from the Pi to the P4 speaker.
7. Add STT, LLM and TTS only after the bidirectional audio transport is stable.
8. Integrate the three LCD state assets and stress all paths concurrently.

Detailed VAD/endpoint implementation, buffering and tuning are specified in
`P4-Voice-Activity-Detection-Plan.md`. The ordered implementation goals and
completion evidence are tracked in `Project-TODO-and-Verification.md`; private PC and
P4 recordings belong under `../VED Training/recordings/` and must not be
committed.
