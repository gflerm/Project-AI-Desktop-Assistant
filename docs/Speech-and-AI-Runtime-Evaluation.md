# Project TARS ΓÇö Speech & AI Runtime Evaluation

**Status:** Version 0.3 ΓÇö Living Work in Progress\
**Date:** 2026-08-18  
**Scope:** Speech-to-text, text-to-speech, wake-word/VAD, local LLM runtimes, cloud speech/AI services, compatibility and benchmark strategy  
**Companion documents:** Project TARS Design Specification, Hardware Architecture & Inventory, Firmware & Software Development Roadmap, Personality Distillation Specification

---

# 1. Purpose

This document evaluates candidate speech and AI runtimes for Project TARS.

The objective is **not** to select one permanent vendor or model. The project should maintain replaceable service interfaces so STT, TTS, wake-word, local LLM and cloud AI components can be benchmarked and replaced independently.

The governing principle is:

> **Choose interfaces first; let measurements choose implementations.**

---

# 2. Evaluation Goals

Each candidate should be judged against:

```text
LATENCY
ACCURACY / QUALITY
CPU USE
GPU / ACCELERATOR USE
RAM USE
STABILITY
ARM64 SUPPORT
X86_64 SUPPORT
OFFLINE CAPABILITY
STREAMING SUPPORT
INTERRUPTIBILITY
API / INTEGRATION QUALITY
MODEL AVAILABILITY
LICENSING
PRIVACY
COST
MAINTENANCE / PROJECT HEALTH
```

A component that wins one category need not become the default for every mode.

---

# 3. Project TARS Service Boundaries

Speech and AI should be isolated behind stable Project TARS interfaces.

Conceptual contracts:

```text
WakeWord.detect(audio)
VAD.process(audio)

SpeechToText.start_stream()
SpeechToText.push_audio()
SpeechToText.finish_turn()

TextToSpeech.synthesize(text)
TextToSpeech.stream(text)
TextToSpeech.cancel()

AIProvider.generate(context)
AIProvider.stream(context)
AIProvider.tool_call(context)
AIProvider.health_check()

VisionProvider.describe(image)
```

The TARS orchestrator should not depend directly on Whisper, Piper, Ollama,
Gemini, OpenAI or another vendor-specific implementation.

---

# 4. Hardware Compatibility Context

| Platform | Primary role | Speech / AI relevance |
|---|---|---|
| ESP32-P4 | Physical companion / edge controller | Orchestration/routing, wake/VAD, UI, audio capture/playback, lightweight local speech; ESP-IDF / FreeRTOS; MB-class memory |
| Raspberry Pi 5 / CPU-first | Primary CPU-first local-compute node | Ollama/llama.cpp, STT/TTS, embeddings, memory and background AI; no CUDA-class assumption |
| NVIDIA Jetson Nano / 4 GB | Optional edge node | CUDA/TensorRT vision; limited modern LLM role |
| Acer i7 / 32 GB / NVIDIA 4 GB | Development workstation | Development, local-model testing, Codex, LM Studio |
| Cloud | High-capability tier | Frontier LLM, premium STT/TTS, multimodal AI |

---

# 5. Speech-to-Text Candidates

## 5.1 whisper.cpp

**Current position:** Preferred first local STT baseline.

Strengths:

- C/C++ implementation;
- broad hardware support through ggml;
- CPU operation;
- quantized models;
- Vulkan acceleration available;
- CUDA builds available;
- ARM64 builds are actively published;
- low dependency overhead;
- appropriate for Pi 5 benchmarking (audio routed from ESP32-P4).

Project TARS fit:

| Platform | Fit |
|---|---|
| ESP32-P4 | Route audio to Pi 5 / cloud |
| Pi 5 | **High** |
| Jetson Nano | Medium / test CUDA compatibility |
| Acer | High |

Risks / questions:

- model size versus latency on Pi 5;
- endpoint/VAD integration still required;
- benchmark actual realtime factor rather than relying on third-party numbers.

**Decision:** STT-001 ΓÇö Include in first benchmark suite.

