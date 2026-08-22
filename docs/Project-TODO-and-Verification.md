# Project James — Project TODO and Verification

**Status:** Version 0.3 — Primary implementation, test, and verification checklist

**Date:** 2026-08-21

**Owner:** Project James implementation and verification workstreams

**Companion documents:** [VAD architecture](P4-Voice-Activity-Detection-Plan.md),
[Pi gateway and Windows voice test](Pi-Gateway-and-Windows-Voice-Test.md),
[FreeRTOS execution plan](P4-FreeRTOS-Execution-Plan.md),
[firmware build guide](Firmware-Build-Guide.md),
[P4-to-Pi audio protocol](P4-Pi-Audio-Protocol.md), and
[VED Training start page](../VED%20Training/README.md), and
[James teaching and response improvement plan](James-Teaching-and-Response-Improvement-Plan.md)

> 🟢 **P4 AUDIO WORK RESUMED — 2026-08-21:** The Windows tester is no longer the
> active acceptance client. The immediate target is the connected ESP32-P4,
> using only its onboard microphone and attached speaker. Camera, displays,
> automatic VAD and vision remain out of scope for this first physical pass.
> GPIO35 BOOT is the temporary active-low push-to-talk control: hold to record,
> release to send, then play the Pi-generated response half-duplex.

> 🟢 **GATEWAY BASELINE — 2026-08-21:** Automatic local/cloud routing and
> `system.status.readonly` are deployed on the Pi. Forty-seven gateway tests
> pass. The Windows tester remains compatible but is retained as a diagnostic
> tool only. Final NUC/host assignment remains paused.

- [x] Make **James** the spoken assistant and project name; remove the previous
  fictional-character name from first-party source, paths and documentation.
- [x] Add a GitHub-detectable root Apache License 2.0, `NOTICE`, and a clear
  `LICENSE-SCOPE.md` that excludes third-party and separately licensed assets.
- [x] Migrate the live Pi services and P4 firmware to the renamed `james_*`
  packages, service units, configuration names and `JAM1` wire identifier in one
  coordinated, rollback-safe deployment. Verified end to end on 2026-08-22;
  the retained legacy services are disabled and available for rollback.
- [x] Route identity questions deterministically without an LLM call; live Pi
  verification returned `system:identity` / `identity-registry` in 1 ms.
- [x] Pass all 49 gateway tests on the Pi after the James identity update.

- [x] Route deterministic time, weather and Pi-status queries before any LLM.
- [x] Route current, research, long-context and high-stakes requests to Gemini.
- [x] Route routine requests to local Ollama with an eight-second deadline.
- [x] Escalate local refusal, empty response, error or timeout to Gemini in the
  same turn.
- [x] Add bounded Wikipedia grounding when Gemini is unavailable or rate-limited.
- [x] Record provider, routing reason, fallback, grounding and timing telemetry.
- [x] Deploy read-only Pi temperature, fan RPM/PWM/state, load, RAM, disk,
  uptime and component-health reporting with no command/write interface.
- [x] Benchmark `qwen3:4b-instruct`: correct 4/4; too slow for spoken default.
- [x] Retain 16 kHz, 16-bit mono capture and playback; 8 kHz was rejected
  because it would reduce STT quality without addressing model latency.
- [x] Raise Gemini output capacity from 160 to 320 tokens after a correct
  multi-part answer was truncated during its third item; retain concise spoken
  response prompting.
- [x] Refine the deployed personality for complete multi-part answers,
  voice-first prose, brief ambiguity handling, reduced encyclopedia-style
  expansion, and restrained wit after the useful answer.

### Candidate and deployed local tools

- [x] Read-only network health: hostname, DNS, internet reachability and
  latency.
- [ ] Read-only NVMe/storage health and capacity warnings.
- [ ] Read-only service error summary and recent James failures.
- [x] Ollama model and active/waiting inference-queue status.
- [ ] Microphone level, clipping, silence and STT-confidence diagnostics.
- [ ] Scoped local document search and retrieval from approved directories.
- [ ] Timers, alarms and reminders with explicit create/cancel confirmation.
- [ ] Calendar, email or smart-device tools only after account/permission review.

Read-only tools may run automatically when explicitly requested. Any tool that
changes files, services, reminders, accounts or physical devices requires a
separate permission policy and a confirmed result before James claims success.

### Current James quality and teaching work

