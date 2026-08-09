# Project TARS --- License & Intellectual Property Policy

**Status:** Version 0.4 — Living Work in Progress\
**Date:** 2026-08-09\
**License model:** Staged / component-specific — private development now; Apache-2.0 default for original software selected for open-source release\
**Applies to:** Project TARS source code, documentation, specifications,
original visual assets, original sound assets, configuration,
interaction designs, prompts, workflows, hardware designs and other
original project materials, except where expressly stated otherwise.

> **Important:** This document is a project licensing template and IP
> policy, not legal advice. Before commercial release, public
> distribution, investment, licensing to third parties, or registration
> of intellectual property, it should be reviewed by a qualified
> intellectual-property attorney in the relevant jurisdiction.

------------------------------------------------------------------------

# Document Status — Living Work in Progress

This policy is a **living project document** and will evolve as Project TARS moves from private research and prototyping toward any future collaboration, distribution or commercial release.

The licensing model is now deliberately **staged and component-specific**.

During private development, unreleased original Project TARS materials remain **All Rights Reserved** unless explicitly marked otherwise.

For original Project TARS **software code selected for public open-source release**, the adopted default licence is **Apache License 2.0**. A component becomes Apache-2.0 licensed only when its repository/file/release is explicitly marked accordingly and the required licence notices are present.

Documentation, personality content, visual/audio assets, hardware design files, models, voices, datasets, branding and third-party materials are **not automatically relicensed** merely because Project TARS software uses Apache-2.0.

This document is not a substitute for professional legal advice and should be reviewed before external commercial use.

---

# Licensing Goal

The goal of this policy is to preserve ownership and control of unreleased Project TARS work while development is underway, clearly separate third-party intellectual property from original project material, and support a deliberate open-source release of reusable Project TARS software under Apache-2.0 without accidentally relicensing unrelated assets, models, documentation, hardware designs, branding or third-party material.

The licensing policy should protect the project **without preventing legitimate use of separately licensed dependencies, APIs and tools under their own terms**.

---

# 1. Copyright Notice

**Copyright © 2026 Project TARS rights holder. All Rights Reserved.**

Unless a specific file, component or release states otherwise, unreleased
original Project TARS materials remain proprietary and protected by
applicable copyright and other intellectual-property laws.

Original Project TARS software explicitly released under Apache-2.0 is
licensed under the Apache License, Version 2.0. The Apache licence applies
only to material expressly identified as covered by it.

For material not expressly released under Apache-2.0 or another stated
licence, no licence is granted except by explicit written permission from
the Project TARS rights holder.

------------------------------------------------------------------------

# 2. Unreleased / Proprietary Material — No Permission to Copy or Redistribute

For Project TARS material that has **not** been explicitly released under Apache-2.0 or another stated licence, without prior written permission from the rights holder you may not:

-   copy or reproduce Project TARS materials;
-   redistribute the source code or documentation;
-   publish substantial portions of the project;
-   modify and redistribute the project or derivative versions;
-   sell, sublicense, rent or commercially exploit Project TARS;
-   incorporate proprietary Project TARS materials into another product;
-   make Project TARS available as a hosted service;
-   remove copyright, attribution, license or ownership notices;
-   represent a modified or copied implementation as an official Project
    TARS product;
-   use original Project TARS visual, audio, personality, branding or
    interaction assets in another product.

Possession of a copy does not transfer ownership or grant a license.

------------------------------------------------------------------------

# 2A. Apache-2.0 Open-Source Software Release Policy

The project has selected **Apache License 2.0** as the default licence for
original Project TARS software that is deliberately released as open source.

This includes suitable project-owned software such as:

- orchestrator/framework code;
- provider and hardware abstraction interfaces;
- Pi/NUC service protocols and implementations;
- deployment/build tooling;
- diagnostics and tests;
- example plugins and clients;
- SDK/API code.

Apache-2.0 does **not** automatically apply to:

- third-party dependencies;
- AI/model weights;
- TTS voices or datasets;
- wake-word models;
- visual/audio assets;
- personality content;
- CAD/PCB/manufacturing files;
- product names, logos or trademarks;
- fictional-character intellectual property.