---

## 5.2 faster-whisper

**Current position:** Strong Pi 5/workstation candidate.

faster-whisper uses CTranslate2 and its project reports substantial speed
and memory improvements over the original Python Whisper implementation,
including 8-bit inference options.

Project TARS fit:

| Platform | Fit |
|---|---|
| ESP32-P4 | Route audio to Pi 5 / cloud |
| Pi 5 | **High** |
| Jetson Nano | Medium / CUDA-version constraints to test |
| Acer | **High** |

Strengths:

- efficient CPU inference;
- strong Python integration;
- GPU support where CTranslate2/CUDA stack is compatible;
- practical batch/streaming application ecosystem.

**Decision:** STT-002 ΓÇö Benchmark on Pi 5 and Acer against whisper.cpp.

---

## 5.3 sherpa-onnx

**Current position:** High-value alternative, especially for streaming speech.

Sherpa-ONNX supports a broad speech stack including:

- streaming and non-streaming speech recognition;
- text-to-speech;
- VAD;
- speaker-related functionality;
- ARM/AArch64 and x86 Linux support;
- multiple model families.

Project TARS fit:

| Platform | Fit |
|---|---|
| ESP32-P4 | Route audio to Pi 5 / cloud |
| Pi 5 | **High** |
| Jetson Nano | Medium-high |
| Acer | High |

Its breadth makes it particularly interesting if a single runtime can
provide multiple offline speech components without tightly coupling them at
the Project TARS interface layer.

**Decision:** STT-003 ΓÇö Include as a streaming/offline comparison candidate.

---

## 5.4 sherpa-ncnn

**Current position:** Lightweight embedded alternative.

The project supports realtime speech recognition and VAD offline and lists
Raspberry Pi among supported platforms.

Potential role:

- compact Pi 5 streaming STT;
- VAD;
- comparison against whisper.cpp for response latency.

**Decision:** STT-004 ΓÇö Secondary Pi 5 benchmark candidate.

---

# 6. Cloud Speech-to-Text Candidates

## 6.1 OpenAI transcription

Current OpenAI speech-to-text APIs support recorded/file transcription and
realtime transcription workflows.

Potential TARS roles:

- high-quality cloud STT;
- benchmark reference against local engines;
- fallback when local STT confidence is poor;
- specialist dictation mode.

Advantages:

- streaming/realtime options;
- simple provider integration;
- strong fit with existing AI-provider architecture.

Trade-offs:

- internet dependency;
- network latency;
- API cost;
- privacy policy considerations.

**Decision:** STT-005 ΓÇö Cloud reference candidate.

---

## 6.2 Deepgram Flux

Flux is explicitly designed for conversational voice agents and includes
contextual turn detection / end-of-turn handling.

This is particularly relevant to Project TARS because conversational
latency is affected not only by transcription speed but by knowing **when
the user has finished speaking**.

Potential advantages:

- realtime transcription;
- turn-taking assistance;
- contextual endpointing;
- lower orchestration burden for conversational speech.

**Decision:** STT-006 ΓÇö High-priority cloud conversational benchmark.

---

## 6.3 Google / Azure speech services

Both remain mature cloud speech candidates.

They should be treated as provider adapters rather than architectural
dependencies.

**Decision:** STT-007 ΓÇö Retain as optional future comparison providers.

---

# 7. STT Comparison Matrix

| Candidate | Offline | Streaming | ESP32-P4 | Pi 5 | Cloud | Initial priority |
|---|---:|---:|---:|---:|---:|---|
| whisper.cpp | Yes | Application-dependent | Routed | **High** | No | **P1** |
| faster-whisper | Yes | Yes/application layer | Routed | **High** | No | P1 Pi 5 |
| sherpa-onnx | Yes | **Yes** | Routed | **High** | No | **P1** |
| sherpa-ncnn | Yes | Yes | Routed | **High** | No | P2 |
| OpenAI STT | No | **Yes** | Client | Client | **Yes** | **P1 cloud** |
| Deepgram Flux | No | **Yes** | Client | Client | **Yes** | **P1 cloud** |
| Google STT | No | Yes | Client | Client | Yes | P2 |
| Azure Speech | No | Yes | Client | Client | Yes | P2 |

