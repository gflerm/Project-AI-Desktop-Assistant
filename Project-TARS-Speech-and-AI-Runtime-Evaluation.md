# Project TARS — Speech & AI Runtime Evaluation

**Status:** Version 0.1 — Living Work in Progress  
**Date:** 2026-08-09  
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
| Raspberry Pi 5 | Physical companion | Wake/VAD, light STT/TTS, UI, local fallback |
| Intel NUC i5 / 16 GB | Local compute node | Local LLM, STT/TTS, embeddings, background AI |
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
- appropriate for Pi and NUC benchmarking.

Project TARS fit:

| Platform | Fit |
|---|---|
| Pi 5 | **High** |
| NUC | **High** |
| Jetson Nano | Medium / test CUDA compatibility |
| Acer | High |

Risks / questions:

- model size versus latency on Pi;
- endpoint/VAD integration still required;
- benchmark actual realtime factor rather than relying on third-party numbers.

**Decision:** STT-001 — Include in first benchmark suite.

---

## 5.2 faster-whisper

**Current position:** Strong NUC/workstation candidate.

faster-whisper uses CTranslate2 and its project reports substantial speed
and memory improvements over the original Python Whisper implementation,
including 8-bit inference options.

Project TARS fit:

| Platform | Fit |
|---|---|
| Pi 5 | Medium / not first choice |
| NUC | **High** |
| Jetson Nano | Medium / CUDA-version constraints to test |
| Acer | **High** |

Strengths:

- efficient CPU inference;
- strong Python integration;
- GPU support where CTranslate2/CUDA stack is compatible;
- practical batch/streaming application ecosystem.

**Decision:** STT-002 — Benchmark on NUC and Acer against whisper.cpp.

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
| Pi 5 | **High** |
| NUC | **High** |
| Jetson Nano | Medium-high |
| Acer | High |

Its breadth makes it particularly interesting if a single runtime can
provide multiple offline speech components without tightly coupling them at
the Project TARS interface layer.

**Decision:** STT-003 — Include as a streaming/offline comparison candidate.

---

## 5.4 sherpa-ncnn

**Current position:** Lightweight embedded alternative.

The project supports realtime speech recognition and VAD offline and lists
Raspberry Pi among supported platforms.

Potential role:

- compact Pi-native streaming STT;
- VAD;
- comparison against whisper.cpp for response latency.

**Decision:** STT-004 — Secondary Pi benchmark candidate.

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

**Decision:** STT-005 — Cloud reference candidate.

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

**Decision:** STT-006 — High-priority cloud conversational benchmark.

---

## 6.3 Google / Azure speech services

Both remain mature cloud speech candidates.

They should be treated as provider adapters rather than architectural
dependencies.

**Decision:** STT-007 — Retain as optional future comparison providers.

---

# 7. STT Comparison Matrix

| Candidate | Offline | Streaming | Pi 5 | NUC | Cloud | Initial priority |
|---|---:|---:|---:|---:|---:|---|
| whisper.cpp | Yes | Application-dependent | **High** | **High** | No | **P1** |
| faster-whisper | Yes | Yes/application layer | Medium | **High** | No | P1 NUC |
| sherpa-onnx | Yes | **Yes** | **High** | **High** | No | **P1** |
| sherpa-ncnn | Yes | Yes | **High** | High | No | P2 |
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

Because Project TARS is currently proprietary, Piper should be evaluated as
a **separate executable/service boundary**, and legal/license compatibility
must be reviewed before any distribution.

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

**Decision:** TTS-001 — Benchmark, but preserve process/service isolation
because of licensing.

---

## 8.2 sherpa-onnx TTS

Sherpa-ONNX supports multiple TTS model families including Piper-style,
VITS and Kokoro-related options.

Advantages:

- shared speech runtime;
- offline;
- ARM64 support;
- potentially attractive Pi/NUC deployment.

**Decision:** TTS-002 — High-priority local alternative.

---

## 8.3 Kokoro-family TTS

Kokoro-family models are attractive because relatively small model sizes
can provide high-quality speech.

For Project TARS, evaluate through a supported runtime such as sherpa-onnx
rather than tightly coupling to a one-off implementation.

Questions:

- Pi latency;
- NUC latency;
- voice quality;
- streaming/chunking behaviour;
- licence of runtime and selected model.

