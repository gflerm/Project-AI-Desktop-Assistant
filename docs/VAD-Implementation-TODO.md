# Project TARS — VAD Implementation TODO and Goals

**Status:** Version 0.1 — Active implementation checklist

**Date:** 2026-08-20

**Owner:** Project TARS firmware/audio workstream

**Companion documents:** `P4-Voice-Activity-Detection-Plan.md`,
`P4-FreeRTOS-Execution-Plan.md`, and
`../VED Training/README.md`

---

# 1. Purpose

This is the executable checklist for taking Project TARS from PC microphone
recordings to reliable automatic speech detection on the P4 and enrolled-voice
verification on the Raspberry Pi 5.

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

# 2. Current Baseline

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

## Not yet proven

- [ ] Real PC corpus has been recorded and validated.
- [ ] P4 onboard microphone capture has been saved as a valid WAV.
- [ ] ESP-SR has been integrated into the firmware.
- [ ] Automatic P4 speech start/end events have been measured.
- [ ] P4-to-Pi audio streaming has been proven end to end.
- [ ] Pi 5 STT and speaker enrollment have been benchmarked.

Checked items above mean the planning/tooling exists; they do not claim that
the corresponding runtime feature works on hardware.

---

# 3. Goal Summary and Critical Path

| Goal | Outcome | Depends on | Status |
|---|---|---|---|
| G0 | PC recording workflow proven | None | Ready to start |
| G1 | P4 microphone capture proven | Board audio driver | Not started |
| G2 | Push-to-talk path proven | G1 | Not started |
| G3 | Standalone VAD works offline | G0, ESP-SR dependency | Not started |
| G4 | P4 endpointing preserves full utterances | G1, G3 | Not started |
| G5 | VAD-bounded audio reaches Pi 5 | G2, G4, Wi-Fi session | Not started |
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

# 4. G0 — Prove the PC Recording Workflow

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

# 5. G1 — Prove P4 Onboard Microphone Capture

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

# 6. G2 — Prove Push-to-Talk Before Automatic VAD

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

# 7. G3 — Integrate and Test Standalone ESP-SR VAD Offline

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

# 8. G4 — Implement P4 Endpointing and Pre-Roll

**Goal:** Turn frame-level speech/silence states into complete utterances.

- [ ] Implement a backend-independent `tars_vad` interface.
- [x] Implement the `tars_endpoint` state machine separately from the backend.
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

# 9. G5 — Stream VAD-Bounded Audio to the Pi 5

**Goal:** Make P4 endpoint events the primary turn boundaries for conversation.

- [ ] Connect endpoint output to the existing bounded uplink path.
- [ ] Send pre-roll before live chunks without duplication.
- [ ] Include stream ID, sequence, format, timestamps, and end reason.
- [ ] Apply explicit backpressure and maximum-buffer policies.
- [ ] Preserve local responsiveness during Wi-Fi stalls.
- [ ] Verify automatic reconnect without replaying stale utterances.
- [ ] Allow Pi-side endpointing only as a secondary diagnostic/safety check.
- [ ] Test 100 consecutive automatic utterances.

**Evidence:** Protocol trace, sequence-gap counter, latency distribution, and
saved receiver audio.

**Exit condition:** No unreported audio gaps, stale replay, or UI stalls during
normal operation and controlled reconnect tests.

---

# 10. G6 — Evaluate AFE/VADNet and Echo Handling

**Goal:** Decide whether ESP-SR AFE/VADNet is the production audio front end.

- [ ] Integrate AFE feed/fetch tasks without violating frame contracts.
- [ ] Compare AFE/VADNet against standalone VAD using the same corpus.
- [ ] Measure Core 1 load, internal RAM, PSRAM, and end-to-end latency.
- [ ] Verify VAD cache/pre-roll handling.
- [ ] Add noise suppression only as a measured experiment.
- [ ] Begin half-duplex with capture muted or gated during TARS playback.
- [ ] Route playback reference audio before enabling AEC.
- [ ] Evaluate AEC using real speaker-to-microphone coupling.
- [ ] Enable barge-in only after echo-trigger rates meet the target.

**Evidence:** Side-by-side quality/resource benchmark.

**Exit condition:** A production backend is selected from measured speech
recall, false triggers, endpoint latency, CPU, memory, and echo behavior.

---

# 11. G7 — Prove STT and Operator Voice Enrollment on Pi 5

**Goal:** Recognize the words and optionally identify the enrolled operator.

- [ ] Select and license-review a Pi 5 STT runtime/model.
- [ ] Benchmark STT separately from P4 VAD boundaries.
- [ ] Report WER and command accuracy by tone, distance, and noise.
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

# 12. G8 — Connect Voice Events to Facial Gestures

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

# 13. G9 — Concurrent Acceptance and Soak Test

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

# 14. Deferred Backlog

These are explicitly outside the first implementation path:

- [ ] wake-word model selection and evaluation;
- [ ] low-power LP-I2S hardware VAD experiment;
- [ ] full-duplex barge-in before AEC is proven;
- [ ] STT model fine-tuning before baseline errors are measured;
- [ ] speaker-model training from scratch;
- [ ] voice-only authorization for sensitive operations;
- [ ] vision-assisted presence or liveness checks;
- [ ] compressed audio transport unless PCM measurements justify it.

---

# 15. Definition of Done

The VAD/voice implementation is complete for the first production milestone
only when all of the following are true:

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
