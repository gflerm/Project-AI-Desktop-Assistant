# Project AI Desktop Companion

> **Living project --- work in progress.**\
> A modular, local-first AI desktop companion combining an ESP32-P4
> interaction node, a Raspberry Pi 5 local-compute node, optional cloud
> AI, speech, touch, display, memory, tools and future vision.

> 🟢 **P4 AUDIO INTEGRATION ACTIVE — 2026-08-21:** The earlier P4 pause is
> superseded for the bounded voice path. The physical P4 now captures speech
> with BOOT push-to-talk, sends it to the Pi gateway and plays James's returned
> voice. Camera and displays remain deferred while timing, reconnect and
> automatic VAD work continue. The
> The user's Asus GPU workstation must remain a development-only resource and
> must never become an automatic production dependency. The proposed always-on
> arrangement is Pi 5 speech/tools/telemetry with local LLM inference on the
> existing Intel NUC8i5BEH, initially comparing `qwen3.5:4b`, `phi4-mini`, and
> `qwen3:4b`. Final host assignment and purchasing remain paused. The user later
> authorized the Pi routing/status implementation and bounded 4B benchmark.

## Project Summary

Project AI Desktop Companion is intended to behave as a persistent
physical AI companion rather than simply a chatbot displayed on a
screen.

The design separates **physical interaction**, **local intelligence**
and **cloud capability** so each can evolve independently.

### Core architecture

``` text
USER
  |
  v
ESP32-P4
display / touch / microphone / speaker
wake/VAD / device state / immediate interaction
  |
  | trusted Wi-Fi LAN
  v
RASPBERRY PI 5 ── 8 GB RAM
local LLM / STT / TTS / memory / embeddings
background services / indexing
  |
  +--------------------+
  |                    |
Wi-Fi / LAN        Wi-Fi / LAN
  |                    |
  +------ CLOUD AI ----+
```

### Design principles

-   **Modular first.** STT, TTS, LLM, vision, memory, display and
    hardware services are replaceable modules behind stable interfaces.
-   **ESP32-P4 = physical companion.** It owns display, touch, audio,
    immediate state and hardware-facing behaviour.
-   **Raspberry Pi 5 = local compute partner.** It provides heavier CPU
    workloads such as local models, speech processing, memory and
    indexing.
-   **Cloud = capability escalation.** Cloud AI is optional and used
    when policy, connectivity and task complexity justify it.
-   **Trusted Wi-Fi = internal service path.** ESP32-P4↔Pi 5 traffic
    uses the trusted LAN; Wi-Fi also serves development, updates and
    cloud access.
-   **Graceful degradation.** Loss of the Pi 5 or internet should reduce
    capability rather than make the companion disappear.
-   **Local-first, not local-only.** Privacy, latency, quality and cost
    determine routing.
-   **Benchmark before buying.** Existing hardware is used first;
    upgrades must solve a measured limitation.
-   **Original identity.** Fictional characters may be studied as design
    references, but the finished personality, voice, visuals and assets
    must be original.
-   **Living specification.** Architecture and component choices may
    change as prototypes are measured.

## Current Hardware Baseline

-   ESP32-P4 --- primary physical/UI node (ESP-IDF / FreeRTOS).
-   Raspberry Pi 5 --- local compute partner (Raspberry Pi OS Lite).
-   7-inch touchscreen --- initial display baseline.
-   Raspberry Pi Touch Display 2 --- preferred official display upgrade
    candidate if testing justifies it (via MIPI-DSI/HDMI bridge on the
    ESP32-P4).
-   NVIDIA Jetson Nano 4 GB --- optional edge/vision experimentation
    node.
-   Acer i7 / 32 GB / NVIDIA development system --- primary engineering
    workstation.
-   Creality K2 Pro + CFS --- enclosure/prototyping fabrication tool.

## Current Software Direction

-   ESP-IDF / FreeRTOS firmware baseline on the ESP32-P4.
-   Raspberry Pi OS Lite 64-bit on the Pi 5 compute node.
-   Minimal graphics stack; no conventional desktop required for
    production kiosk operation.
-   Service-based boot/autostart and recovery.
-   Deployment workflow from the development workstation.
-   `whisper.cpp` as the first local STT baseline on the Pi 5.
-   Piper and sherpa-family TTS candidates on the Pi 5, with licensing
    evaluated separately.
-   Ollama as the first operational Pi 5 local-LLM server candidate.
-   `llama.cpp` as the portable low-level local inference reference.
-   Cloud STT/TTS/LLM providers remain interchangeable through adapters.
-   Multi-agent development is permitted where modules have clear
    ownership, contracts, tests and integration gates.

## Documentation

The following documents are the current design source of truth:

-   [Design Specification](Design-Specification.md) ---
    overall goals, architecture, modules, interfaces and design
    requirements.
-   [Hardware Architecture &
    Inventory](Hardware-Architecture-and-Inventory.md) ---
    hardware inventory, ESP32-P4/Pi 5 roles, display, audio, networking
    and verification plans.