---

# 8. Text-to-Speech Candidates

## 8.1 Piper

**Current position:** Preferred local/offline baseline for evaluation.

The original rhasspy/piper repository is archived. Current Piper
development is under `OHF-Voice/piper1-gpl`.

Important licensing note:

**Current Piper code is GPL-3.0.**

Because private/unreleased Project TARS material remains All Rights
Reserved while explicitly released original software defaults to
Apache-2.0, Piper should initially be evaluated as a **separate
executable/service boundary**. GPL and voice-model compatibility must be
reviewed for the exact distribution model before release.

Individual voice-model licences must also be checked separately.

Strengths:

- fast local synthesis;
- suitable for embedded/offline use;
- CLI/web-server/API options;
- broad existing voice ecosystem.

Project TARS role:

- offline speech;
- immediate fallback;
- low-cost local response path.

**Decision:** TTS-001 ΓÇö Benchmark, but preserve process/service isolation
because of licensing.

---

## 8.2 sherpa-onnx TTS

Sherpa-ONNX supports multiple TTS model families including Piper-style,
VITS and Kokoro-related options.

Advantages:

- shared speech runtime;
- offline;
- ARM64 support;
- potentially attractive Pi 5 deployment.

**Decision:** TTS-002 ΓÇö High-priority local alternative.

---

## 8.3 Kokoro-family TTS

Kokoro-family models are attractive because relatively small model sizes
can provide high-quality speech.

For Project TARS, evaluate through a supported runtime such as sherpa-onnx
rather than tightly coupling to a one-off implementation.

Questions:

- Pi 5 latency;
- voice quality;
- streaming/chunking behaviour;
- licence of runtime and selected model.

**Decision:** TTS-003 ΓÇö Benchmark primarily on Pi 5.

---

# 9. Cloud TTS Candidates

## 9.1 OpenAI TTS

OpenAI's current speech API supports streaming speech generation and
multiple built-in voices.

Potential role:

- high-quality default cloud voice;
- low-latency streamed speech;
- personality-quality benchmark.

**Decision:** TTS-004 ΓÇö P1 cloud benchmark.

---

## 9.2 Gemini TTS

Current Gemini TTS supports controllable speech generation, including
natural-language guidance for style, pace, accent and tone.

This is particularly relevant to the Project TARS personality layer because
the personality renderer may control delivery style without embedding those
choices permanently into the core assistant logic.

Potential role:

- expressive cloud personality voice;
- style-controlled responses;
- comparison with OpenAI streaming TTS.

**Decision:** TTS-005 ΓÇö P1 personality/quality benchmark.

---

## 9.3 Deepgram Aura / cloud TTS

Deepgram provides cloud speech tooling alongside its STT stack.

Potential advantage:

- one vendor can provide low-latency voice-agent speech path;
- natural pairing with Flux STT.

**Decision:** TTS-006 ΓÇö Include when benchmarking end-to-end cloud voice
latency.

---

## 9.4 Azure neural speech / Google Cloud Speech

Retain as secondary mature providers if primary candidates fail cost,
quality, regional availability or operational requirements.

---

# 10. TTS Comparison Matrix

| Candidate | Offline | Streaming | ESP32-P4 | Pi 5 | Cloud | Initial priority |
|---|---:|---:|---:|---:|---:|---|
| Piper | Yes | Service-dependent | Client | **High** | No | **P1 local** |
| sherpa-onnx TTS | Yes | Model-dependent | Client | **High** | No | **P1 local** |
| Kokoro via supported runtime | Yes | Runtime-dependent | Client | **High** | No | P1/P2 |
| OpenAI TTS | No | **Yes** | Client | Client | **Yes** | **P1 cloud** |
| Gemini TTS | No | API-driven | Client | Client | **Yes** | **P1 cloud** |
| Deepgram TTS | No | Yes | Client | Client | Yes | P2/P1 voice-agent test |
| Azure / Google Cloud | No | Yes | Client | Client | Yes | P2 |

