# Project James — Directory Tree

**Status:** Living document

**Last updated:** 2026-08-21

**Purpose:** A readable map of the repository and the ownership of each major
directory. Update this document whenever a tracked top-level directory or
important subsystem directory is added, renamed, or removed.

---

# Repository Overview

```text
Project-AI-Desktop-Assistant/
├── VED Training/          Private voice-corpus workflow and evaluation tools
├── assets/                Runtime and source media assets
├── docs/                  Architecture, plans, policies, and living references
├── images/                Hardware references and whole-face mockups
├── main/                  ESP32-P4 application firmware
├── output/                Generated, review-ready project artifacts
├── pi_gateway/            Isolated Raspberry Pi 5 voice gateway deployment
├── tools/                 Reproducible developer/build helpers
├── CMakeLists.txt         ESP-IDF project entry point
├── partitions.csv         P4 flash-partition layout
└── sdkconfig.defaults     Tracked ESP-IDF configuration defaults
```

Generated or machine-specific directories such as `.git/`, `build/`,
`managed_components/`, caches, and private recordings are intentionally omitted
from the main tree.

---

# Detailed Tracked Tree

```text
Project-AI-Desktop-Assistant/
├── .gitignore
├── CMakeLists.txt
├── partitions.csv
├── sdkconfig.defaults
│
├── VED Training/
│   ├── README.md
│   ├── SETUP-AND-RECORDING-PLAN.md
│   ├── docs/
│   │   └── Voice-Corpus-and-Speaker-Enrollment-Test-Plan.md
│   ├── plans/
│   │   └── recording-plan.csv
│   ├── templates/
│   │   ├── corpus-manifest.example.csv
│   │   ├── speaker-scores.example.csv
│   │   └── vad-predictions.example.csv
│   └── tools/
│       ├── check_wav.py
│       ├── evaluate_speaker_scores.py
│       ├── evaluate_vad.py
│       ├── setup.ps1
│       └── validate_corpus.py
│
├── assets/
│   └── facial-gestures/
│       ├── README.md
│       ├── manifest.yaml
│       ├── export/
│       │   └── .gitkeep
│       └── source/
│           ├── core-states/
│           │   ├── acting.png
│           │   ├── attentive.png
│           │   ├── boot.png
│           │   ├── error.png
│           │   ├── heard.png
│           │   ├── idle.png
│           │   ├── listening.png
│           │   ├── offline.png
│           │   ├── sleep.png
│           │   ├── speaking.png
│           │   ├── success.png
│           │   ├── thinking.png
│           │   ├── uncertain.png
│           │   └── warning.png
│           └── presentation-modifiers/
│               ├── busy.png
│               ├── cautious.png
│               ├── curious.png
│               ├── focused.png
│               ├── normal.png
│               ├── playful.png
│               └── quiet.png
│
├── docs/
│   ├── README.md
│   ├── summary.md
│   ├── Design-Specification.md
│   ├── Directory-Tree.md
│   ├── Firmware-Build-Guide.md
│   ├── Firmware-Software-Roadmap.md
│   ├── Hardware-Architecture-and-Inventory.md
│   ├── License-and-IP-Policy.md
│   ├── LICENSE-SELECTION.md
│   ├── Open-Source-Licensing-Strategy.md
│   ├── P4-FreeRTOS-Execution-Plan.md
│   ├── Pi-Gateway-and-Windows-Voice-Test.md
│   ├── P4-Pi-Audio-Protocol.md
│   ├── P4-Voice-Activity-Detection-Plan.md
│   ├── Personality-Distillation.md
│   ├── Speech-and-AI-Runtime-Evaluation.md
│   ├── James-Teaching-and-Response-Improvement-Plan.md
│   ├── Project-TODO-and-Verification.md
│   └── VAD-Implementation-TODO.md       Compatibility pointer to master TODO
│
├── images/
│   ├── ESP32 LCD Wiring Reference Schematic.png
│   └── Three-LCD-Face-Mockup.png
│
├── output/
│   └── pdf/
│       └── Project-TODO-and-Verification.pdf
│
├── pi_gateway/
│   ├── README.md
│   ├── requirements.txt
│   ├── scripts/
│   │   ├── benchmark-ollama-model.py
│   │   ├── benchmark-turns.py
│   │   ├── install-pi.sh
│   │   ├── live-turn-test.py
│   │   ├── run-voice-acceptance.py
│   │   ├── smoke-test-pi.sh
│   │   ├── test-routing.py
│   │   ├── verify-adaptive-settings.py
│   │   └── verify-teaching-upgrade.py
│   ├── systemd/
│   │   ├── piper-james.service
│   │   └── james-gateway.service
│   ├── james_gateway/
│   │   ├── __init__.py
│   │   ├── capabilities.py
│   │   ├── config.py
│   │   ├── intents.py
│   │   ├── local_learning.py
│   │   ├── main.py
│   │   ├── network_status.py
│   │   ├── personality.py
│   │   ├── persistent_memory.py
│   │   ├── protocol.py
│   │   ├── search.py
│   │   ├── services.py
│   │   ├── speech_adaptation.py
│   │   ├── system_status.py
│   │   ├── telemetry.py
│   │   └── weather.py
│   └── tests/
│       ├── test_answer_completion.py
│       ├── test_intents.py
│       ├── test_personality.py
│       ├── test_local_learning.py
│       ├── test_persistent_memory.py
│       ├── test_protocol.py
│       ├── test_routing.py
│       ├── test_search.py
│       ├── test_speech_adaptation.py
│       ├── test_system_status.py
│       ├── test_telemetry.py
│       ├── test_weather.py
│       └── test_websocket.py
│
├── tests/
│   ├── test_james_feedback.py
│   ├── test_james_regression_replay.py
│   └── test_james_windows_tester.py
│
├── main/
    ├── CMakeLists.txt
    ├── Kconfig.projbuild
    ├── idf_component.yml
    ├── app_main.c
    ├── james_audio_capture.c
    ├── james_audio_capture.h
    ├── james_audio_frame.h
    ├── james_audio_ring.c
    ├── james_audio_ring.h
    ├── james_endpoint.c
    ├── james_endpoint.h
    ├── james_ptt_client.c
    ├── james_ptt_client.h
    ├── james_wifi.c
    └── james_wifi.h
└── tools/
    ├── analyze_james_sessions.py
    ├── analyze_james_telemetry.py
    ├── build_james_review_queue.py
    ├── build-firmware.ps1
    ├── Launch-James-Tester.ps1
    ├── replay_james_review_queue.py
    ├── james_feedback.py
    ├── james_windows_tester.py
    └── render-project-todo-pdf.py
```