The authoritative rule is therefore:

> **Private/unreleased material stays All Rights Reserved; original software
> explicitly released as open source uses Apache-2.0; everything else keeps
> its expressly stated licence or rights status.**

The companion `Open-Source-Licensing-Strategy.md` defines the
engineering process, dependency boundaries and release gate for this model.

------------------------------------------------------------------------

# 3. Private Evaluation

A person who has lawfully received a copy directly from the rights
holder may inspect or evaluate that copy privately only to the extent
expressly authorised by the rights holder.

Private access does not grant permission to redistribute, publish,
sublicense or commercialise the project.

------------------------------------------------------------------------

# 4. Contributions

No outside contribution automatically creates a right to distribute or
control Project TARS.

Before accepting substantial third-party contributions, the project
should establish a written Contributor License Agreement or
copyright-assignment policy.

Until such a policy exists, third-party code should not be merged into
the proprietary codebase unless its ownership and licensing terms are
clear and compatible with this project.

------------------------------------------------------------------------

# 5. Third-Party Software

Project TARS may depend on open-source, commercial or otherwise
separately licensed software.

Those components remain subject to their own licenses.

This Project TARS license does **not** override third-party licenses and
does not claim ownership of third-party software.

A dependency inventory should be maintained containing, where
applicable:

``` text
Component
Version
Source
License
Copyright notice
Modification status
Distribution obligations
```

Particular care should be taken before introducing strong-copyleft
dependencies or assets whose terms could conflict with the intended
proprietary distribution model.

------------------------------------------------------------------------

# 6. AI Models, APIs and Services

Project TARS may interface with third-party AI models, APIs or hosted
services.

Examples may include services supplied by OpenAI, Google or other
providers.

Use of those services remains governed by the applicable provider terms,
policies and licenses.

Project TARS does not claim ownership of third-party models, APIs or
service infrastructure merely because an adapter or integration exists
in the project.

The architecture should remain provider-independent wherever practical.

------------------------------------------------------------------------

# 7. Fictional Characters and Inspiration

Project TARS has used fictional and commercial characters as
**design-analysis references** during research.

References may include concepts inspired by characters or products such
as:

-   TARS from *Interstellar*;
-   EMO by LivingAI;
-   Rocky from *Project Hail Mary*;
-   JARVIS;
-   Data;
-   R2-D2;
-   the Emergency Medical Hologram;
-   K-2SO;
-   KITT;
-   WALL-E;
-   Baymax;
-   C-3PO;
-   Marvin;
-   GLaDOS;
-   HAL 9000.

These references identify sources of high-level design inspiration only.

Project TARS does **not** claim ownership of those characters, names,
films, books, television programmes, games, products, trademarks,
dialogue, voices, artwork, sounds, designs or associated intellectual
property.

Their respective rights remain with their respective owners.

------------------------------------------------------------------------

# 8. No Character Reproduction

The finished Project TARS product should develop an original identity.

Unless separately licensed from the appropriate rights holder, the
project should not intentionally reproduce:

-   copyrighted character dialogue;
-   recognizable voice performances;
-   character-specific catchphrases;
-   copyrighted artwork;
-   recognizable fictional robot sounds;
-   distinctive character animation;
-   logos;
-   protected visual designs;
-   fictional character likenesses;
-   proprietary product assets.

Design principles such as competence, concise communication, curiosity,
uncertainty handling, attention management or calm escalation should be
implemented as **original Project TARS behaviours**, not as character
impersonation.

------------------------------------------------------------------------

# 9. Project Name and Branding

**Project TARS is currently a working project name.**

Because "TARS" is strongly associated with the fictional robot in
*Interstellar*, this working name should **not automatically be assumed
safe for commercial branding**.

Before public or commercial launch:

1.  select and evaluate an original product name;
2.  conduct appropriate trademark searches;
3.  check relevant product/service classes and jurisdictions;
4.  obtain legal advice where appropriate;
5.  register important marks where commercially justified.

The internal codename may later differ from the public product name.

------------------------------------------------------------------------

# 10. Original Personality