---

# 11. Wake Word and Voice Activity Detection

Wake word and VAD should remain separate from STT.

Reason:

```text
WAKE / VAD
   |
   v
decide when to send audio
   |
   v
STT
```

This prevents expensive STT from running unnecessarily and permits the ESP32-P4
to react immediately before any network call.

VAD must also remain separate from speaker verification. The P4 VAD is
speaker-independent and uses recorded audio for calibration/evaluation, not
personal voice training. The Pi 5 performs optional operator enrollment and
speaker-embedding comparison after VAD has bounded the utterance. The private
PC/P4 corpus workflow is maintained under `../VED Training/`, and the ordered
implementation checklist is `Project-TODO-and-Verification.md`.

Candidates for evaluation:

- openWakeWord;
- Silero VAD;
- sherpa-onnx VAD;
- WebRTC VAD;
- deterministic push-to-talk during initial development.

**Initial recommendation:** Do not let wake-word work block M5. Begin with
touch/push-to-talk, then add wake detection after the conversational loop is
stable.

**VAD implementation order:** push-to-talk transport, recorded-file standalone
VAD, P4 endpoint/pre-roll state machine, live P4 VAD, AFE/VADNet comparison,
then echo cancellation/barge-in. Apply the same held-out corpus to each backend
so changes are measurable.

---

# 12. Local LLM Runtime Candidates

## 12.1 Ollama

**Current position:** Preferred operational local-model server for the Pi 5.

Official Ollama Linux installation supports ARM64 as well as AMD64.

Advantages:

- simple model management;
- service model;
- straightforward local API;
- easy experimentation;
- ARM64 availability;
- good fit for dedicated Pi 5 service.

Project TARS fit:

| Platform | Fit |
|---|---|
| ESP32-P4 | Not applicable / routes LLM to Pi 5 |
| Pi 5 | **Excellent operational fit** |
| Jetson Nano | Low priority |
| Acer | Excellent development/testing fit |

The Pi 5 should not run an LLM simply because Ollama can run there. It should
only do so if latency and RAM measurements justify it.

**Decision:** LLM-001 ΓÇö Preferred first local server on Pi 5.

---

## 12.2 llama.cpp

**Current position:** Preferred low-level universal local inference backend.

Current llama.cpp provides:

- CPU inference;
- ARM-focused optimizations;
- CUDA;
- Vulkan;
- SYCL and other backends;
- CPU+GPU hybrid inference;
- GGUF model support;
- an OpenAI-compatible API server via `llama serve`.

This makes it especially valuable as a stable lower-level reference even if
Ollama is used operationally.

Project TARS fit:

| Platform | Fit |
|---|---|
| ESP32-P4 | Routes to Pi 5 / cloud |
| Pi 5 | **High** |
| Jetson Nano | Candidate with CUDA constraints |
| Acer | **High** |

**Decision:** LLM-002 ΓÇö Low-level reference and alternative/fallback behind
the same provider interface; Ollama remains the operational default
candidate.

---

## 12.3 LM Studio

LM Studio currently supports local LLM operation on Windows and Linux,
including x64 and ARM64 Linux, and uses llama.cpp for GGUF models.

Its current system guidance recommends 16 GB+ RAM and approximately 4 GB+
dedicated VRAM where applicable.

Project TARS role:

- **development workstation tool**, not primary embedded runtime;
- model discovery;
- quick benchmarks;
- visual model management;
- local API testing.

Current LM Studio APIs include native REST as well as OpenAI-compatible and
Anthropic-compatible endpoints.

**Decision:** LLM-003 ΓÇö Preferred interactive model laboratory on Acer.

---

## 12.4 LocalAI

LocalAI remains a candidate unified self-hosted AI gateway, especially if
Project TARS later benefits from presenting multiple local model types
behind one API.

Potential roles:

- LLM serving;
- embeddings;
- speech;
- image/vision model gateway.

The project should not add it merely to add another abstraction layer.