**Decision:** TTS-003 — Benchmark primarily on NUC; test Pi if practical.

---

# 9. Cloud TTS Candidates

## 9.1 OpenAI TTS

OpenAI's current speech API supports streaming speech generation and
multiple built-in voices.

Potential role:

- high-quality default cloud voice;
- low-latency streamed speech;
- personality-quality benchmark.

**Decision:** TTS-004 — P1 cloud benchmark.

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

**Decision:** TTS-005 — P1 personality/quality benchmark.

---

## 9.3 Deepgram Aura / cloud TTS

Deepgram provides cloud speech tooling alongside its STT stack.

Potential advantage:

- one vendor can provide low-latency voice-agent speech path;
- natural pairing with Flux STT.

**Decision:** TTS-006 — Include when benchmarking end-to-end cloud voice
latency.

---

## 9.4 Azure neural speech / Google Cloud Speech

Retain as secondary mature providers if primary candidates fail cost,
quality, regional availability or operational requirements.

---

# 10. TTS Comparison Matrix

| Candidate | Offline | Streaming | Pi 5 | NUC | Cloud | Initial priority |
|---|---:|---:|---:|---:|---:|---|
| Piper | Yes | Service-dependent | **High** | **High** | No | **P1 local** |
| sherpa-onnx TTS | Yes | Model-dependent | High | **High** | No | **P1 local** |
| Kokoro via supported runtime | Yes | Runtime-dependent | Candidate | **High** | No | P1/P2 |
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

This prevents expensive STT from running unnecessarily and permits the Pi
to react immediately before any network call.

Candidates for evaluation:

- openWakeWord;
- Silero VAD;
- sherpa-onnx VAD;
- WebRTC VAD;
- deterministic push-to-talk during initial development.

**Initial recommendation:** Do not let wake-word work block M5. Begin with
touch/push-to-talk, then add wake detection after the conversational loop is
stable.

---

# 12. Local LLM Runtime Candidates

## 12.1 Ollama

**Current position:** Preferred operational local-model server for the NUC.

Official Ollama Linux installation supports ARM64 as well as AMD64.

Advantages:

- simple model management;
- service model;
- straightforward local API;
- easy experimentation;
- ARM64 availability;
- good fit for dedicated NUC service.

Project TARS fit:

| Platform | Fit |
|---|---|
| Pi 5 | Good for small models / experimentation |
| NUC | **Excellent operational fit** |
| Jetson Nano | Low priority |
| Acer | Excellent development/testing fit |

The Pi should not run an LLM simply because Ollama can run there. It should
only do so if latency and RAM measurements justify it.

**Decision:** LLM-001 — Preferred first local server on NUC.

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
| Pi 5 | **High** for small quantized models |
| NUC | **High** |
| Jetson Nano | Candidate with CUDA constraints |
| Acer | **High** |

**Decision:** LLM-002 — Benchmark/reference backend and fallback to Ollama.

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

**Decision:** LLM-003 — Preferred interactive model laboratory on Acer.

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

**Decision:** LLM-004 — Evaluate later only if unified local serving solves
a demonstrated operational problem.

---

## 12.5 vLLM

vLLM is oriented toward high-throughput model serving and is more relevant
to substantially stronger compute infrastructure.

For the currently known Project TARS hardware, this complexity is unlikely
to provide sufficient benefit during early development.

**Decision:** LLM-005 — Defer.

---

# 13. Local LLM Runtime Comparison

| Runtime | Pi 5 | NUC i5/16GB | Jetson Nano | Acer/NVIDIA | Headless/API fit | Project priority |
|---|---:|---:|---:|---:|---:|---|
| Ollama | Good | **Excellent** | Low/experimental | Excellent | **Excellent** | **P1** |
| llama.cpp | **Excellent flexibility** | **Excellent** | Candidate | **Excellent** | **Excellent** | **P1** |
| LM Studio | Possible but not preferred | Possible | No | **Excellent** | Good | **P1 dev tool** |
| LocalAI | Good | High | Candidate | High | **Excellent** | P2 |
| vLLM | Low relevance | Low relevance CPU-only | Poor fit | Depends on GPU | Excellent | Deferred |

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
  endpoint: http://nuc:11434
