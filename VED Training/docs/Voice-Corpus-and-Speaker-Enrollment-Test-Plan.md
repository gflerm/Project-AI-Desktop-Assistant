# Project TARS --- Voice Corpus, VAD and Speaker Enrollment Test Plan

**Status:** Version 0.1 --- Test preparation baseline\
**Date:** 2026-08-20\
**Document role:** Recording protocol, VAD/STT evaluation, speaker enrollment,
threshold selection, privacy and acceptance criteria\
**Companion to:** `P4-Voice-Activity-Detection-Plan.md`,
`P4-FreeRTOS-Execution-Plan.md` and `Speech-and-AI-Runtime-Evaluation.md`

---

# 1. Separate the Three Questions

"Recognize my voice in different tones" can mean three different things:

| Question | Technology | Normal execution node |
|---|---|---|
| Is anyone speaking? | VAD/endpoint detection | P4 |
| What words were spoken? | Speech-to-text (STT/ASR) | Pi 5 |
| Is the speaker the enrolled operator? | Speaker verification/identification | Pi 5 |

VAD is speaker-independent. It should detect human speech regardless of who is
speaking and does not need personal voice training. It needs threshold tuning
and representative test recordings.

STT should initially use a pretrained model and be evaluated across the
operator's tones, volumes, speaking rates and distances. Fine-tuning is a later
option only if a measured, repeatable error pattern remains.

Speaker verification should use a pretrained speaker-embedding model. The
operator records an enrollment set, the Pi computes embeddings and averages or
otherwise aggregates them into a local voice profile. This is **enrollment**,
not training a neural network from scratch.

---

# 2. Recommended First System

```text
P4 microphone
   |
   +--> P4 VAD: speech/silence and utterance boundaries
   |
   +--> Pi 5 STT: transcript
   |
   +--> Pi 5 speaker embedding: similarity to enrolled operator
                                   |
                                   +--> operator / unknown + confidence
```

Use the transcript normally even when speaker identity is unknown, subject to
the configured permissions. Speaker verification may personalize low-risk
behavior, but must not be the only authorization factor for destructive,
financial, security-sensitive or privacy-sensitive actions.

Recorded/replayed audio and synthetic speech can fool ordinary speaker
verification systems. Sensitive actions still require explicit confirmation
or a stronger authentication method.

---

# 3. Corpus Privacy

The raw voice corpus is biometric/personal data.

- store recordings under `recordings/`, which is ignored by Git;
- never commit raw voice samples, voice embeddings or operator identifiers;
- use an opaque local speaker ID rather than a full legal name;
- encrypt backups where practical;
- document consent for every non-operator speaker;
- never collect other people's voices without permission;
- make diagnostic retention time-limited;
- allow the operator to delete and re-enroll the voice profile;
- keep model files and generated embeddings out of the public repository.

The repository contains only plans, schemas, prompt lists and evaluation tools.

---

# 4. Recording Format

Record through the actual onboard P4 microphone and final audio path wherever
possible.

```text
container:     WAV
encoding:      signed PCM
sample rate:   16,000 Hz
sample width:  16 bit
channels:      mono
target length: 2--8 seconds per utterance
```

Do not normalize or denoise the master recordings. Evaluation must preserve
the signal the deployed system receives. Derived processed files may be kept
separately and labeled with the processing chain.

Before every session record at least ten seconds of room silence for noise and
false-activation analysis.

---

# 5. Recording Matrix

Collect at least three sessions on different days. Do not record the entire
corpus in one sitting; session variation is essential for realistic speaker
verification.

## 5.1 Speaking styles

```text
normal
quiet
loud but not shouting
slow and deliberate
fast but intelligible
tired / low energy
excited / energetic
questioning intonation
technical dictation
short acknowledgements
```

Do not force unsafe vocal strain. "Different tones" means natural variations,
not imitating extreme voices.

## 5.2 Distances

```text
near:        approximately 0.4 m
normal desk: approximately 0.8--1.0 m
far:         approximately 1.5--2.0 m
```

## 5.3 Acoustic conditions

```text
quiet room
computer fan
keyboard and mouse
3D printer or similar steady machinery
chair/desk movement
open window or distant traffic
TARS speaker playback at low/normal volume
```

Record noise conditions rather than adding artificial noise to every clip.
Synthetic mixtures may supplement but must not replace real recordings.

---

# 6. Dataset Splits

Never evaluate speaker verification using the same recordings used for
enrollment.

| Split | Purpose | Operator target |
|---|---|---:|
| `enrollment` | Build the initial averaged voice embedding | 12--20 clips |
| `validation` | Select similarity threshold and tune VAD | At least 30 clips |
| `test` | Final unbiased evaluation | At least 30 clips |
| `noise` | False VAD activation tests with no speech | At least 30 minutes total |
| `impostor` | Measure false acceptance using consenting non-operator voices | At least 3 speakers, 10+ clips each |

