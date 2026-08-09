# Project AI Desktop Companion

> **Living project --- work in progress.**\
> A modular, local-first AI desktop companion combining a Raspberry Pi 5
> interaction node, an Intel NUC local-compute node, optional cloud AI,
> speech, touch, display, memory, tools and future vision.

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
RASPBERRY PI 5
display / touch / microphone / speaker
wake/VAD / device state / immediate interaction
  |
  | dedicated point-to-point Ethernet
  v
INTEL NUC8i5BEH — i5-8259U / 16 GB RAM
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
-   **Pi 5 = physical companion.** It owns display, touch, audio,
    immediate state and hardware-facing behaviour.
-   **NUC = local compute partner.** It provides heavier CPU workloads
    such as local models, speech processing, memory and indexing.
-   **Cloud = capability escalation.** Cloud AI is optional and used
    when policy, connectivity and task complexity justify it.
-   **Dedicated Ethernet = internal backbone.** Pi↔NUC traffic uses a
    private wired link; Wi-Fi remains available for development, updates
    and cloud access.
-   **Graceful degradation.** Loss of the NUC or internet should reduce
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

-   Raspberry Pi 5 --- primary physical/UI node.
-   Intel NUC8i5BEH --- Core i5-8259U, 4 cores / 8 threads, 16 GB RAM;
    primary local compute node.
-   First-generation Raspberry Pi 7-inch DSI touchscreen --- initial
    display baseline.
-   Raspberry Pi Touch Display 2 --- preferred official DSI upgrade
    candidate if testing justifies it.
-   NVIDIA Jetson Nano 4 GB --- optional edge/vision experimentation
    node.
-   Acer i7 / 32 GB / NVIDIA development system --- primary engineering
    workstation.
-   Creality K2 Pro + CFS --- enclosure/prototyping fabrication tool.

## Current Software Direction

-   Raspberry Pi OS Lite 64-bit on the Pi 5.
-   Minimal graphics stack; no conventional desktop required for
    production kiosk operation.
-   Service-based boot/autostart and recovery.
-   SSH/deployment workflow from the development workstation.
-   `whisper.cpp` as the first local STT baseline.
-   Piper and sherpa-family TTS candidates, with licensing evaluated
    separately.
-   Ollama as the first operational NUC local-LLM server candidate.
-   `llama.cpp` as the portable low-level local inference reference.
-   Cloud STT/TTS/LLM providers remain interchangeable through adapters.
-   Multi-agent development is permitted where modules have clear
    ownership, contracts, tests and integration gates.

## Documentation

The following documents are the current design source of truth:

-   [Design Specification](Project-TARS-Design-Specification.md) ---
    overall goals, architecture, modules, interfaces and design
    requirements.
-   [Hardware Architecture &
    Inventory](Project-TARS-Hardware-Architecture-and-Inventory.md) ---
    hardware inventory, Pi/NUC roles, display, audio, networking and
    verification plans.
-   [Firmware & Software
    Roadmap](Project-TARS-Firmware-Software-Roadmap.md) --- development
    work packages, milestones, modular implementation plan and
    multi-agent workflow.
-   [Speech & AI Runtime
    Evaluation](Project-TARS-Speech-and-AI-Runtime-Evaluation.md) ---
    STT, TTS, wake/VAD, Ollama, llama.cpp and cloud/local AI evaluation
    and benchmark strategy.
-   [Personality Distillation](Project-TARS-Personality-Distillation.md)
    --- behavioural/personality design distilled into original reusable
    traits rather than copied character expression.
-   [License & IP Policy](Project-TARS-License-and-IP-Policy.md) ---
    ownership, third-party IP, fictional-character boundaries and staged
    private/open-source policy.
-   [Open-Source Licensing
    Strategy](Project-TARS-Open-Source-Licensing-Strategy.md) ---
    software licence choice, dependency/model/asset boundaries and
    release compliance.
-   [Licence Selection](LICENSE-SELECTION.md) --- concise record of the
    selected default software licence.

## Licensing

Original Project AI Desktop Companion / Project TARS software
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

-   [License & IP Policy](Project-TARS-License-and-IP-Policy.md)
-   [Open-Source Licensing
    Strategy](Project-TARS-Open-Source-Licensing-Strategy.md)
-   [Licence Selection](LICENSE-SELECTION.md)

## Project Status

**Work in progress --- specification and prototyping stage.**

Current priorities are to:

1.  verify the owned hardware configuration;
2.  establish the Pi 5 minimal runtime;
3.  establish the private Pi↔NUC network;
4.  implement stable service/provider interfaces;
5.  build the first display/touch/audio conversational loop;
6.  benchmark STT, TTS and local/cloud LLM paths;
7.  integrate memory, tools and optional vision incrementally;
8.  keep tests and documentation synchronized with each architectural
    decision.

The project should favour **measured behaviour over specification-sheet
assumptions**.

------------------------------------------------------------------------

**Project AI Desktop Companion**\
*Modular physical interaction. Local intelligence. Cloud capability when
useful.*