The 2026-08-21 review covered all 60 private recorded turns, 390 gateway
telemetry events, the CSV export and all five benchmark/smoke artifacts. The
evidence and phased remedy are in the
[James teaching and response improvement plan](James-Teaching-and-Response-Improvement-Plan.md).

- [x] Review all recorded prompt/response JSON, JSONL and CSV evidence and
  classify the observed failure patterns.
- [x] Identify contaminated transcript-correction data; the reported 64.5% WER
  is not valid until its audio references are manually verified.
- [x] Introduce feedback schema version 2 with separate transcript, answer,
  route/tool, preferred-answer and approval fields.
- [x] Bind feedback to immutable turn UUIDs and migrate the existing 60 turns
  into a review queue without auto-promoting ambiguous corrections.
- [x] Build a replayable regression suite from the reviewed real prompts and
  preserve all 60 private turns in a zero-auto-promotion review queue.
- [x] Add a live capability registry, multi-intent composition and stricter
  intent contracts before any model fine-tuning.
- [x] Preserve all tool/model results in one conversation ledger and verify
  numbered follow-ups such as “repeat point 3”.
- [x] Record provider finish reason, detect incomplete answers before TTS and
  enforce single-flight local inference with bounded cancellation.
- [ ] Collect at least 50 audio-verified utterances and 50 reviewed answer cases
  before evaluating any training dataset.
- [ ] Consider LoRA/fine-tuning only after 200–500 approved examples and a
  held-out quality suite exist; training must not run on the Pi 5.
- [x] Deploy explicit Pi-local persistent memory with remember/list/soft-forget,
  cloud sharing disabled by default, and bulk deletion blocked from chat.
- [x] Deploy read-only network/DNS/internet and Ollama active/waiting queue
  status tools.
- [x] Pass 47 gateway tests, five Windows feedback/capture/replay tests and the live
  teaching-upgrade verifier on 2026-08-21.
- [x] Pass the controlled ten-question live acceptance set through chat, TTS
  and synthesized Whisper loopback on 2026-08-21: 10/10 passed, average chat
  2.61 s, maximum chat 11.63 s. The operator-microphone PTT pass remains a
  separate human verification step.

---

# 1. Purpose

This is the master executable checklist for implementing and verifying Project
James across the P4 firmware, physical hardware, Raspberry Pi 5 services,
facial gestures, speech pipeline, integration tests, and release gates. The
current critical path begins with PC recordings and physical P4 microphone
validation, then proceeds through VAD, Pi services, and full-system testing.

This file is the primary day-to-day project document for deciding what to do
next, running tests, recording evidence, and deciding whether a goal is truly
complete. Companion documents explain design details; completion status belongs
here.

It deliberately separates three functions:

| Function | Owner | Work performed |
|---|---|---|
| Voice activity detection (VAD) | P4 | Detect speech start/end; calibrate thresholds and endpoint timing |
| Speech-to-text (STT) | Pi 5 | Convert bounded speech audio into words |
| Speaker verification | Pi 5 | Enroll and compare the operator's voice using a pretrained embedding model |

“VAD training” in informal project discussions means corpus-based calibration
and testing. VAD is not trained to recognize the operator. Speaker recognition
uses enrollment and held-out testing, not a newly trained neural model.

---

# 2. How to Use This Checklist

For every development or test session:

1. Start with the first incomplete item on the critical path unless a blocker is
   recorded beside it.
2. Run the relevant build or validation command before hardware testing.
3. Preserve the evidence named under that goal: logs, reports, WAV metadata,
   counters, screenshots, or protocol traces.
4. Tick an item only after its stated behavior has been observed. A successful
   compile proves the code builds; it does not prove the microphone, LCD, Wi-Fi,
   PSRAM, or timing on physical hardware.
5. Record measured values and the test date in this document or a linked report.
6. Update the goal summary whenever a goal changes state.

All actionable checkboxes from the firmware roadmap, hardware inventory, and
speech-runtime evaluation are consolidated here. Those documents remain the
source for architecture, rationale, specifications, and measured facts, but
they are not separate progress trackers.

Standard clean firmware verification from the repository root:

```powershell
.\tools\build-firmware.ps1 -Clean
Test-Path .\build\project_james.bin
Test-Path .\build\bootloader\bootloader.bin
```

Both `Test-Path` commands must return `True`, and the build must end with
`Project build complete`. See the [firmware build guide](Firmware-Build-Guide.md)
for the sandbox/toolchain explanation and configurable installation paths.