The Project TARS Personality Distillation Specification is intended to
create an original companion identity.

The project should preserve the following distinction:

``` text
INSPIRATION
    ↓
abstract design principle
    ↓
Project TARS implementation
    ↓
original behaviour / language / visuals / sounds
```

It should avoid:

``` text
existing character
    ↓
direct imitation
    ↓
copied dialogue / voice / appearance / branding
```

The project should maintain records of its original design process where
practical.

------------------------------------------------------------------------

# 11. Original Assets

Original assets developed specifically for Project TARS may include:

-   interface graphics;
-   animations;
-   icons;
-   sound effects;
-   notification sounds;
-   voice-direction specifications;
-   personality specifications;
-   prompts;
-   documentation;
-   diagrams;
-   hardware enclosure designs;
-   PCB designs;
-   source code;
-   configuration schemas.

Where practical, source files and creation dates should be retained.

Third-party assets must be recorded separately with their licensing
information.

------------------------------------------------------------------------

# 12. AI-Assisted Development

AI systems may be used to assist with:

-   coding;
-   documentation;
-   research;
-   design exploration;
-   testing;
-   refactoring;
-   brainstorming;
-   asset ideation.

AI-assisted output should be reviewed before inclusion in the project.

Where provenance or ownership is important, maintain reasonable records
showing human selection, modification, integration and authorship
decisions.

Do not intentionally request AI systems to reproduce protected
third-party assets for incorporation into the finished product.

------------------------------------------------------------------------

# 13. Repository Policy

Until a deliberate release decision is made, the primary Project TARS
repository should be treated as **private**.

Recommended repository controls:

-   private repository visibility;
-   multi-factor authentication;
-   restricted collaborator access;
-   branch protection;
-   protected release credentials;
-   no API secrets committed to source control;
-   `.env` and credential files excluded;
-   license file present at repository root;
-   copyright headers where appropriate;
-   third-party notices maintained;
-   backups retained.

------------------------------------------------------------------------

# 14. Secrets and Credentials

API keys, passwords, private keys, tokens and other credentials are
**not project source code** and must never be intentionally distributed
with Project TARS.

Configuration examples should use placeholders such as:

``` text
OPENAI_API_KEY=<your-key>
GEMINI_API_KEY=<your-key>
```

Real credentials should use secure environment variables or an
appropriate secret store.

------------------------------------------------------------------------

# 15. Hardware Designs

Original Project TARS mechanical, enclosure, PCB and other hardware
design files are also proprietary unless specifically released under a
separate license.

Possession of STL, STEP, Gerber, KiCad or similar files does not grant
permission to manufacture products for redistribution or sale.

A separate hardware license may be created later if hardware designs are
intentionally opened.

------------------------------------------------------------------------

# 16. Documentation

Project documentation is proprietary unless otherwise marked.

This includes, among other materials:

-   Project TARS Design Specification;
-   Project TARS Personality Distillation Specification;
-   architecture documents;
-   build instructions;
-   research notes;
-   diagrams;
-   test plans;
-   implementation notes.

Short quotations may be permitted where required by applicable law, but
this document does not grant permission to reproduce or republish
substantial portions.

------------------------------------------------------------------------

# 17. Commercial Licensing

The rights holder may later choose to offer separate licences,
including:

-   individual developer licences;
-   commercial licences;
-   OEM licences;
-   research licences;
-   educational licences;
-   source licences;
-   hardware manufacturing licences.

Any such licence must be granted separately in writing.

The existence of a future commercial licensing programme does not create
rights under the present policy.

------------------------------------------------------------------------

# 18. No Warranty

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, PROJECT TARS
MATERIALS PROVIDED FOR EVALUATION OR DEVELOPMENT ARE PROVIDED "AS IS",
WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED.

THE RIGHTS HOLDER DOES NOT WARRANT THAT THE SOFTWARE IS ERROR-FREE,
SECURE, FIT FOR A PARTICULAR PURPOSE, OR SUITABLE FOR SAFETY-CRITICAL
USE.

------------------------------------------------------------------------