**Decision:** LLM-004 ΓÇö Evaluate later only if unified local serving solves
a demonstrated operational problem.

---

## 12.5 vLLM

vLLM is oriented toward high-throughput model serving and is more relevant
to substantially stronger compute infrastructure.

For the currently known Project TARS hardware, this complexity is unlikely
to provide sufficient benefit during early development.

**Decision:** LLM-005 ΓÇö Defer.

---

# 13. Local LLM Runtime Comparison

| Runtime | ESP32-P4 | Raspberry Pi 5 (CPU-first) | Jetson Nano | Acer/NVIDIA | Headless/API fit | Project priority |
|---|---:|---:|---:|---:|---:|---|
| Ollama | Not applicable | **Excellent** | Low/experimental | Excellent | **Excellent** | **P1** |
| llama.cpp | Not applicable | **Excellent** | Candidate | **Excellent** | **Excellent** | **P1** |
| LM Studio | Not applicable | Possible | No | **Excellent** | Good | **P1 dev tool** |
| LocalAI | Not applicable | High | Candidate | High | **Excellent** | P2 |
| vLLM | Not applicable | Low relevance CPU-only | Poor fit | Depends on GPU | Excellent | Deferred |

---

# 14. Model-Format Strategy

GGUF should be treated as an important local-model format because of
llama.cpp/Ollama/LM Studio ecosystem compatibility.

Project TARS should avoid storing model selection in application code.

Configuration example:

```yaml
llm:
  provider: ollama
  model: qwen-example
  endpoint: http://pi5:11434
```

Alternative:

```yaml
llm:
  provider: llama_cpp
  model: local-model.gguf
  endpoint: http://pi5:8080
```

Changing the runtime should not change the orchestrator contract.

Internal Pi 5 endpoints are reached over the trusted Wi-Fi LAN ESP32-P4ΓåöPi 5
service path. Services should bind to or be firewalled toward the trusted
LAN. The cloud remains the policy-approved fallback path.

---

# 15. Initial Recommended Stack

## 15.1 First usable companion

```text
ESP32-P4
|
+-- touch / push-to-talk
+-- wake-word / VAD candidate
+-- local display/audio
+-- lightweight local speech functions
+-- Project TARS orchestrator
        |
        +-- Raspberry Pi 5 (trusted Wi-Fi LAN path)
        |    whisper.cpp STT
        |    Piper TTS first isolated local baseline
        |    sherpa-family TTS high-priority alternative
        |    Ollama operational local-LLM candidate
        |    llama.cpp low-level reference/alternative
        |
        +-- Cloud escalation / comparison
             Gemini / OpenAI adapter
```

This minimizes early dependencies.

## 15.2 First quality comparison

Benchmark in parallel:

### STT

```text
whisper.cpp / faster-whisper on Pi 5
sherpa-onnx
OpenAI cloud STT
Deepgram Flux
```

### TTS

```text
Piper
sherpa-onnx / Kokoro candidate
OpenAI TTS
Gemini TTS
Deepgram cloud TTS
```

### LLM

```text
Ollama on Pi 5
llama.cpp on Pi 5
LM Studio on Acer for development comparison
Gemini/OpenAI cloud providers
```

---

# 16. Speech Benchmark Plan

Use the same recorded test set for every STT candidate.

Create samples covering:

- quiet desk speech;
- conversational speech;
- technical vocabulary;
- ESP32-P4 / Raspberry Pi 5 / Linux terminology;
- names used frequently in Project TARS;
- background fan noise;
- speaker playback occurring nearby;
- different microphone distances;
- interrupted/unfinished sentences.

Measure:

```text
word error / practical transcription errors
technical-word accuracy
end-of-turn latency
first partial transcript latency
final transcript latency
CPU %
RAM
power/temperature
false endpoint rate
missed speech
recovery after interruption
```

The most useful STT is not necessarily the one with the lowest academic WER.
For Project TARS, **turn latency and technical vocabulary accuracy matter
heavily**.

---

# 17. TTS Benchmark Plan

Use a fixed response corpus containing:

- one-word acknowledgement;
- short technical answer;
- long explanation;
- numbers;
- filenames;
- code-related terms;
- warnings;
- conversational humour;
- serious/high-severity warning.

Measure:

```text
time to first audio
total synthesis time
streaming capability
CPU %
RAM
voice naturalness
technical pronunciation
interrupt/cancel latency
consistency
offline availability
```

Personality evaluation:

```text
Does it sound calm?
Can humour remain understated?
Does a serious warning sound clear?
Does the voice become tiring after 30 minutes?
```

Voice choice should be tested for long-term desk use, not only impressive
five-second demos.

---

# 18. LLM Runtime Benchmark Plan

For each runtime/model pair:

```text
model size
quantization
RAM at load
RAM during inference
load time
time to first token
tokens/second
prompt processing speed
context size tested
CPU %
GPU %
temperature
power
tool-call reliability
structured-output reliability
crash/recovery behaviour
```

Use the same small Project TARS test suite:

- casual question;
- technical troubleshooting;
- deterministic intent;
- tool selection;
- JSON/schema response;
- memory-retrieval prompt;
- offline fallback;
- ambiguity/uncertainty test.

---

# 19. End-to-End Voice Benchmark

A component benchmark is not enough.

Measure:

```text
USER STOPS SPEAKING
        |
        v
ENDPOINT DETECTED
        |
        v
FINAL STT
        |
        v
ORCHESTRATOR / LLM FIRST TOKEN
        |
        v
TTS FIRST AUDIO
```

Record:

- speech-end to endpoint;
- endpoint to transcript;
- transcript to first LLM token;
- first token to first audio;
- total perceived response latency.

**Perceived conversational latency is the primary voice metric.**

A slightly slower STT model with much better endpointing may produce a
faster-feeling assistant.

---

# 20. Licensing and Proprietary-Project Compatibility

Every runtime and every model must be evaluated separately.

Track:

```text
runtime licence
model licence
voice licence
commercial-use permission
redistribution permission
attribution
copyleft implications
API terms
```

Particular current caution:

**Piper's current active codebase is GPL-3.0.**

Project TARS should preserve a service/process boundary and obtain proper
licensing review before distributing a proprietary product containing or
bundling GPL components.

Do not assume an open-source runtime means every downloadable model/voice
has the same licence.

---

# 21. Privacy Modes

The architecture should eventually support policy profiles.

## Local-first

```text
wake/VAD -> ESP32-P4
STT -> Pi 5
LLM -> Pi 5
TTS -> Pi 5
```

Maximum local processing, reduced cloud capability.

## Balanced

```text
wake/VAD -> ESP32-P4
STT -> local
LLM -> cloud when complexity requires
TTS -> local or cloud
```

Likely default development target.

## Quality-first

```text
wake/VAD -> ESP32-P4
STT -> premium cloud
LLM -> frontier cloud
TTS -> premium cloud
```

Used when connectivity/privacy policy permits and output quality matters
more than local operation.

---

# 22. Fallback Policy

Example:

```text
PRIMARY STT
   |
failure / poor confidence
   v
SECONDARY STT
```

Similarly:

```text
Pi 5 LLM unavailable
   -> cloud provider

cloud unavailable
   -> local Pi 5 model

Pi 5 unavailable
   -> ESP32-P4 deterministic/local capability

cloud TTS unavailable
   -> local TTS
```

Fallback should be explicit and visible in diagnostics.

---

# 23. Benchmark Data Recording

Create a machine-readable results file later, for example:

```text
benchmarks/
  stt-results.csv
  tts-results.csv
  llm-results.csv
  end-to-end-latency.csv
```

This living document should summarize decisions; raw measurements belong in
benchmark files.

---

# 24. Current Shortlist

## P1 ΓÇö Build/test early

- whisper.cpp;
- sherpa-onnx;
- faster-whisper on Pi 5;
- OpenAI cloud STT;
- Deepgram Flux;
- Piper as isolated local TTS candidate;
- sherpa-onnx/Kokoro TTS;
- OpenAI cloud TTS;
- Gemini TTS;
- Ollama;
- llama.cpp;
- LM Studio on Acer.