## Latest completed test — P4 BOOT-button voice round trip

The user resumed **G1/G2 physical P4 audio validation** on 2026-08-21. Execute
this bounded sequence before enabling the camera, displays, VAD or wake word:

- [x] Implement onboard ES8311 microphone capture as 16 kHz, 16-bit mono PCM.
- [x] Implement GPIO35 BOOT hold/release PTT with debounce and a 20-second cap.
- [x] Implement authenticated WebSocket uplink to `titanium:8090` and binary
  100 ms `JAM1` chunks.
- [x] Implement binary 16 kHz PCM response playback through ES8311/NS4150B.
- [x] Keep capture and playback half-duplex; ignore the camera.
- [x] Build the firmware successfully with ESP-IDF 6.0.2 on 2026-08-21.
- [x] Place the approved private Wi-Fi password and gateway token in ignored
  `main/james_private_config.h`; never print, document or commit either value.
- [x] Flash COM7 and verify P4 boot, 32 MB PSRAM, ES8311 microphone and speaker
  codec startup, 16 kHz capture and unclipped live microphone levels.
- [x] Configure the P4 for the 2.4 GHz `WETOHOST2.4` SSID.
- [x] Observe the P4 obtain `192.168.8.131`, connect to Titanium, authenticate
  its WebSocket session and report “Gateway ready.”
- [x] Hold BOOT, ask “Who are you and what do you do?”, release BOOT, and hear
  a complete response beginning “My name is James.”
- [x] Record capture, STT/routing, TTS and release-to-audio timing evidence.

The first physical turn captured 2.50 seconds without clipping, transcribed the
question exactly, returned the deterministic James identity answer and played
it successfully. Speaker output was tuned to 95% ES8311 volume and accepted as
substantially improved. The post-migration acceptance turn on 2026-08-22
captured 2.14 seconds, produced the exact transcript and deterministic identity
response 2.29 seconds after release, began speaker output after 3.82 seconds and
finished the complete response 15.02 seconds after release. These P4 timestamps
provide the first physical capture-to-response timing baseline.

The always-on inference-host evaluation remains a later decision:

- [ ] Obtain the NUC IP address, username, OS and authorized SSH access.
- [ ] Inspect the NUC8i5BEH CPU, 16 GB RAM, storage, thermals and network state.
- [ ] Benchmark `qwen3.5:4b`, `phi4-mini`, and `qwen3:4b` without changing the
  Pi's currently deployed fallback.
- [ ] Test time, weather, web search, timer, general knowledge and refusal
  recovery through real gateway tools rather than model guesses.
- [ ] Record warm response start, tokens/second, STT, LLM/tool, TTS and total
  release-to-audio latency in the existing telemetry.
- [ ] Require approximately 2–3 seconds to warm LLM response and approximately
  5 seconds to spoken-response start, plus correct tool use and stable sessions.
- [ ] Decide whether to assign the NUC or specify a dedicated low-power
  replacement from the measured shortfall.
- [ ] Keep **Production NUC**, **Emergency Pi**, **Development Asus**, and
  **Cloud** routes explicit; Asus and Cloud must remain manual opt-ins.

**Host-decision hold:** none of the NUC boxes should be executed or checked
until the user explicitly resumes that separate project-host decision.

---

# 3. Current Baseline

## Prepared

- [x] VAD architecture and endpointing plan documented.
- [x] FreeRTOS task/core allocation documented.
- [x] Private PC recording workspace created under `VED Training`.
- [x] Multi-tone recording plan and manifest templates created.
- [x] WAV format/clipping checker created.
- [x] Corpus, VAD-boundary, and speaker-score evaluation tools created.
- [x] Raw recordings excluded from Git.
- [x] Initial 16 kHz P4 microphone diagnostic source implemented.
- [x] Clean ESP-IDF 6.0.2 firmware build verified on 2026-08-20.
- [x] Bounded 500 ms producer/consumer audio queue implemented.
- [x] Backend-independent endpoint state machine and on-device transition
  self-test implemented.
- [x] Version 1 P4-to-Pi audio/control protocol documented.

## Verified development evidence

