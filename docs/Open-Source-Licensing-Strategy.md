# Project TARS --- Open-Source Licensing Strategy

**Status:** Version 0.3 --- Adopted licensing strategy / Living Work in Progress\
**Date:** 2026-08-09\
**Default open-source software licence:** Apache License 2.0\
**Working project name:** Project TARS\
**Important:** This is an engineering/licensing plan, not legal advice.
Obtain qualified IP/legal review before public or commercial release.

------------------------------------------------------------------------

## 1. Decision

For original Project TARS **software source code explicitly selected for
open-source release**, the adopted default licence is:

> **Apache License 2.0 ΓÇö adopted default for original software explicitly released as open source.**

This is preferred over MIT for Project TARS because the project is
intended to be modular, extensible, AI-assisted, potentially
collaborative, and may later have commercial/OEM uses. Apache-2.0
remains permissive while adding an explicit patent licence and
patent-termination mechanism.

The project should **not** attempt to relicense third-party software, AI
models, voices, datasets, fonts, media, APIs, fictional characters,
trademarks, or hardware/vendor materials. Those remain under their own
terms.

------------------------------------------------------------------------

## 2. Why Apache-2.0 Fits Project TARS

Project TARS is designed around replaceable modules and provider
adapters:

``` text
ESP32-P4 runtime
Pi 5 compute services
STT adapters
TTS adapters
LLM providers
vision providers
memory services
UI/display
hardware interfaces
cloud adapters
```

A permissive licence fits this architecture because users can build
proprietary or open extensions without forcing the whole application
into one copyleft licence.

Apache-2.0 provides:

-   permission for commercial and non-commercial use;
-   permission to modify and redistribute;
-   permission to create proprietary products using the licensed code;
-   explicit patent rights from contributors;
-   preservation of copyright/licence notices;
-   a NOTICE mechanism where required;
-   no requirement that downstream applications publish all source code;
-   compatibility with a modular plugin/service architecture.

The explicit patent grant is the main reason to prefer Apache-2.0 over
MIT as the **Project TARS default software licence**.

------------------------------------------------------------------------

## 3. Recommended Licence Map

One licence should not be forced onto every type of project material.

  -----------------------------------------------------------------------
  Material                            Recommended treatment
  ----------------------------------- -----------------------------------
  Original Project TARS software code **Apache-2.0**

  API/protocol definitions and SDK    **Apache-2.0**
  code                                

  Example clients/plugins             **Apache-2.0**

  Build/deployment scripts            **Apache-2.0**

  Configuration schemas               **Apache-2.0**

  Technical documentation             Apache-2.0 initially; CC BY 4.0 may
                                      be considered later for
                                      documentation-only releases

  Original UI assets/icons/sounds     Explicit asset licence required
                                      before public release; do not
                                      assume code licence automatically
                                      covers every asset

  Personality specification           Keep clearly original; decide
                                      explicit documentation/content
                                      licence before public release

  Mechanical/PCB/CAD designs          Evaluate a hardware-specific
                                      licence such as CERN-OHL-P-2.0
                                      before publishing manufacturing
                                      source

  Third-party dependencies            Their own licences

  AI model weights                    Their own model licences

  TTS voices                          Their own voice/dataset licences

  Cloud APIs                          Provider terms

  Product name/logo/trademarks        **Not granted by Apache-2.0**

  Fictional-character IP              Not part of Project TARS licensing
                                      rights
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 4. Relationship to Project IP Policy

`License-and-IP-Policy.md` v0.3 reconciled the project-level
policy: private/unreleased material remains All Rights Reserved, while
original software deliberately selected for public open-source release
defaults to Apache-2.0. Models, voices, assets, hardware designs,
documentation, branding and third-party materials retain separate terms.

That policy-level reconciliation does not automatically license any file.
Before each public open-source publication:

1.  make a deliberate release decision;
2.  identify which files/components are being opened;
3.  confirm ownership/provenance;
4.  mark the released files/components explicitly and remove conflicting
    notices from that release scope;
5.  add the Apache-2.0 `LICENSE` file;
6.  add `NOTICE` and `THIRD_PARTY_NOTICES` where applicable;
7.  tag the first open-source release.

Until a component passes that release-specific audit and is explicitly
marked, it remains under the private/unreleased policy.

------------------------------------------------------------------------

## 5. Third-Party Compatibility Rules

### 5.1 Preferred dependency classes

Prefer dependencies under permissive licences such as:

``` text
Apache-2.0
MIT
BSD-2-Clause
BSD-3-Clause
ISC
```

These are generally easier to combine with an Apache-2.0 Project TARS
core, subject to their notice requirements.

### 5.2 Copyleft dependencies

GPL/AGPL components are **not automatically forbidden**, but they
require deliberate architectural and distribution review.

Rules:

-   do not copy GPL source into Apache-licensed Project TARS code;
-   do not assume a process boundary automatically resolves every
    licensing issue;
-   keep separately installed services genuinely separate where
    appropriate;
-   record exact version and licence;
-   review redistribution/bundling before release;
-   obtain legal advice when the boundary or obligations are uncertain.

