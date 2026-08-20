# Project TARS — Directory Tree

**Status:** Living document

**Last updated:** 2026-08-20

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
│   ├── P4-Pi-Audio-Protocol.md
│   ├── P4-Voice-Activity-Detection-Plan.md
│   ├── Personality-Distillation.md
│   ├── Speech-and-AI-Runtime-Evaluation.md
│   ├── Project-TODO-and-Verification.md
│   └── VAD-Implementation-TODO.md       Compatibility pointer to master TODO
│
├── images/
│   ├── ESP32 LCD Wiring Reference Schematic.png
│   └── Three-LCD-Face-Mockup.png
│
├── main/
    ├── CMakeLists.txt
    ├── Kconfig.projbuild
    ├── idf_component.yml
    ├── app_main.c
    ├── tars_audio_capture.c
    ├── tars_audio_capture.h
    ├── tars_audio_frame.h
    ├── tars_audio_ring.c
    ├── tars_audio_ring.h
    ├── tars_endpoint.c
    └── tars_endpoint.h
└── tools/
    └── build-firmware.ps1
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