| Date | Verification | Result |
|---|---|---|
| 2026-08-20 | `build-firmware.ps1 -Clean` | Passed: application 2131/2131 and bootloader 174/174 |
| 2026-08-20 | Incremental `build-firmware.ps1` | Passed: firmware image regenerated successfully |
| 2026-08-20 | Endpoint synthetic startup test | Compiled into firmware; physical startup log still required |
| 2026-08-21 | Pi gateway ten-question voice acceptance | Passed 10/10 through live routing, TTS and synthesized STT loopback; private evidence retained under `captures/` |
| 2026-08-21 | P4 BOOT-button PTT firmware build | Passed; final documented build is 0xFA9C0 bytes (1,026,496 B) with 88% of the smallest app partition free |
| 2026-08-21 | Pi James identity suite and live query | 49/49 tests passed; deterministic live response identified as James in 1 ms |
| 2026-08-21 | Physical P4 flash and audio startup | COM7 flash verified; ESP32-P4 v1.3 and 32 MB PSRAM passed; ES8311 input/output opened at 16 kHz; microphone showed no clipping |
| 2026-08-21 | Physical P4 Wi-Fi association | Blocked: only `WETOHOST5.8` at 5 GHz is visible; a 2.4 GHz SSID is required |
| 2026-08-21 | Physical P4 gateway connection | Passed on `WETOHOST2.4`; received `192.168.8.131`, authenticated to Titanium and reached BOOT-PTT ready state |
| 2026-08-21 | Physical P4 voice round trip | Passed: 2.50 s BOOT capture, exact STT, deterministic James identity response and completed 16 kHz TTS playback |
| 2026-08-21 | P4 speaker-volume tuning | Passed at ES8311 95%; user reported the result much better; NS4150B remains fixed-gain/enable-only |
| 2026-08-21 | P4 firmware/memory baseline | ~0.98 MiB app; 88% app partition free; connected runtime used 250.4 KiB internal heap and 7.7 KiB PSRAM heap, with 350.9 KiB and 31.10 MiB respectively free |
| 2026-08-22 | Coordinated James Pi/P4 migration | Passed: 49/49 gateway tests; `james-gateway.service` and `piper-james.service` active; legacy services disabled and retained for rollback; P4 flashed with `JAM1` firmware and authenticated from `192.168.8.131` |
| 2026-08-22 | Post-migration physical PTT acceptance | Passed: 2.14 s BOOT capture, exact STT, deterministic James identity response, first audio 3.82 s after release and complete 16 kHz playback |
| 2026-08-22 | Operator audio/response acceptance | Passed: user confirmed both the returned audio and James response were good |

## Not yet proven

- [ ] Real PC corpus has been recorded and validated.
- [x] P4 onboard microphone live capture and signal statistics have been proven.
- [ ] P4 onboard microphone capture has been saved as a valid WAV.
- [ ] ESP-SR has been integrated into the firmware.
- [ ] Automatic P4 speech start/end events have been measured.
- [x] Manual PTT P4-to-Pi audio streaming and returned speech have been proven end to end.
- [ ] Automatic VAD-bounded P4-to-Pi streaming has been proven end to end.
- [ ] Pi 5 STT and speaker enrollment have been benchmarked.

Checked items above mean the planning/tooling exists; they do not claim that
the corresponding runtime feature works on hardware.

---

# 4. Goal Summary and Critical Path

| Goal | Outcome | Depends on | Status |
|---|---|---|---|
| G0 | PC recording workflow proven | None | Ready to start |
| G1 | P4 microphone capture proven | Board audio driver | Live 16 kHz capture proven; WAV evidence pending |
| G2 | Push-to-talk path proven | G1 | Complete — physical capture/STT/James/TTS turn passed |
| G3 | Standalone VAD works offline | G0, ESP-SR dependency | Not started |
| G4 | P4 endpointing preserves full utterances | G1, G3 | In progress — state machine implemented |
| G5 | VAD-bounded audio reaches Pi 5 | G2, G4, Wi-Fi session | Manual stream proven; automatic VAD endpointing next |
| G6 | AFE/VADNet production path evaluated | G4 | Not started |
| G7 | STT and speaker enrollment proven | G0, Pi 5 runtime | Not started |
| G8 | Face states follow the voice pipeline | G4, gesture renderer | Not started |
| G9 | Concurrent system passes soak test | G5–G8 | Not started |

Critical path:

```text
G0 PC corpus -----------------------> G3 offline VAD ---+
                                                       |
G1 P4 capture -> G2 push-to-talk --------------------> G4 endpointing
                                                       |
                                                       v
                                    G5 Pi streaming -> G7 STT/enrollment
                                                       |
                                    G6 AFE/VADNet -----+
                                                       v
                                    G8 face states -> G9 soak test
```