## P2 ΓÇö Evaluate after first voice loop

- sherpa-ncnn;
- Deepgram cloud TTS;
- Azure speech;
- Google cloud STT;
- LocalAI.

## Deferred

- vLLM on current hardware;
- heavyweight models directly on the ESP32-P4 merely for the sake of being local;
- tightly coupled single-vendor voice/LLM architecture.

---

# 25. Current Decisions

## SAI-001 ΓÇö Speech and LLM components remain independently replaceable

**Status:** Adopted.

No single STT/TTS/LLM vendor owns the Project TARS architecture.

## SAI-002 ΓÇö whisper.cpp is the first local STT baseline

**Status:** Adopted for benchmarking.

## SAI-003 ΓÇö Ollama is the first operational Pi 5 LLM server candidate

**Status:** Adopted for benchmarking.

## SAI-004 ΓÇö llama.cpp remains the universal low-level local reference

**Status:** Adopted.

## SAI-005 ΓÇö Local TTS must have a cloud-quality comparison

**Status:** Adopted.

Do not select a local voice purely because it is offline.

## SAI-006 ΓÇö Perceived end-to-end latency is more important than isolated model speed

**Status:** Adopted.

## SAI-007 ΓÇö Wake-word implementation must not block the first useful voice loop

**Status:** Adopted.

Use push-to-talk/touch first if needed.

## SAI-008 ΓÇö GPL and model licences are evaluated before distribution

**Status:** Adopted.

## SAI-009 ΓÇö Piper is the first isolated local TTS benchmark baseline

**Status:** Adopted for benchmarking.

Sherpa-family TTS remains a high-priority replaceable alternative. Piper
code and each selected voice model must pass the applicable release audit.

## SAI-010 ΓÇö Internal Pi 5 AI services are reached over the trusted Wi-Fi LAN

**Status:** Adopted for prototyping.

Speech and LLM endpoints should be reached over the trusted Wi-Fi LAN service
path by default, with health-aware policy-approved fallback.

---

# 26. Immediate Next Actions

Execution status is centralized in
[`Project-TODO-and-Verification.md`](Project-TODO-and-Verification.md). The former action
list maps there as follows:

- P4 microphone identification, I2S capture, and hardware proof: G1;
- trusted P4-to-Pi transport and end-to-end latency: G5;
- STT/TTS/AI adapters, fixed corpora, Pi runtimes, cloud comparisons, and
  speaker enrollment: G7;
- full concurrent conversational acceptance: G9.

Use this evaluation document for candidate rationale and measured comparison
results. Change task status only in the primary TODO so the project has one
authoritative queue.

---

# 27. Source Notes

Primary/current technical sources consulted for this revision include:

- ggml-org/whisper.cpp project documentation;
- SYSTRAN/faster-whisper project documentation;
- k2-fsa/sherpa-onnx and sherpa-ncnn documentation;
- OHF-Voice/piper1-gpl repository/licence;
- Ollama Linux documentation;
- ggml-org/llama.cpp documentation;
- LM Studio documentation;
- OpenAI speech-to-text and text-to-speech documentation;
- Deepgram Flux documentation;
- Google Gemini TTS documentation.

Because this software ecosystem changes rapidly, compatibility and licensing
must be rechecked before production release.

---

# 28. Version History

| Version | Date | Notes |
|---|---|---|
| 0.3 | 2026-08-18 | ESP32-P4 is the primary companion, Raspberry Pi 5 is the local-compute partner, ESP32-P4ΓåöPi 5 link is trusted Wi-Fi |
| 0.2 | 2026-08-09 | Reconciled exact NUC hardware and CPU-first assumptions, local-first LLM routing, Piper baseline wording, private-network deployment and staged licensing language |
| 0.1 | 2026-08-09 | Initial STT/TTS/local-LLM runtime comparison, compatibility matrices, licensing cautions, benchmark methodology, fallback strategy and recommended first-build stack |