# 19. Limitation of Liability

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THE RIGHTS HOLDER
SHALL NOT BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL OR
EXEMPLARY DAMAGES ARISING FROM UNAUTHORISED OR AUTHORISED USE OF PROJECT
TARS MATERIALS, EXCEPT WHERE SUCH LIMITATION IS PROHIBITED BY LAW.

Jurisdiction-specific legal review is required before relying on this
clause commercially.

------------------------------------------------------------------------

# 20. Permissions

Requests to copy, distribute, license, manufacture, integrate or
commercially use proprietary Project TARS materials require explicit
permission from the rights holder.

A formal contact address should be inserted here before external
distribution:

``` text
Licensing contact: [TO BE DEFINED]
```

------------------------------------------------------------------------

# 21. Adopted Release Strategy

The adopted policy is:

> **Private while developing; Apache-2.0 for original software deliberately
> opened; separate licensing for assets, hardware, models and identity.**

The intended structure is component-specific:

``` text
KEEP PROPRIETARY
        |
        +-- commercial binary distribution
        +-- paid source licence
        +-- OEM licence

OPEN SELECTED SOFTWARE COMPONENTS UNDER APACHE-2.0
        |
        +-- SDK
        +-- protocol
        +-- plugins
        +-- hardware interface
        +-- example clients
        +-- reusable orchestrator components explicitly selected for release

KEEP SEPARATELY LICENSED OR PRIVATE UNLESS EXPLICITLY RELEASED
        |
        +-- personality engine
        +-- application-specific orchestration/policy
        +-- original assets
        +-- commercial integrations
```

Opening one component does not change the licensing of the rest of the
project. The Apache-2.0 selection is the default for original software
chosen for release, not a blanket relicensing of every Project TARS asset.
The orchestrator is not categorically open or proprietary: each reusable
component requires an explicit release-scope decision and licence marking.

------------------------------------------------------------------------

# 22. Recommended IP Checklist Before Public Release

-   [ ] Choose an original commercial product name.
-   [ ] Perform trademark clearance.
-   [ ] Obtain professional IP/legal review.
-   [ ] Confirm ownership of all accepted contributions.
-   [ ] Audit third-party dependencies and licences.
-   [ ] Audit images, sounds, fonts, voices and other assets.
-   [ ] Remove fictional-character imitation from production assets.
-   [ ] Maintain a `THIRD_PARTY_NOTICES` file.
-   [ ] Maintain a software bill of materials where appropriate.
-   [ ] Confirm AI/API provider terms for the intended deployment.
-   [ ] Confirm privacy/data-processing requirements.
-   [ ] Remove secrets from repository history.
-   [ ] Decide whether patents, registered designs or trademarks are
    appropriate.
-   [ ] Replace the working Project TARS branding if legal review
    recommends it.
-   [ ] Create commercial end-user terms before distribution.

------------------------------------------------------------------------

# 23. Practical Development Rule

Until the licensing strategy changes, contributors and collaborators
should work from this assumption:

> **Treat Project TARS as private during development. Only files/components
> deliberately released with an explicit Apache-2.0 or other licence may be
> copied, modified or redistributed under that licence.**

------------------------------------------------------------------------

# 24. Relationship to Other Project Documents

This document governs licensing/IP policy for original Project TARS
material.

Companion documents currently include:

-   `Design-Specification.md`
-   `Personality-Distillation.md`
-   `Open-Source-Licensing-Strategy.md`
-   `LICENSE-SELECTION.md`

Technical or personality specifications do not grant permission to use
the project.

If a future component contains its own explicit licence, that
component's licence should govern that component only.

------------------------------------------------------------------------

# 25. Version History

  ---------------------------------------------------------------------------------
  Version                 Date                    Notes
  ----------------------- ----------------------- ---------------------------------
  0.4                     2026-08-09              Clarified that orchestrator
                                                  release scope is decided
                                                  component by component

  0.3                     2026-08-09              Reconciled proprietary
                                                  development policy with
                                                  adopted Apache-2.0 default
                                                  for explicitly released
                                                  original software

  0.1                     2026-08-09              Initial
                                                  proprietary/all-rights-reserved
                                                  project licensing and IP policy

  ---------------------------------------------------------------------------------