---

# 5. G0 — Prove the PC Recording Workflow

**Goal:** Produce correctly formatted, private recordings that exercise
natural changes in the operator's voice.

- [ ] Install Audacity from the official source.
- [ ] Run `VED Training/tools/setup.ps1`.
- [ ] Select the intended PC microphone and record in mono at 16 kHz.
- [ ] Record room silence, normal speech, and quiet speech test clips.
- [ ] Run `VED Training/tools/check_wav.py` against those clips.
- [ ] Correct sample rate, channel count, encoding, or gain problems.
- [ ] Complete session 001 from `VED Training/plans/recording-plan.csv`.
- [ ] Complete session 002 on another day.
- [ ] Complete session 003 for prompts requiring a third repetition.
- [ ] Populate the private corpus manifest with actual transcripts.
- [ ] Run `validate_corpus.py` with zero format or metadata errors.
- [ ] Back up the private corpus securely without adding it to Git.

**Evidence:** Private validation report plus session notes.

**Exit condition:** Every accepted clip is mono, 16-bit, 16 kHz PCM WAV,
unclipped, correctly named, and assigned to only one data split.

---

# 6. G1 — Prove P4 Onboard Microphone Capture

**Goal:** Capture the actual signal that the deployed system will hear.

- [ ] Confirm ES8311 I2C communication and codec identity/configuration.
- [x] Configure MCLK, BCLK, LRCK, and I2S receive routing in the diagnostic.
- [x] Start with 16 kHz, signed 16-bit, mono application audio.
- [x] Drain fixed 20 ms reads from a dedicated `audio_rx_task` on Core 1.
- [x] Add read-error, peak, RMS, clipping, and stack-watermark counters.
- [ ] Confirm the diagnostic configuration and readings on physical hardware.
- [x] Add a bounded producer/consumer ring before networking or file output.
- [ ] Save a bounded diagnostic WAV without blocking the DMA task.
- [ ] Record P4 silence, normal speech, quiet speech, and loud speech.
- [ ] Validate the P4 WAV files with the same PC checker.
- [ ] Document actual gain, noise floor, DC offset, clipping, and channel map.
- [ ] Run a one-hour capture soak test.

**Evidence:** Valid P4 diagnostic WAVs and health-counter log.

**Exit condition:** No unexplained DMA overruns, watchdog resets, malformed WAVs,
or clipped normal speech during the soak test.

---

# 7. G2 — Prove Push-to-Talk Before Automatic VAD

**Goal:** Isolate microphone, buffering, networking, and STT from VAD tuning.

- [ ] Add an explicit start/stop input or temporary software command.
- [ ] Allocate bounded PCM blocks and a PSRAM history ring.
- [ ] Emit `AUDIO_START`, ordered `AUDIO_CHUNK`, and `AUDIO_END` messages.
- [ ] Receive and save the stream on a PC/Pi test receiver.
- [ ] Compare received PCM length and checksum/counters with the source.
- [ ] Run Pi 5 STT against at least 20 push-to-talk utterances.
- [ ] Record capture-to-first-transcript and end-to-final-transcript latency.
- [ ] Verify clean cancellation, timeout, and reconnect behavior.

**Evidence:** Receiver logs, saved WAVs, STT results, and latency report.

**Exit condition:** Repeated utterances arrive without missing/reordered audio and
produce stable transcripts before automatic detection is introduced.

---

# 8. G3 — Integrate and Test Standalone ESP-SR VAD Offline

**Goal:** Establish a minimal P4-compatible VAD baseline using repeatable audio.

- [ ] Select and pin an exact compatible `espressif/esp-sr` version.
- [ ] Record component/model licensing and redistribution obligations.
- [ ] Compile a host or P4 recorded-file VAD harness.
- [ ] Feed 20 ms frames: 320 samples, 640 bytes, 16 kHz mono PCM.
- [ ] Export detected state and predicted speech boundaries to CSV.
- [ ] Test normal, quiet, loud, fast, slow, tired, and energetic speech.
- [ ] Test silence, fan, keyboard, and representative room noise.
- [ ] Run `VED Training/tools/evaluate_vad.py`.
- [ ] Record results separately by tone, distance, and noise condition.
- [ ] Select an initial VAD mode/threshold without using the final test split.

**Evidence:** Reproducible build/version record, prediction CSV, and evaluation
report.