```

Alternative:

```yaml
llm:
  provider: llama_cpp
  model: local-model.gguf
  endpoint: http://nuc:8080
```

Changing the runtime should not change the orchestrator contract.

---

# 15. Initial Recommended Stack

## 15.1 First usable companion

```text
PI 5
|
+-- touch / push-to-talk
+-- VAD candidate
+-- whisper.cpp STT
+-- local display/audio
+-- Piper OR sherpa TTS local fallback
+-- Project TARS orchestrator
        |
        +-- Cloud LLM
        |    Gemini / OpenAI adapter
        |
        +-- NUC
             Ollama / llama.cpp experimental local LLM
```

This minimizes early dependencies.

## 15.2 First quality comparison

Benchmark in parallel:

### STT

```text
whisper.cpp on Pi
whisper.cpp / faster-whisper on NUC
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
Ollama on NUC
llama.cpp on NUC
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
- Raspberry Pi / Linux terminology;
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
wake/VAD -> Pi
STT -> Pi/NUC
LLM -> NUC
TTS -> Pi/NUC
```

Maximum local processing, reduced cloud capability.

## Balanced

```text
wake/VAD -> Pi
STT -> local
LLM -> cloud when complexity requires
TTS -> local or cloud
```

Likely default development target.

## Quality-first

```text
wake/VAD -> Pi
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
NUC LLM unavailable
   -> cloud provider

cloud unavailable
   -> local NUC model

NUC unavailable
   -> Pi deterministic/local capability

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

## P1 — Build/test early

- whisper.cpp;
- sherpa-onnx;
- faster-whisper on NUC;
- OpenAI cloud STT;
- Deepgram Flux;
- Piper as isolated local TTS candidate;
- sherpa-onnx/Kokoro TTS;
- OpenAI cloud TTS;
- Gemini TTS;
- Ollama;
- llama.cpp;
- LM Studio on Acer.

## P2 — Evaluate after first voice loop

- sherpa-ncnn;
- Deepgram cloud TTS;
- Azure speech;
- Google cloud STT;
- LocalAI.

## Deferred

- vLLM on current hardware;
- heavyweight models directly on Pi merely for the sake of being local;
- tightly coupled single-vendor voice/LLM architecture.

---

# 25. Current Decisions

## SAI-001 — Speech and LLM components remain independently replaceable

**Status:** Adopted.

No single STT/TTS/LLM vendor owns the Project TARS architecture.

## SAI-002 — whisper.cpp is the first local STT baseline

**Status:** Adopted for benchmarking.

## SAI-003 — Ollama is the first operational NUC LLM server candidate

**Status:** Adopted for benchmarking.

## SAI-004 — llama.cpp remains the universal low-level local reference

**Status:** Adopted.

## SAI-005 — Local TTS must have a cloud-quality comparison

**Status:** Adopted.

Do not select a local voice purely because it is offline.

## SAI-006 — Perceived end-to-end latency is more important than isolated model speed

**Status:** Adopted.

## SAI-007 — Wake-word implementation must not block the first useful voice loop

**Status:** Adopted.

Use push-to-talk/touch first if needed.

## SAI-008 — GPL and model licences are evaluated before distribution

**Status:** Adopted.

---

# 26. Immediate Next Actions

- [ ] Identify microphone hardware.
- [ ] Establish common STT adapter interface.
- [ ] Establish common TTS adapter interface.
- [ ] Establish common AI provider interface.
- [ ] Build fixed STT test-audio corpus.
- [ ] Build fixed TTS test-script corpus.
- [ ] Install whisper.cpp on Pi 5 after runtime baseline is ready.
- [ ] Install whisper.cpp/faster-whisper on NUC.
- [ ] Test sherpa-onnx on Pi/NUC.
- [ ] Install Ollama on NUC.
- [ ] Install/verify llama.cpp on NUC.
- [ ] Use LM Studio on Acer for model comparison.
- [ ] Configure one real cloud STT provider.
- [ ] Configure two cloud TTS candidates.
- [ ] Record first end-to-end conversational latency.
- [ ] Update this document using measured results.

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
| 0.1 | 2026-08-09 | Initial STT/TTS/local-LLM runtime comparison, compatibility matrices, licensing cautions, benchmark methodology, fallback strategy and recommended first-build stack |