---

# Directory Responsibilities

| Directory | Responsibility | Commit policy |
|---|---|---|
| `VED Training/` | PC recording instructions, prompt plans, schemas, and evaluation tools | Commit plans/tools; never commit recordings or embeddings |
| `assets/` | Source artwork and later device-ready exported media | Commit reviewed assets and manifests |
| `docs/` | System design, architecture decisions, roadmaps, policies, and TODOs | Keep aligned with implemented behavior |
| `images/` | Hardware reference images and complete-device mockups | Commit project-relevant references |
| `main/` | ESP32-P4 firmware component and application configuration | Build and hardware-test before marking goals complete |
| `output/` | Reviewed project artifacts generated from tracked sources | Commit stable deliverables; exclude temporary renders |
| `pi_gateway/` | Authenticated P4/Pi protocol receiver, provider adapters, James personality, Pi services, deployment, and tests | Commit source/configuration; never commit tokens, downloaded models, or runtime state |
| `tools/` | Reproducible project-level build and developer helpers | Commit scripts; keep generated output elsewhere |
| `build/` | Generated ESP-IDF build products | Never commit |
| `managed_components/` | Downloaded ESP-IDF component dependencies | Never commit; versions come from dependency configuration |

---

# Private and Generated Layout

These paths may exist locally but are not part of the tracked tree:

```text
VED Training/
└── recordings/
    └── voice-corpus/
        ├── manifest.csv
        ├── validation-report.json
        ├── session-001/
        ├── session-002/
        └── session-003/

Project-AI-Desktop-Assistant/
├── build/
├── captures/
├── managed_components/
└── **/__pycache__/
```

Voice recordings, voice embeddings, private manifests, and private evaluation
reports are biometric/personal data. They must remain outside Git even if the
repository is public.

---

# Maintenance Rule

Update this document when any of the following occurs:

- a tracked top-level directory is added, renamed, or removed;
- a new firmware subsystem is added under `main/`;
- a new plan or living reference is added under `docs/`;
- an asset family or export layout changes;
- the private voice-training layout changes;
- a generated/private directory gains a new handling rule.

Use the committed tree as the source of truth:

```powershell
git ls-tree -r --name-only HEAD
```

Do not paste the complete contents of `build/` or `managed_components/` into
this document. Summarize those directories by purpose instead.