**Exit condition:** Validation targets in the VAD plan are met or the failure is
documented with a specific mitigation experiment.

---

# 9. G4 — Implement P4 Endpointing and Pre-Roll

**Goal:** Turn frame-level speech/silence states into complete utterances.

- [ ] Implement a backend-independent `james_vad` interface.
- [x] Implement the `james_endpoint` state machine separately from the backend.
- [ ] Add at least 500 ms of bounded pre-roll.
- [x] Add start confirmation and end-of-speech hangover/hysteresis.
- [x] Add maximum utterance and no-speech timeouts.
- [ ] Preserve pre-trigger frames through the VAD cache where supported.
- [x] Add deterministic synthetic VAD sequences to the on-device startup
  self-test.
- [ ] Verify short acknowledgements such as “yes”, “no”, and “pause”.
- [ ] Verify that the first phoneme is not clipped.
- [ ] Recover cleanly after ring overrun or backend failure.
- [ ] Retain push-to-talk as the fallback mode.

**Evidence:** Unit-test output, audio boundary overlays, and failure-injection
results.

**Exit condition:** At least 98% normal-desk detection, 95% across planned tone
conditions, and no more than 150 ms leading clipping on over 99% of accepted
validation clips.

---

# 10. G5 — Stream VAD-Bounded Audio to the Pi 5

**Goal:** Make P4 endpoint events the primary turn boundaries for conversation.

- [ ] Connect endpoint output to the existing bounded uplink path.
- [x] Deploy the isolated authenticated Pi receiver on `titanium:8090`.
- [x] Verify protocol framing, acknowledgements, sequence-gap rejection, and
  complete mocked STT/LLM/TTS turns in automated tests.
- [x] Verify gateway health, capability discovery, Gemini access, Ollama
  fallback availability, and male TTS on the live Pi.
- [x] Implement the authenticated trusted-LAN Wi-Fi/WebSocket client path.
- [x] Prove the trusted Wi-Fi LAN and authenticated WebSocket path on the
  physical P4 (`192.168.8.131` on 2026-08-21).
- [x] Prove one complete manual PTT microphone→STT→James→TTS→speaker turn on
  physical hardware.
- [ ] Send pre-roll before live chunks without duplication.
- [ ] Include stream ID, sequence, format, timestamps, and end reason.
- [ ] Apply explicit backpressure and maximum-buffer policies.
- [ ] Preserve local responsiveness during Wi-Fi stalls.
- [ ] Verify automatic reconnect without replaying stale utterances.
- [ ] Allow Pi-side endpointing only as a secondary diagnostic/safety check.
- [ ] Test 100 consecutive automatic utterances.
- [ ] Measure P4-to-Pi latency and throughput under idle and inference load.
- [x] Record the first complete capture-to-transcript-to-response latency.

**Evidence:** Protocol trace, sequence-gap counter, latency distribution, and
saved receiver audio.

**Exit condition:** No unreported audio gaps, stale replay, or UI stalls during
normal operation and controlled reconnect tests.

---

# 11. G6 — Evaluate AFE/VADNet and Echo Handling

**Goal:** Decide whether ESP-SR AFE/VADNet is the production audio front end.

- [ ] Integrate AFE feed/fetch tasks without violating frame contracts.
- [ ] Compare AFE/VADNet against standalone VAD using the same corpus.
- [ ] Measure Core 1 load, internal RAM, PSRAM, and end-to-end latency.
- [ ] Verify VAD cache/pre-roll handling.
- [ ] Add noise suppression only as a measured experiment.
- [x] Implement initial half-duplex capture gating during James playback.
- [ ] Route playback reference audio before enabling AEC.
- [ ] Evaluate AEC using real speaker-to-microphone coupling.
- [ ] Enable barge-in only after echo-trigger rates meet the target.

**Evidence:** Side-by-side quality/resource benchmark.

**Exit condition:** A production backend is selected from measured speech
recall, false triggers, endpoint latency, CPU, memory, and echo behavior.

---

# 12. G7 — Prove STT and Operator Voice Enrollment on Pi 5

**Goal:** Recognize the words and optionally identify the enrolled operator.