LGPL dependencies also require compliance review, especially when
linking or distributing modified libraries.

------------------------------------------------------------------------

## 6. Current AI/Speech Dependency Notes

### whisper.cpp

Current upstream project licence: **MIT**.

Generally suitable as a permissive Project TARS dependency. However,
optional/example integrations may carry additional licences. In
particular, FFmpeg-enabled/example code must be audited rather than
assuming every optional build path has identical licensing.

**Project rule:** pin the build configuration and generate a
dependency/SBOM report.

### faster-whisper

Current upstream project licence: **MIT**.

Suitable as a permissive candidate, while CTranslate2 and transitive
dependencies must still be recorded.

### llama.cpp

Current upstream project licence: **MIT**.

Suitable as a permissive local-inference runtime. **Model weights are
separate** and must be licensed independently.

### Ollama

Current upstream project licence: **MIT**.

Suitable as a local service/runtime candidate. Models downloaded through
Ollama retain their individual model licences.

### sherpa-onnx / related speech runtimes

Treat runtime, bundled libraries, and downloaded speech models as
separate licence records. Do not infer model rights from runtime rights.

### Piper

The active `OHF-Voice/piper1-gpl` project is **GPL-3.0-or-later**.

This is the most obvious current licensing caution in the proposed
stack.

Project TARS should:

-   keep Piper optional;
-   avoid making Piper a mandatory linked component of the
    Apache-licensed core;
-   prefer service/process integration during evaluation;
-   audit the selected voice model separately;
-   consider a more permissively licensed TTS runtime/model combination
    for distributable builds.

The archived older Piper repository was MIT-licensed, but development
has moved and old code should not be selected merely to avoid current
licensing obligations without a technical/security/maintenance review.

### openWakeWord

The code is **Apache-2.0**, but upstream states that its included
pretrained models are **CC BY-NC-SA 4.0**.

That means the code licence fits Project TARS very well, while the
included pretrained wake-word models are not suitable for unrestricted
commercial distribution.

**Project rule:** use a model with verified compatible rights, or
train/obtain a wake-word model whose training data and model licence
permit the intended use.

------------------------------------------------------------------------

## 7. AI Models Are Not Covered by the Project Licence

A local runtime being MIT/Apache licensed does **not** make its models
open under the same licence.

Maintain a model register:

``` text
model name
model version/hash
source
model licence
training/use restrictions where known
commercial-use permission
redistribution permission
attribution requirements
deployment nodes
```

This applies to:

-   Ollama models;
-   GGUF models used by llama.cpp;
-   Whisper model files;
-   TTS voices;
-   wake-word models;
-   embedding models;
-   vision models.

------------------------------------------------------------------------

## 8. Fictional Characters and Original Identity

The project documents use fictional/commercial characters as
design-analysis references, including TARS, Rocky, JARVIS, KITT and
others.

An Apache-2.0 licence **cannot grant rights the Project TARS
contributors do not own**.

Therefore public releases must not include unlicensed:

-   copied dialogue;
-   recognizable character voices;
-   protected character artwork;
-   film/book/game assets;
-   distinctive copyrighted sound effects;
-   logos;
-   character likenesses;
-   copied animation;
-   proprietary product assets.

The final companion should use an original personality, original
language, original visuals and original sounds.

------------------------------------------------------------------------

## 9. Project Name and Trademark Boundary

`Project TARS` should remain a **working/internal project name** until
trademark and branding review is complete.

Apache-2.0 grants copyright and patent permissions described by the
licence; it does **not** grant a general right to use project trademarks
or third-party trademarks.

Before a public/commercial launch:

-   select/evaluate an original public product name;
-   perform trademark clearance;
-   define logo/name usage rules;
-   decide whether a separate trademark policy is required.

------------------------------------------------------------------------

## 10. Contributions

Before accepting broad external contributions, add:

-   `CONTRIBUTING.md`;
-   Developer Certificate of Origin (DCO) sign-off **or** a suitable
    CLA;
-   contribution provenance rules;
-   dependency-introduction rules;
-   AI-assisted contribution disclosure guidance where appropriate.

Recommended initial approach:

> **Apache-2.0 + DCO-style sign-off for ordinary contributions.**

A CLA can be introduced later if dual licensing, commercial relicensing,
or a foundation/company structure makes it necessary.

------------------------------------------------------------------------

## 11. Repository Files for an Open-Source Release

Recommended repository root:

``` text
LICENSE
NOTICE
THIRD_PARTY_NOTICES.md
README.md
CONTRIBUTING.md
SECURITY.md
TRADEMARKS.md          # when public branding exists
DEPENDENCIES.md        # or generated SBOM
MODEL-LICENSES.md
ASSET-LICENSES.md
```

The repository should also generate an SBOM for releases where
practical.

------------------------------------------------------------------------

## 12. Source Headers

Do not add huge licence blocks to every source file.

Recommended SPDX header:

``` text
SPDX-License-Identifier: Apache-2.0
```

Where useful:

``` text
Copyright 2026 Project TARS contributors
SPDX-License-Identifier: Apache-2.0
```

Third-party files should retain their original copyright and licence
notices.

------------------------------------------------------------------------

## 13. Distribution Gate

No public binary, container, OS image or hardware bundle should be
released until the following are checked:

-   [ ] Project-owned files have an explicit licence.
-   [ ] Third-party dependency inventory is complete.
-   [ ] Model licences are recorded.
-   [ ] TTS voice licences are recorded.
-   [ ] Wake-word model rights are recorded.
-   [ ] Fonts/icons/sounds/images are audited.
-   [ ] GPL/LGPL/AGPL components have been reviewed.
-   [ ] Required source/notices are included.
-   [ ] Cloud/API terms have been reviewed for the deployment model.
-   [ ] Secrets have been removed.
-   [ ] Fictional-character assets/imitations have been removed.
-   [ ] Public product name/trademark review is complete.
-   [ ] SBOM is generated.
-   [ ] Legal review is completed before commercial distribution.

------------------------------------------------------------------------

## 14. Recommended Architecture for Licence Isolation

The existing modular architecture helps enormously.

``` text
PROJECT TARS CORE (Apache-2.0)
        |
        +-- STT adapter -------- permissive runtime / cloud API
        |
        +-- TTS adapter -------- permissive runtime preferred
        |                         GPL service optional/reviewed
        |
        +-- LLM adapter -------- Ollama / llama.cpp / cloud
        |
        +-- Wake adapter ------- code + separately licensed model
        |
        +-- Vision adapter ----- runtime + separately licensed model
```

Adapters should communicate through documented contracts. This is good
engineering and makes licence provenance easier to audit.

------------------------------------------------------------------------

## 15. Adopted Open-Source Position

The adopted direction is:

> **Open the reusable engineering platform; keep identity and
> third-party rights cleanly separated.**

A sensible candidate public structure is:

**Candidate software for Apache-2.0 release:**

- provider interfaces;
- ESP32-P4/Pi 5 service protocols;
- hardware abstraction;
- deployment tooling;
- example plugins;
- diagnostics and tests;
- reusable orchestrator components selected through a component-level
  release decision.

**Separately licensed or reviewed:**

- personality and identity content;
- application-specific orchestration/policy that has not been selected
  for release;
- voice and wake-word models;
- original art/audio;
- CAD/hardware design;
- branding.

**Never claimed as Project TARS IP:**

- fictional characters and their assets;
- third-party models and APIs;
- third-party libraries.

The release scope of the orchestrator is therefore **component-specific**,
not categorically open or categorically proprietary.

------------------------------------------------------------------------

## 16. Final Recommendation

### Default software licence

**Apache License 2.0**

### Why not GPL as the project licence?

GPL is excellent when reciprocal source sharing is the project's primary
goal. Project TARS is likely to benefit more from broad integration,
embedded/OEM experimentation, proprietary plugins and cloud/local
provider combinations. Apache-2.0 gives that flexibility while
preserving attribution and providing an explicit patent grant.

### Why not MIT as the project licence?

MIT would also work and many important dependencies already use it.
Apache-2.0 is preferred because Project TARS may grow into a
multi-contributor hardware/software platform and Apache-2.0 provides
clearer patent terms.

### Hardware

If Project TARS later publishes manufacturing-ready CAD/PCB source,
evaluate **CERN-OHL-P-2.0** as a separate permissive hardware licence
rather than assuming the software licence is ideal for hardware design
files.

------------------------------------------------------------------------

## 17. Licensing Decisions

### LIC-001 --- Apache-2.0 is the adopted default software licence

**Status:** Adopted for original software explicitly selected for release.

### LIC-002 --- Third-party components retain their own licences

**Status:** Required.

### LIC-003 --- Models and voices require independent licence records

**Status:** Required.

### LIC-004 --- Strong-copyleft dependencies require explicit review

**Status:** Required.

### LIC-005 --- Project branding and fictional-character rights are outside the software licence

**Status:** Required.

### LIC-006 --- Policy-level reconciliation is complete; each release still requires an audit

**Status:** Reconciled at policy level; release-specific audit remains required.

### LIC-007 --- Hardware may use a separate hardware-specific licence

**Status:** Candidate; decide when CAD/PCB files are ready for release.

------------------------------------------------------------------------

## 18. Version History

  ------------------------------------------------------------------------
  Version                 Date                    Notes
  ----------------------- ----------------------- ------------------------
  0.3                     2026-08-09              Removed stale reconciliation
                                                  wording, aligned adopted
                                                  status and made orchestrator
                                                  release scope explicitly
                                                  component-specific

  0.2                     2026-08-09              Adopted Apache-2.0 as the
                                                  default for original software
                                                  explicitly selected for
                                                  open-source release

  0.1                     2026-08-09              Initial open-source
                                                  licensing strategy;
                                                  recommends Apache-2.0
                                                  for original software,
                                                  establishes
                                                  dependency/model/asset
                                                  boundaries and
                                                  public-release gate

  ------------------------------------------------------------------------