-   [Firmware & Software
    Roadmap](Firmware-Software-Roadmap.md) --- development
    work packages, milestones, modular implementation plan and
    multi-agent workflow.
-   [P4 FreeRTOS Execution Plan](P4-FreeRTOS-Execution-Plan.md) ---
    dual-core task allocation, Wi-Fi/Pi 5 communication, onboard audio,
    PSRAM use, failure handling and staged integration benchmarks.
-   [Directory Tree](Directory-Tree.md) --- living repository map,
    directory ownership, tracked layout, private/generated paths and update
    rules.
-   [Firmware Build Guide](Firmware-Build-Guide.md) --- repeatable ESP-IDF
    build commands, clean-build safety and the sandbox-compatible no-ccache
    wrapper.
-   [P4 Voice Activity Detection
    Plan](P4-Voice-Activity-Detection-Plan.md) --- P4-local VAD,
    endpointing, ESP-SR/VADNet integration, audio buffering, Pi 5 stream
    events, tuning corpus and staged test plan.
-   [Project TODO and Verification](Project-TODO-and-Verification.md) --- the
    single authoritative progress tracker for PC recording, P4 hardware,
    firmware, Pi 5 services, gestures, testing and release evidence. A polished
    [PDF edition](../output/pdf/Project-TODO-and-Verification.pdf) is generated
    from the same Markdown source.
-   [P4-to-Pi Audio Protocol](P4-Pi-Audio-Protocol.md) --- versioned control,
    PCM framing, acknowledgements, backpressure, cancellation and reconnect
    contract for speech and response exchange.
-   [Pi Gateway and Windows Voice
    Test](Pi-Gateway-and-Windows-Voice-Test.md) --- deployed Titanium services,
    Gemini/Ollama routing, male Piper voice, model measurements, and the
    Windows push-to-talk STT/LLM/TTS verification workflow.
-   [VED Training — Start Here](../VED%20Training/README.md) --- beginner PC
    setup, Audacity recording workflow, private folder layout and first WAV
    validation commands.
-   [Voice Corpus, VAD and Speaker Enrollment Test
    Plan](../VED%20Training/docs/Voice-Corpus-and-Speaker-Enrollment-Test-Plan.md) --- private
    recording protocol, multi-tone VAD/STT tests, speaker enrollment,
    threshold selection, privacy and replay-risk controls.
-   [Speech & AI Runtime
    Evaluation](Speech-and-AI-Runtime-Evaluation.md) ---
    STT, TTS, wake/VAD, Ollama, llama.cpp and cloud/local AI evaluation
    and benchmark strategy.
-   [James Teaching and Response Improvement
    Plan](James-Teaching-and-Response-Improvement-Plan.md) --- evidence from the
    recorded sessions and telemetry, failure taxonomy, trustworthy feedback
    schema, regression gates, persistent learning plan and fine-tuning criteria.
-   [Personality Distillation](Personality-Distillation.md)
    --- behavioural/personality design distilled into original reusable
    traits rather than copied character expression.
-   [License & IP Policy](License-and-IP-Policy.md) ---
    ownership, third-party IP, fictional-character boundaries and staged
    private/open-source policy.
-   [Open-Source Licensing
    Strategy](Open-Source-Licensing-Strategy.md) ---
    software licence choice, dependency/model/asset boundaries and
    release compliance.
-   [Licence Selection](LICENSE-SELECTION.md) --- concise record of the
    selected default software licence.

## Licensing

Original Project AI Desktop Companion / Project James software
**explicitly released as open source** uses the **Apache License 2.0**
as the default project software licence.

Unreleased/private project material remains **All Rights Reserved**
unless explicitly licensed otherwise.

Third-party libraries, models, TTS voices, wake-word models, datasets,
fonts, images, audio assets, cloud APIs and hardware/vendor material
retain their own licences and terms.

The project software licence does **not** grant rights to third-party
fictional characters, names, voices, artwork, trademarks or other
protected intellectual property.

See:

-   [Apache License 2.0](../LICENSE)
-   [Licence Scope](../LICENSE-SCOPE.md)
-   [NOTICE](../NOTICE)
-   [License & IP Policy](License-and-IP-Policy.md)
-   [Open-Source Licensing
    Strategy](Open-Source-Licensing-Strategy.md)
-   [Licence Selection](LICENSE-SELECTION.md)

## Project Status

**Work in progress --- specification and prototyping stage.**

Current priorities are to:

1.  measure the physical P4 voice round trip by stage and over repeated turns;
2.  verify reconnect, cancellation and bounded-buffer behaviour;
3.  integrate automatic VAD endpointing while retaining BOOT PTT fallback;
4.  implement stable service/provider interfaces;
5.  add the face/display state loop after the audio path is stable;
6.  continue benchmarking STT, TTS and local/cloud LLM paths;
7.  integrate memory, tools and optional vision incrementally;
8.  keep tests and documentation synchronized with each architectural
    decision.

The project should favour **measured behaviour over specification-sheet
assumptions**.

------------------------------------------------------------------------

**Project AI Desktop Companion**\
*Modular physical interaction. Local intelligence. Cloud capability when
useful.*