- [x] Record Pi 5 model, CPU, installed RAM, NVMe, and microSD inventory.
- [x] Record free NVMe capacity: approximately 156 GB at deployment audit.
- [ ] Record power-supply specification.
- [x] Verify the 64-bit Pi OS baseline: Debian GNU/Linux 12 (bookworm), AArch64.
- [ ] Verify cooling-fan operation, Ethernet, Wi-Fi, and Bluetooth.
- [ ] Benchmark sustained CPU temperature and idle/inference power.
- [x] Establish common STT, TTS, and Gemini/Ollama provider adapter interfaces.
- [ ] Build fixed STT audio and TTS script evaluation corpora.
- [ ] Select and license-review a Pi 5 STT runtime/model.
- [ ] Benchmark faster-whisper and/or whisper.cpp on the Pi 5.
- [ ] Benchmark STT separately from P4 VAD boundaries.
- [ ] Report WER and command accuracy by tone, distance, and noise.
- [x] Install/verify Ollama and run the initial `llama3.2:3b` versus
  `qwen3:1.7b` spoken-assistant comparison.
- [x] Select `qwen3:1.7b` as the initial local fallback with thinking disabled.
- [ ] Record model-load time, first-token latency, and sustained token speed.
- [x] Deploy an isolated male Piper baseline using
  `en_GB-northern_english_male-medium` on localhost port 5001.
- [ ] Tune/test the synthesized pronunciation and STT recognition of “James”;
  initial loopback preserved the sentence but misheard the opening name.
- [ ] Complete the fixed-corpus local TTS benchmark and test sherpa-onnx as a
  replaceable candidate.
- [x] Verify real Gemini generation and configure `auto` cloud-first/local-
  fallback conversation routing.
- [x] Create and verify the Windows push-to-talk STT/LLM/TTS test application.
- [x] Add Windows/LAN and Pi-side capture, STT, LLM/tool, TTS, and
  release-to-audio timing telemetry.
- [x] Persist privacy-safe rotating gateway telemetry with transcript/response
  text disabled by default and expose aggregate p50/p95 metrics in the tester.
- [x] Add live, persistent personality controls to the Windows tester while
  retaining the trust/severity rules and original male-voice policy.
- [x] Add persistent Whisper vocabulary hints and operator-taught transcript/
  word corrections; enroll the observed `Dateway` → `Gateway` error.
- [x] Add an eight-second grounded-cloud deadline, HTTP-429 circuit breaker,
  Wikipedia-grounded local fallback, pinned Ollama model, and three-turn memory.
- [x] Add explicit private session recording to the tester: input/response WAV,
  transcript stages, answer, route, timing, issue tags, and operator notes under
  the Git-ignored `captures/james-sessions/` directory.
- [x] Add local JSONL-to-CSV telemetry conversion and a local analysis report;
  verify that the installed Whisper response does not expose confidence rather
  than fabricating that metric.
- [x] Default the tester to automatic routing and add persistent, explicitly
  taught Pi-local lessons that are retrieved only for Ollama and never sent to
  Gemini.
- [x] Live-verify a local lesson: Ollama identified itself as James after the
  lesson was stored; no OpenAI/ChatGPT API route exists in the gateway.
- [ ] Record and flag at least 20 representative failed/weak turns, run the
  private session analyzer, and convert recurring unsupported requests into a
  prioritized capability/tool implementation list.
- [x] Add single-flight gateway inference admission control and active/waiting
  queue visibility; retain the earlier 56–66 s contention outliers as baseline
  evidence rather than treating them as current expected performance.
- [x] Add and live-test deterministic named-place current weather via Open-Meteo.
- [x] Add intent-aware Gemini Google Search grounding for current public
  information while avoiding search overhead on ordinary questions.
- [ ] Add deterministic adapters and confirmation policies for timers,
  reminders, device diagnostics/control, source display, prices, sports,
  schedules, and other action-oriented query classes as they enter scope.
- [ ] Configure one cloud STT provider and two cloud TTS candidates for
  measured fallback comparisons.
- [ ] Use LM Studio on the Acer workstation for controlled model comparison.
- [ ] Select and license-review a pretrained speaker-embedding model.
- [ ] Use 12–20 clean enrollment clips from at least two days.
- [ ] Keep validation and test clips out of enrollment.
- [ ] Average and normalize valid enrollment embeddings.
- [ ] Obtain explicit consent before collecting other-speaker trials.
- [ ] Export genuine and impostor similarity scores.
- [ ] Run `evaluate_speaker_scores.py` and select a validation threshold.
- [ ] Run the untouched final test once.
- [ ] Add stronger confirmation for consequential commands.

**Evidence:** STT report, private enrollment-profile metadata, score report, and
selected threshold rationale.