Enrollment should include multiple tones and at least two recording sessions,
but mostly clean near/desk audio. Validation and test sets should contain the
harder distances and noise conditions.

Use different phrases between enrollment and test. This checks text-independent
speaker characteristics rather than memorization of a particular sentence.

---

# 7. Prompt Set

The tracked recording plan is `VED Training/plans/recording-plan.csv`. It includes:

- short yes/no acknowledgements;
- conversational requests;
- technical terms and identifiers;
- numbers and punctuation-like pauses;
- questions;
- longer phrases with internal silence;
- deliberately varied tones and distances;
- noise-only captures.

The transcript must record what was actually spoken, including mistakes or
restarts, not merely the intended prompt.

---

# 8. File and Metadata Layout

```text
VED Training/recordings/voice-corpus/    Git-ignored private data
  session-001/
  session-002/
  session-003/

VED Training/
  README.md
  SETUP-AND-RECORDING-PLAN.md
  plans/
  recording-plan.csv
  templates/
  corpus-manifest.example.csv
  vad-predictions.example.csv
  speaker-scores.example.csv

VED Training/tools/
  setup.ps1
  check_wav.py
  validate_corpus.py
  evaluate_vad.py
  evaluate_speaker_scores.py
```

Each corpus manifest row records:

```text
file
split
speaker_id
session_id
phrase_id
transcript
tone
distance_m
noise
device
consent
speech_start_ms
speech_end_ms
```

Use a waveform editor to mark the first intended speech onset and final speech
offset. For clips containing multiple separated speech regions, create a richer
sidecar annotation later; the initial tools expect one overall speech interval
per utterance.

---

# 9. VAD Test Procedure

## 9.1 Offline test first

1. Capture WAV files through the P4 microphone path.
2. Validate WAV format, duration, clipping and RMS level.
3. Label speech start/end boundaries.
4. Feed the same audio to every candidate VAD backend.
5. Export predicted start/end boundaries.
6. Run `evaluate_vad.py` against the held-out manifest.
7. Compare by tone, distance and noise—not only aggregate accuracy.

## 9.2 Required VAD metrics

```text
speech detection recall
missed utterance count
false activation count/rate
mean and p95 speech-start delay
mean and p95 end-of-speech delay
mean clipped-leading-speech duration
short-utterance detection rate
speaker-playback false activation rate
```

## 9.3 Initial acceptance gates

These gates are provisional and should become stricter after the first corpus:

- no first-word clipping above 150 ms on more than 1% of accepted test clips;
- at least 98% detection for normal desk speech;
- at least 95% detection across all operator tone conditions;
- at least 95% detection for short acknowledgements;
- p95 end-of-speech latency below 1.2 seconds;
- fewer than one false activation per hour in the representative quiet/idle
  noise test;
- zero unhandled crashes, queue overflows or watchdog events.

Do not hide weak far-field/noisy results inside a strong average.

---

# 10. STT Robustness Test

The Pi 5 STT service receives the VAD-bounded utterances. Test transcription
separately from VAD so a missed word can be attributed correctly.

Measure:

```text
word error rate (WER)
exact-match rate for short commands
number/identifier accuracy
time to first partial transcript
time from AUDIO_END to final transcript
failure rate by tone, distance and noise
```

Before considering model fine-tuning:

1. verify microphone gain and clipping;
2. verify VAD pre-roll and endpoints;
3. test a stronger pretrained STT model;
4. add a Project TARS vocabulary/context bias if supported;
5. isolate recurring errors in a held-out corpus.

Fine-tuning on one speaker too early can reduce general robustness and create a
maintenance burden. Prefer model selection, audio quality and vocabulary hints
first.

---

# 11. Speaker Enrollment

## 11.1 Recommended Pi 5 candidate

Use a pretrained speaker-embedding model through sherpa-onnx on the Pi 5.
sherpa-onnx supports speaker embedding extraction, enrollment, search and
verification and runs on Raspberry Pi/ARM Linux.

References:

- [sherpa-onnx speaker identification documentation](https://k2-fsa.github.io/sherpa/onnx/speaker-identification/index.html)
- [official speaker-identification Python example](https://github.com/k2-fsa/sherpa-onnx/blob/master/python-api-examples/speaker-identification.py)
- [speaker embedding C API and manager](https://github.com/k2-fsa/sherpa-onnx/blob/master/sherpa-onnx/c-api/docs/speaker-embedding.dox)

Model selection and licensing must be reviewed separately. A model being
downloadable does not automatically make every commercial use or training-data
condition acceptable.

## 11.2 Enrollment workflow

1. Select 12--20 clean operator clips across at least two days.
2. Exclude clipped, reverberant or incorrectly labeled clips.
3. Require at least roughly 2 seconds of actual speech per clip.
4. Compute one normalized embedding per clip.
5. Inspect within-operator similarities and remove only objectively corrupt
   outliers, recording the reason.
6. Average and re-normalize the remaining enrollment embeddings.
7. Store the enrolled embedding locally on the Pi 5, encrypted where practical.
8. Never use enrollment clips for validation or final testing.

Include normal, quiet, energetic and tired speech in enrollment. Do not include
every extreme noisy condition; the embedding should represent the operator,
not the room noise.

## 11.3 Verification

For each held-out utterance:

```text
audio -> speaker embedding -> cosine similarity to enrolled embedding
```

The score is compared to a threshold:

```text
score >= threshold -> operator candidate
score < threshold  -> unknown speaker
```

Do not copy the example threshold blindly. Select it from validation results.

---

# 12. Threshold Selection

Collect genuine operator scores and consenting impostor scores. Sweep possible
thresholds and calculate:

- false acceptance rate (FAR): impostor accepted as operator;
- false rejection rate (FRR): operator rejected;
- true acceptance rate (TAR);
- equal-error region for comparison;
- condition-specific FAR/FRR by tone, distance and noise.

Choose the operating point from risk:

| Use | Threshold posture |
|---|---|
| Greeting/personalized display | More tolerant |
| Access to private memory | Conservative plus confirmation |
| Tool execution | Conservative plus permission policy |
| Destructive/security-sensitive action | Voice alone never sufficient |

The tracked `evaluate_speaker_scores.py` tool sweeps thresholds over a supplied
score CSV. Keep raw recordings and embeddings private.

---

# 13. Testing Different Tones

The model should recognize the operator across natural voice variation without
requiring one profile per mood.

Report speaker-verification results separately for:

```text
normal
quiet
loud
slow
fast
tired
energetic
questioning
```

If one condition has a high false-rejection rate:

1. check recording level and clipping;
2. check actual voiced duration;
3. inspect room/reverberation mismatch;
4. add a small number of clean examples from that condition to enrollment;
5. rebuild the enrollment average;
6. re-evaluate on untouched validation and test clips.

Never move test clips into enrollment merely to make the reported result look
better. Record new enrollment material and preserve the held-out test set.

---

# 14. Replay, Synthetic Voice and Liveness

Speaker verification is not proof of physical presence. Add defensive layers
for consequential use:

- require a fresh, randomized challenge phrase;
- compare the recognized transcript with the requested phrase;
- detect obvious playback/channel artifacts where practical;
- use camera/presence signals only with explicit privacy policy;
- require touch/PIN/device confirmation for high-risk actions;
- rate-limit repeated failed identity attempts;
- log decisions and confidence without storing raw voice by default.

Voice identity should be a contextual signal, not a universal password.

---

# 15. Session Procedure

For each recording session:

1. record date/time, room, device/enclosure revision and microphone gain;
2. record ten seconds of silence;
3. record normal desk phrases first;
4. record tone variations without vocal strain;
5. record near and far conditions;
6. record real noise conditions;
7. inspect levels before recording the whole session;
8. mark unusable clips rather than silently deleting them;
9. copy metadata into the private corpus manifest;
10. run the validator and preserve its JSON report with the private session.

Aim for peaks below approximately -3 dBFS and avoid any digital clipping. Do
not chase a single RMS value across quiet and loud speech; record the natural
range while ensuring quiet speech remains above the noise floor.

---

# 16. Decisions

## VT001 --- VAD is speaker-independent

**Status:** Architectural fact.

Personal voice enrollment must not be embedded into the P4 VAD backend.

## VT002 --- Speaker verification runs on Pi 5

**Status:** Adopted baseline.

The P4 supplies VAD-bounded audio; Pi 5 computes and compares speaker
embeddings.

## VT003 --- Enroll a pretrained model before considering training

**Status:** Adopted implementation order.

Training a speaker model from scratch is unnecessary and poorly supported by a
single-person corpus.

## VT004 --- Multi-session held-out evaluation is mandatory

**Status:** Test requirement.

Enrollment, validation and test audio must remain separate.

## VT005 --- Voice is not sole authorization for high-risk actions

**Status:** Security requirement.

Replay and synthetic-voice risks require stronger confirmation.

## VT006 --- Raw voice and embeddings remain private

**Status:** Privacy requirement.

They are ignored by Git and must never be pushed to the public repository.

---

# 17. Immediate Next Actions

1. Implement bounded WAV capture from the P4's ES8311 microphone path.
2. Complete recording session 001 using `VED Training/plans/recording-plan.csv`.
3. Validate format, clipping and metadata with `validate_corpus.py`.
4. Label speech boundaries for the validation subset.
5. Export standalone/AFE VAD predictions and run `evaluate_vad.py`.
6. Complete sessions 002 and 003 on different days.
7. Benchmark Pi 5 STT by tone, distance and noise.
8. Select and license-review a sherpa-onnx speaker embedding model.
9. Enroll only the designated enrollment clips.
10. Export held-out similarity scores and select a threshold with
    `evaluate_speaker_scores.py`.