**Exit condition:** Measured performance is acceptable for the chosen use; voice
identity is not the sole authorization for risky actions.

---

# 13. G8 — Connect Voice Events to Facial Gestures

**Goal:** Make the device respond visibly without waiting for the Pi 5.

- [ ] Map armed/no-speech to the attentive or idle face.
- [ ] Map confirmed speech start to `listening`.
- [ ] Map accepted utterance end to `heard`.
- [ ] Map Pi processing to `thinking`.
- [ ] Drive `speaking` from actual playback state/amplitude.
- [ ] Map timeout, offline, and error conditions explicitly.
- [ ] Coalesce obsolete events so display work cannot backlog audio.
- [ ] Verify gesture transitions during 100 voice turns.

**Evidence:** State-event log and recorded demonstration.

**Exit condition:** Visible state matches the audio/conversation state without
causing audio overruns, excessive latency, or stale animation playback.

---

# 14. G9 — Concurrent Acceptance and Soak Test

**Goal:** Prove the complete voice path while the rest of the assistant runs.

- [ ] Run microphone, VAD, Wi-Fi, STT exchange, TTS playback, and three LCDs.
- [ ] Record both-core utilization and worst-case saturation.
- [ ] Record task stack, internal heap, PSRAM, and ring/queue watermarks.
- [ ] Count microphone overruns, playback underruns, dropped frames, and resets.
- [ ] Run quiet-room false-trigger testing for at least one hour.
- [ ] Run a four-hour representative conversation/display soak test.
- [ ] Test Pi restart, AP loss, VAD backend failure, and buffer pressure.
- [ ] Confirm push-to-talk and offline/degraded behavior still work.

**Evidence:** Soak-test report and retained metrics.

**Exit condition:** No watchdog event or unbounded memory growth; zero unexplained
audio gaps; failures recover without rebooting the complete assistant.

---

# 15. Deferred Backlog

These are explicitly outside the first implementation path:

- [ ] wake-word model selection and evaluation;
- [ ] low-power LP-I2S hardware VAD experiment;
- [ ] full-duplex barge-in before AEC is proven;
- [ ] STT model fine-tuning before baseline errors are measured;
- [ ] speaker-model training from scratch;
- [ ] voice-only authorization for sensitive operations;
- [ ] vision-assisted presence or liveness checks;
- [ ] compressed audio transport unless PCM measurements justify it.

## Optional Jetson Nano evaluation

These items become active only if the Jetson is selected for the vision path:

- [ ] Record the exact board/dev-kit revision, CPU/GPU specification, storage,
  JetPack, and Ubuntu versions.
- [ ] Record its power supply, power mode, and cooling arrangement.
- [ ] Verify Ethernet/Wi-Fi, CUDA, OpenCV acceleration, and TensorRT.
- [ ] Benchmark a representative vision model.
- [ ] Measure sustained temperature and power.
- [ ] Compare vision latency against the P4 and Pi 5 alternatives before
  assigning it a permanent architectural role.

---

# 16. Development and Merge Gate

Apply this gate to every implementation work package before merge or release:

- [ ] Work-package acceptance criteria are satisfied.
- [ ] Unit and contract tests pass where present.
- [ ] Lint, type, and static checks pass where configured.
- [ ] No secrets, private recordings, or biometric data are staged.
- [ ] Public interfaces and protocol changes are documented.
- [ ] Independent review is complete.
- [ ] Review findings are resolved or explicitly accepted.
- [ ] Integration-branch tests pass.
- [ ] Relevant physical-hardware testing is complete or clearly marked as
  pending rather than inferred from a successful build.
- [ ] This TODO and affected architecture documents reflect any changed
  assumptions.

---

# 17. Definition of Done

The first Project James production milestone is complete only when all of the
following are true:

- [ ] G0 through G9 exit conditions are met or formally waived with evidence.
- [ ] PC and P4 results are reported separately.
- [ ] VAD, STT, and speaker-verification errors can be attributed separately.
- [ ] All model/component versions and licences are recorded.
- [ ] Raw voice, embeddings, and private test reports remain outside Git.
- [ ] Push-to-talk remains a working fallback.
- [ ] Failure and recovery paths have been tested.
- [ ] The architecture documents match the implemented task/core allocation.
- [ ] Final thresholds come from validation data, not the test split.
- [ ] The public repository contains no biometric recordings or embeddings.
