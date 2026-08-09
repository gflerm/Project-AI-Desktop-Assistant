# Project TARS --- Firmware & Software Development Roadmap

**Status:** Version 0.3 --- Living Work in Progress\
**Date:** 2026-08-09\
**Scope:** Firmware/software only; mechanical enclosure and hardware
construction are tracked separately\
**Companion documents:** Project TARS Design Specification, Personality
Distillation Specification, Hardware Architecture & Inventory, License &
IP Policy

------------------------------------------------------------------------

# 1. Purpose

This document turns the Project TARS specifications into a **modular
development roadmap with time estimates, milestones, dependencies,
integration gates and definitions of done**.

It is deliberately a living estimate rather than a promised delivery
date.

The estimates assume extensive use of AI-assisted development, including
ChatGPT for architecture, research, specification, review and debugging
assistance, and Codex-style coding agents for implementation,
refactoring, tests and repository work.

AI assistance can compress coding time substantially, but it does not
eliminate:

-   architecture decisions;
-   physical-device testing;
-   integration problems;
-   API/runtime incompatibilities;
-   debugging;
-   latency tuning;
-   security review;
-   user-experience iteration;
-   regression testing.

The project therefore estimates **elapsed focused development time**,
not raw lines-of-code production time.

------------------------------------------------------------------------

# 2. Planning Assumptions

## 2.1 Development resources currently assumed

  -----------------------------------------------------------------------
  Resource                Planning assumption     Effect
  ----------------------- ----------------------- -----------------------
  ChatGPT                 Plus subscription       Architecture, research,
                          currently available     specifications,
                                                  debugging, review and
                                                  planning

  Codex                   Windows/Codex           Implementation,
                          development workflow    repository work, tests,
                          available               refactoring and
                                                  repetitive coding

  Cloud LLM               Gemini/Gemma-family API Early conversational
                          already experimented    backend and provider
                          with                    testing

  Additional cloud AI     Provider-swappable      Can be introduced
                          architecture            without redesigning
                                                  core system

  Acer development laptop i7-class, 32 GB RAM,    Primary
                          NVIDIA 4 GB GPU         coding/build/test
                                                  workstation

  Raspberry Pi 5          Primary physical        UI, touch, audio/event
                          runtime                 handling and device
                                                  services

  Intel NUC               i5 / 16 GB available    Optional local
                                                  AI/services node

  Jetson Nano             First-generation / 4 GB Optional CUDA/vision
                          available               experimentation
  -----------------------------------------------------------------------

Exact account quotas, model limits and API billing are **not treated as
guaranteed capacity**. If a subscription or API limit becomes a
bottleneck, the timeline must be revised rather than silently assuming
unlimited agent throughput.

## 2.2 Working cadence

The timeline uses **Focused Development Days (FDD)**.

One FDD means approximately one productive project day, not necessarily
one calendar day.

This avoids pretending that a hobby/personal engineering project will
receive eight uninterrupted hours every day.

Calendar duration therefore depends on actual cadence:

  Average project effort     10 FDD requires approximately
  ------------------------ -------------------------------
  1 focused day/week                              10 weeks
  2 focused days/week                              5 weeks
  3 focused days/week                           3--4 weeks
  5 focused days/week                              2 weeks

## 2.3 Estimate bands

Each module has three estimates:

-   **Prototype** --- first working vertical slice;
-   **Review/debug** --- make it reliable enough to integrate;
-   **Integrated v1** --- tested with adjacent modules and documented.

These are engineering estimates, not deadlines.

------------------------------------------------------------------------


## 2.4 Pi runtime baseline

The current Raspberry Pi deployment baseline is:

```text
Raspberry Pi OS Lite 64-bit
+ minimal graphics stack
+ Project TARS fullscreen UI
+ supervised Project TARS services
+ SSH/admin tooling
```

The roadmap does not assume installation of a full Raspberry Pi desktop
environment.

This should reduce background overhead and make the Pi behave like a
dedicated appliance.

Development is expected to occur primarily on the Acer workstation, with
deployments pushed to the Pi.

# 3. Project Dashboard

**Current project state:** Specification / architecture / inventory\
**Current software milestone:** M0 --- Repository and runtime
foundation\
**First major target:** M5 --- Usable voice companion\
**First useful companion target:** approximately **20--32 FDD**\
**More complete v1 software target:** approximately **40--65 FDD**\
**Optional vision:** deliberately outside the critical path

  -------------------------------------------------------------------------------------
  Module                       Status                  Critical path? Main blocker
  ---------------------------- ---------------- --------------------- -----------------
  Architecture/specification   In progress                        Yes Continue refining
                                                                      interfaces

  Repository/dev environment   Not started                        Yes Establish
                                                                      canonical
                                                                      repo/toolchain

  Core event/state runtime     Not started                        Yes Interfaces to
                                                                      define

  Display/animation            Not started                        Yes Pi/display
                                                                      verification

  Touch input                  Not started                         No Display/touch
                                                                      verification

  Voice input                  Not started                        Yes Microphone
                                                                      selection/test

  Voice output                 Not started                        Yes TTS/audio path
                                                                      decision

  Orchestrator                 Designed                           Yes Runtime/event
                               conceptually                           contracts

  AI provider layer            Early experiment                   Yes Formal common
                               exists                                 interface

  Personality/policy           Specification                      Yes Runtime policy
                               exists                                 implementation

  Memory                       Designed           No for first speech Schema/API
                               conceptually                           

  Tool framework               Designed           No for first speech Permission model
                               conceptually                           

  Workstation bridge           Designed                            No Local
                               conceptually                           RPC/security

  Local NUC AI                 Candidate                           No Benchmark
                                                                      hardware/models

  Vision                       Deferred                            No Camera/compute
                                                                      benchmark

  Codex integration            Designed                            No Secure tool
                               conceptually                           interface

  Packaging/autostart          Not started                    Yes for Stable services
                                                    appliance-like v1 

  Observability/testing        Not started                        Yes Must grow with
                                                                      every module
  -------------------------------------------------------------------------------------

------------------------------------------------------------------------

# 4. Modularity Rule

Every major capability should be replaceable behind a stable interface.

``` text
UI / DISPLAY
      |
EVENT BUS / STATE
      |
ORCHESTRATOR
      |
+-----+------+-------+-------+
|            |       |       |
VOICE       AI     TOOLS   MEMORY
|            |
STT/TTS   PROVIDERS
             |
       LOCAL / LAN / CLOUD
```

A module must not need to know which vendor/model implements another
module unless that dependency is explicitly part of its interface.

Examples:

``` text
SpeechToText.transcribe(audio)
TextToSpeech.speak(text)
AIProvider.generate(context)
Vision.describe(frame)
Tool.execute(request)
Memory.store(record)
Memory.retrieve(query)
Display.set_state(state)
```

This modularity is one of the project's primary schedule-control
mechanisms: components can be developed and tested independently.

------------------------------------------------------------------------

# 5. Milestone Summary

  Milestone   Result                                  Cumulative estimate
  ----------- ------------------------------------- ---------------------
  M0          Repo + dev/runtime foundation                      2--4 FDD
  M1          Event bus + state machine                          4--7 FDD
  M2          Animated display + touch                          7--12 FDD
  M3          Cloud brain/orchestrator text loop               10--16 FDD
  M4          Voice in + voice out                             16--25 FDD
  **M5**      **First usable desk companion**              **20--32 FDD**
  M6          Memory + personality/policy                      25--39 FDD
  M7          Tools + workstation partnership                  31--48 FDD
  M8          Local NUC/offline intelligence                   35--54 FDD
  M9          Optional vision                                  39--60 FDD
  M10         Codex development-agent integration              43--62 FDD
  M11         v1 hardening / appliance behaviour           **50--75 FDD**

Parallel work means module estimates do not simply add together.

------------------------------------------------------------------------

# 6. WP00 --- Repository, Development Environment & CI Foundation

**Priority:** Critical\
**Prototype:** 1--2 FDD\
**Review/debug:** 0.5--1 FDD\
**Integrated v1:** 2--4 FDD

## Deliverables

-   canonical private repository;
-   project directory layout;
-   Python/runtime version decision;
-   dependency management;
-   `.env` / secrets policy;
-   configuration structure;
-   logging conventions;
-   basic unit-test framework;
-   lint/format/type-check tooling;
-   Pi deployment method;
-   Raspberry Pi OS Lite 64-bit image/baseline definition;
-   minimal graphics/input/audio package manifest;
-   SSH-based deployment workflow;
-   development-machine setup notes;
-   initial CI where useful.

## AI-agent leverage

**Very high.** Coding agents are excellent at scaffolding,
configuration, repetitive tests and documentation.

## Definition of done

A clean machine can clone the repository, install dependencies, run
tests and launch a minimal Project TARS service from documented
instructions.

A clean Pi OS Lite image can also be provisioned into a working Project
TARS runtime using documented or scripted steps.

------------------------------------------------------------------------

# 7. WP01 --- Core Event Bus, State Machine & Service Contracts

**Priority:** Critical\
**Prototype:** 1--2 FDD\
**Review/debug:** 1--2 FDD\
**Integrated v1:** 2--4 FDD

## Responsibilities

-   normalized event schema;
-   companion states;
-   asynchronous event dispatch;
-   service health events;
-   error events;
-   cancellation;
-   timeouts;
-   clean shutdown;
-   configuration loading.

Initial states:

``` text
BOOTING
IDLE
ATTENTIVE
LISTENING
THINKING
SPEAKING
WORKING
NOTIFYING
ERROR
OFFLINE
SLEEPING
```

## Definition of done

Mock modules can publish and consume events without importing each
other's implementation details, and state transitions are covered by
tests.

------------------------------------------------------------------------

# 8. WP02 --- Display & Animation Service

**Priority:** Critical\
**Prototype:** 2--3 FDD\
**Review/debug:** 1--2 FDD\
**Integrated v1:** 3--5 FDD

## First iteration

-   full-screen Pi UI;
-   predefined animation/state assets;
-   immediate listening acknowledgement;
-   thinking loop;
-   speaking response;
-   error/offline state;
-   status overlay;
-   frame-rate/CPU monitoring.

## Later iteration

-   amplitude/timing-reactive speaking animation;
-   ambient idle behaviours;
-   specialist-mode indicators;
-   notification cards;
-   optional diagnostic screen.

## Definition of done

The display reacts immediately to local state changes and remains smooth
while a simulated slow cloud request runs.

------------------------------------------------------------------------

# 9. WP03 --- Touch Input

**Priority:** Medium\
**Prototype:** 1 FDD\
**Review/debug:** 0.5--1 FDD\
**Integrated v1:** 1--2 FDD

## First controls

-   tap to listen;
-   cancel/stop;
-   mute;
-   settings/diagnostics entry;
-   privacy controls;
-   fallback interaction when voice is unavailable.

## Definition of done

Touch events enter the same event system as voice/tool events rather
than bypassing the architecture.

------------------------------------------------------------------------

# 10. WP04 --- AI Provider Abstraction / "Cloud Brain"

**Priority:** Critical\
**Prototype:** 1--2 FDD\
**Review/debug:** 1 FDD\
**Integrated v1:** 2--4 FDD

## Common interface

``` text
generate()
stream()
vision()
tool_call()
health_check()
```

Initial implementation may wrap the already-tested Gemini/Gemma-family
cloud endpoint.

Other providers remain adapters rather than architectural changes.

## Required behaviour

-   streaming;
-   timeout;
-   cancellation;
-   retry policy;
-   provider health;
-   usage/error logging;
-   provider selection;
-   graceful unavailable state.

## Definition of done

A test conversation can switch between at least a mock provider and one
real provider without changing the orchestrator.

------------------------------------------------------------------------

# 11. WP05 --- Assistant Orchestrator

**Priority:** Critical / core brain\
**Prototype:** 2--4 FDD\
**Review/debug:** 2--3 FDD\
**Integrated v1:** 4--7 FDD

## Responsibilities

-   receive normalized events;
-   assemble context;
-   decide local/LAN/cloud path;
-   call AI providers;
-   call tools;
-   stream output;
-   manage cancellation;
-   maintain conversation state;
-   apply personality/policy;
-   enforce permissions;
-   expose provenance/uncertainty where useful;
-   handle degraded operation.

## Definition of done

Text input can traverse:

``` text
INPUT -> ORCHESTRATOR -> PROVIDER -> STREAMED RESPONSE -> DISPLAY/LOG
```

with cancellation, timeout and simulated provider failure handled
cleanly.

------------------------------------------------------------------------

# 12. WP06 --- Voice Input Pipeline

**Priority:** Critical\
**Prototype:** 2--4 FDD\
**Review/debug:** 2--3 FDD\
**Integrated v1:** 4--7 FDD

## Modules

``` text
MICROPHONE
  -> AUDIO CAPTURE
  -> VAD
  -> WAKE / PUSH-TO-TALK
  -> STT
  -> NORMALIZED USER EVENT
```

Wake word can follow push-to-talk during early development rather than
blocking the first useful build.

## Testing

-   quiet room;
-   normal desk noise;
-   speaker active;
-   interruptions;
-   false wake rate;
-   end-of-speech latency;
-   STT accuracy.

## Definition of done

Normal desk speech reliably produces a text event with measured latency
and visible microphone/listening state.

------------------------------------------------------------------------

# 13. WP07 --- Voice Output / TTS Pipeline

**Priority:** Critical\
**Prototype:** 1--3 FDD\
**Review/debug:** 1--2 FDD\
**Integrated v1:** 3--5 FDD

## Requirements

-   streaming or low-latency TTS where possible;
-   interruptible playback;
-   volume control;
-   mute;
-   speech-state events;
-   display synchronization;
-   configurable voice provider;
-   local/cloud implementations interchangeable.

## Definition of done

TARS can speak a streamed answer, animate while speaking, and stop
quickly when interrupted.

------------------------------------------------------------------------

# 14. WP08 --- Conversational Loop Integration

**Priority:** Critical\
**Prototype:** 1--2 FDD\
**Review/debug:** 2--3 FDD\
**Integrated v1:** 3--5 FDD

This creates the first complete loop:

``` text
USER SPEAKS
 -> LISTENING DISPLAY
 -> STT
 -> ORCHESTRATOR
 -> CLOUD/LOCAL AI
 -> STREAMED RESPONSE
 -> TTS
 -> SPEAKING DISPLAY
 -> IDLE
```

## Milestone M5 --- First Usable Companion

M5 is reached when the above loop works repeatedly without developer
intervention.

This is the most important early milestone.

Everything after M5 improves capability; M5 proves the architecture.

------------------------------------------------------------------------

# 15. WP09 --- Personality & Behaviour Policy Runtime

**Priority:** High\
**Prototype:** 1--2 FDD\
**Review/debug:** 1--2 FDD\
**Integrated v1:** 2--4 FDD

Implement the personality specification as configuration and policies
rather than one giant prompt.

Includes:

-   personality parameters;
-   severity/tone governor;
-   humour limits;
-   attention policy;
-   epistemic/provenance policy;
-   specialist-mode hooks;
-   persistent bounded behavioural state;
-   non-verbal response vocabulary.

## Definition of done

Changing the underlying AI provider does not noticeably replace the
Project TARS identity.

------------------------------------------------------------------------

# 16. WP10 --- Memory & Working State

**Priority:** High but not M5-critical\
**Prototype:** 1--2 FDD\
**Review/debug:** 1--2 FDD\
**Integrated v1:** 3--5 FDD

Initial SQLite-backed categories:

-   session context;
-   working state;
-   approved preferences;
-   deliberate long-term memory;
-   diagnostic/system history.

Vector retrieval is deferred until actual stored material justifies it.

## Definition of done

Memory writes are explicit and inspectable; restart preserves intended
state without confusing diagnostic logs with conversational memory.

------------------------------------------------------------------------

# 17. WP11 --- Tool Framework

**Priority:** High\
**Prototype:** 2--3 FDD\
**Review/debug:** 2--3 FDD\
**Integrated v1:** 4--6 FDD

Every tool should define:

``` text
name
schema
permissions
timeout
host
risk/severity
result format
audit behaviour
```

Initial low-risk tools:

-   system information;
-   project/file lookup;
-   controlled status queries;
-   Git read/status operations;
-   PC telemetry.

Higher-risk write/shell tools come later.

## Definition of done

A provider can request a permitted tool through the orchestrator,
receive a structured result and cannot silently bypass the permission
layer.

------------------------------------------------------------------------

# 18. WP12 --- Workstation Partnership / LAN RPC

**Priority:** Medium-high\
**Prototype:** 2--3 FDD\
**Review/debug:** 1--2 FDD\
**Integrated v1:** 3--5 FDD

## Responsibilities

-   node discovery or initial static configuration;
-   authenticated local RPC;
-   health/status;
-   workstation telemetry;
-   remote task request;
-   cancellation;
-   structured result return;
-   audit log.

## Definition of done

The Pi can safely request one useful service from the workstation
without exposing an unrestricted remote shell.

------------------------------------------------------------------------

# 19. WP13 --- NUC Local Compute Services

**Priority:** Medium\
**Prototype:** 2--4 FDD after benchmark\
**Review/debug:** 1--2 FDD\
**Integrated v1:** 3--6 FDD

Candidate services:

-   local STT;
-   local TTS;
-   embeddings;
-   vector database;
-   small quantized LLM;
-   background indexing;
-   local tool services.

Do not build every service merely because the NUC exists.

## Definition of done

At least one workload can route Pi -\> NUC -\> Pi with health detection
and automatic fallback.

------------------------------------------------------------------------

# 20. WP14 --- Offline / Degraded Operation

**Priority:** High for robust v1\
**Prototype:** 1--2 FDD\
**Review/debug:** 1--2 FDD\
**Integrated v1:** 2--4 FDD

Scenarios:

-   cloud unavailable;
-   NUC unavailable;
-   workstation unavailable;
-   STT unavailable;
-   TTS unavailable;
-   network unavailable.

## Definition of done

Loss of an optional service reduces capability without freezing or
misleading the user.

------------------------------------------------------------------------

# 21. WP15 --- Optional Vision

**Priority:** Deferred / optional\
**Prototype:** 2--4 FDD\
**Review/debug:** 2--3 FDD\
**Integrated v1:** 4--7 FDD

Vision is **not on the first-useful-version critical path**.

First slice:

``` text
USER REQUEST
 -> CAMERA SNAPSHOT
 -> LOCAL/LAN/CLOUD VISION
 -> RESULT
 -> DISCARD IMAGE BY DEFAULT
```

Later:

-   presence detection;
-   object detection;
-   QR/code recognition;
-   workbench inspection;
-   workstation awareness.

Jetson Nano, NUC and future Pi accelerator options should be benchmarked
rather than assumed.

## Definition of done

Camera use is visible, permission-aware and event-driven, and images are
not silently retained or uploaded.

------------------------------------------------------------------------

# 22. WP16 --- Codex / Development-Agent Integration

**Priority:** Medium / high-value specialist feature\
**Prototype:** 2--4 FDD\
**Review/debug:** 2--3 FDD\
**Integrated v1:** 4--7 FDD

Target workflow:

``` text
VOICE / TOUCH REQUEST
 -> TARS ORCHESTRATOR
 -> DEVELOPMENT INTENT
 -> PERMISSION / SCOPE
 -> CODEX AGENT ON DEVELOPMENT PC
 -> DIFF / TESTS / RESULT
 -> TARS SUMMARY
```

This should come **after** the generic tool framework and workstation
bridge exist.

## Safety boundary

The development agent is a tool, not the personality engine.

Repository modifications should remain reviewable.

## Definition of done

A bounded development task can be requested through TARS, executed
through the development toolchain, tested, and summarized with the
resulting changes inspectable.

------------------------------------------------------------------------

# 23. WP17 --- Attention, Notifications & Proactivity

**Priority:** Medium\
**Prototype:** 1--2 FDD\
**Review/debug:** 1--2 FDD\
**Integrated v1:** 2--4 FDD

Event levels:

``` text
SILENT
AMBIENT
INFO
IMPORTANT
URGENT
```

The attention manager chooses:

-   no interruption;
-   visual state only;
-   subtle sound;
-   notification;
-   spoken interruption.

## Definition of done

Routine events do not make the companion annoying, while important
events reliably surface.

------------------------------------------------------------------------

# 24. WP18 --- Observability, Test Harness & Diagnostics

**Priority:** Continuous / critical\
**Initial foundation:** 1--2 FDD\
**Ongoing:** approximately 15--25% of integration effort

Build alongside every module:

-   structured logs;
-   event trace;
-   latency metrics;
-   provider health;
-   node health;
-   audio timings;
-   test fixtures;
-   mock AI providers;
-   mock tools;
-   replayable event sequences;
-   crash reports;
-   diagnostic UI.

AI coding agents can generate large portions of tests, but humans still
need to decide whether those tests prove the correct behaviour.

------------------------------------------------------------------------

# 25. WP19 --- Packaging, Boot, Updates & Appliance Behaviour

**Priority:** Critical for v1\
**Prototype:** 1--2 FDD\
**Review/debug:** 2--3 FDD\
**Integrated v1:** 3--5 FDD

Includes:

-   Raspberry Pi OS Lite 64-bit runtime baseline;
-   no conventional desktop environment by default;
-   minimal graphics stack required by selected UI framework;
-   boot directly into companion UI;
-   service supervision;
-   restart after crash;
-   configuration validation;
-   log rotation;
-   safe shutdown;
-   version display;
-   deployment/update process;
-   backup/restore of configuration and memory.

## Definition of done

Powering the Pi on results in a usable companion without opening a
terminal.

------------------------------------------------------------------------

# 26. Critical Path to First Useful Companion

The shortest sensible path is:

``` text
WP00 REPO / ENVIRONMENT
        |
WP01 EVENT BUS / STATE
        |
+-------+--------+
|                |
WP02 DISPLAY   WP04 AI PROVIDER
|                |
+------ WP05 ORCHESTRATOR
               |
        +------+------+
        |             |
     WP06 STT       WP07 TTS
        |             |
        +------WP08---+
               |
              M5
      FIRST USABLE COMPANION
```

Touch can develop alongside display.

Personality can begin as a thin policy configuration and deepen after
M5.

Memory, tools, NUC compute, vision and Codex integration should **not
block M5**.

------------------------------------------------------------------------

# 27. Suggested Iteration Schedule

## Iteration A --- Skeleton

**Estimate:** 4--7 FDD

Goal:

> The system boots, displays state, passes events and can talk to a
> cloud AI through typed interfaces.

Includes WP00, WP01, early WP02, WP04 and early WP05.

## Iteration B --- It Talks

**Estimate:** additional 6--10 FDD

Goal:

> Type/touch input produces a streamed AI response and spoken output
> with display feedback.

Adds touch, TTS and orchestration refinement.

## Iteration C --- It Listens

**Estimate:** additional 6--9 FDD

Goal:

> Reliable desk voice conversation.

Adds microphone, VAD/STT, interruption and audio debugging.

## Iteration D --- It Becomes TARS

**Estimate:** additional 4--7 FDD

Goal:

> Persistent original identity, working state, useful memory and
> appropriate behaviour.

Adds personality runtime, memory and attention foundation.

## Iteration E --- It Does Things

**Estimate:** additional 6--10 FDD

Goal:

> Safe tool use and workstation partnership.

Adds generic tools, permissions and LAN RPC.

## Iteration F --- It Uses the Machines Around It

**Estimate:** additional 4--7 FDD

Goal:

> Local NUC/workstation services participate automatically.

Adds routing, health and degraded-mode logic.

## Iteration G --- It Sees

**Estimate:** additional 4--7 FDD

Goal:

> Optional, privacy-aware vision.

Not required before useful deployment.

## Iteration H --- It Helps Build Itself

**Estimate:** additional 4--7 FDD

Goal:

> TARS can delegate bounded development work to Codex and report the
> result.

## Iteration I --- Harden v1

**Estimate:** additional 7--12 FDD

Goal:

> Reliable daily desk use.

Focus:

-   soak testing;
-   audio edge cases;
-   reconnection;
-   crashes;
-   boot/restart;
-   permissions;
-   latency;
-   UX annoyances;
-   documentation;
-   backup/recovery.

------------------------------------------------------------------------

# 28. Parallelisation Opportunities

AI coding agents make parallel work practical, but only when interfaces
are frozen enough.

Good parallel pairs:

``` text
DISPLAY       || AI PROVIDER ADAPTER
TOUCH         || TTS
MEMORY        || TOOL SCHEMAS
NUC SERVICE   || WORKSTATION SERVICE
VISION        || NON-VISION CORE HARDENING
TESTS         || IMPLEMENTATION
DOCUMENTATION || IMPLEMENTATION
```

Poor parallelisation:

``` text
multiple agents independently changing the event schema
multiple agents redesigning the orchestrator simultaneously
UI built against an undefined state model
tools built before permissions/contracts exist
```

**Rule:** parallelize modules, serialize architecture changes.

------------------------------------------------------------------------


# 29. Multi-Agent Development Strategy

Multiple coding agents may work on Project TARS concurrently. This is an
explicit development strategy, not an accidental side effect of using AI
tools.

The objective is to reduce elapsed implementation time **without allowing
parallel agents to fragment the architecture**.

## 29.1 Core rule

> **One architecture, many bounded workers.**

Agents may work concurrently on separate modules, tests, documentation,
review and supporting tasks once the relevant contracts are stable.

Agents should generally **not** make independent competing changes to the
same core files.

## 29.2 Recommended agent roles

A development iteration may assign roles such as:

| Agent | Example responsibility |
|---|---|
| Architecture / lead agent | Interfaces, acceptance criteria, dependency decisions |
| Display agent | UI, animation and display-state service |
| Voice-input agent | Audio capture, VAD, wake/push-to-talk and STT adapter |
| Voice-output agent | TTS, playback, interruption and speech-state events |
| Provider agent | Gemini/OpenAI/local AI provider adapters |
| Memory agent | SQLite state/memory implementation |
| Tooling agent | Tool schemas, permission layer and selected tools |
| Test agent | Unit, contract, integration and regression tests |
| Review agent | Independent code/diff review against specifications |
| Documentation agent | API notes, deployment docs and change records |

These are temporary roles. A separate permanent agent is not required for
every module.

## 29.3 Work-package contract

Before an implementation agent starts, its task should contain:

```text
WORK PACKAGE ID
OBJECTIVE
FILES / MODULE OWNERSHIP
INPUT INTERFACES
OUTPUT INTERFACES
DEPENDENCIES
ACCEPTANCE CRITERIA
TEST REQUIREMENTS
OUT-OF-SCOPE ITEMS
SECURITY / PERMISSION CONSTRAINTS
EXPECTED DELIVERABLE
```

The clearer this contract is, the safer parallel development becomes.

## 29.4 File and module ownership

During a parallel work cycle, each implementation agent should have a
defined ownership boundary.

Preferred:

```text
Agent A -> tars/display/*
Agent B -> tars/audio/stt/*
Agent C -> tars/providers/*
Agent D -> tests/contracts/*
```

Avoid:

```text
Agent A -> modifies orchestrator.py
Agent B -> independently modifies orchestrator.py
Agent C -> changes event schema at the same time
```

Shared/core files should normally have a single integration owner for that
cycle.

## 29.5 Branch/worktree model

Where the development environment supports it, each implementation task
should use its own Git branch or worktree.

Example:

```text
main
 |
 +-- feature/display-state
 +-- feature/stt-pipeline
 +-- feature/provider-gemini
 +-- test/event-contracts
```

Agents should commit small, reviewable changes.

No agent should silently merge its own work into the protected integration
branch merely because its local tests pass.

## 29.6 Testing hierarchy

Testing should happen **throughout** development rather than only once all
agents have finished.

```text
AGENT IMPLEMENTS MODULE
        |
MODULE UNIT TESTS
        |
CONTRACT TESTS
        |
INDEPENDENT REVIEW
        |
MERGE TO INTEGRATION BRANCH
        |
CROSS-MODULE INTEGRATION TESTS
        |
SYSTEM / HARDWARE TEST
        |
REGRESSION SUITE
```

### Level 1 — Unit tests

Written alongside the module.

They verify internal behaviour in isolation.

### Level 2 — Contract tests

Verify that the module obeys the agreed interface.

Examples:

- STT always returns the agreed transcript/result structure;
- providers expose consistent streaming events;
- display service accepts defined state events;
- tools obey the common result/error schema.

Contract tests are particularly important for multi-agent development
because they let one agent implement against another module before that
module is complete.

### Level 3 — Integration tests

Run after independently developed modules are combined.

Examples:

```text
STT -> EVENT BUS -> ORCHESTRATOR
ORCHESTRATOR -> PROVIDER -> STREAM
STREAM -> TTS -> DISPLAY
ORCHESTRATOR -> TOOL -> RESULT
```

### Level 4 — System tests

Run on the actual Project TARS hardware/environment.

These measure real behaviour that mocks cannot prove:

- microphone behaviour;
- speaker echo;
- touch;
- display responsiveness;
- Pi CPU/RAM use;
- network latency;
- NUC/workstation availability;
- camera behaviour;
- restart/recovery.

### Level 5 — Regression tests

Every fixed bug should add a regression test where practical.

A bug should ideally be allowed to fail a test once and never surprise us
the same way again.

## 29.7 Cross-agent review

Code review should deliberately use an agent that did **not** author the
change when practical.

The review agent checks:

- work-package requirements;
- architecture/interface compliance;
- unnecessary coupling;
- error handling;
- cancellation/timeouts;
- security/permission boundaries;
- test quality;
- maintainability;
- logging;
- documentation;
- accidental scope expansion.

The authoring agent may then address review findings.

This creates an AI equivalent of maker/checker separation, while final
engineering judgement remains with the human project owner.

## 29.8 Integration agent / maintainer role

One agent or development session should act as **integration maintainer**.

Its job is not to rewrite every module.

It should:

- verify branches are based on the expected interfaces;
- run contract tests;
- resolve controlled merge conflicts;
- reject architectural drift;
- run the integrated test suite;
- record failures;
- coordinate fixes back to module agents.

This role prevents “everyone edits everything” development.

## 29.9 Parallel workflow example

A voice-companion iteration could run as:

```text
                    FROZEN INTERFACES
                           |
        +------------------+------------------+
        |                  |                  |
   AGENT A             AGENT B            AGENT C
   Display             STT                AI Provider
        |                  |                  |
   unit tests          unit tests         unit tests
        |                  |                  |
        +--------- CONTRACT TESTS ------------+
                           |
                     REVIEW AGENTS
                           |
                    INTEGRATION MERGE
                           |
               CROSS-MODULE TEST SUITE
                           |
                    PI HARDWARE TEST
                           |
                   ACCEPT / FIX / REPEAT
```

Meanwhile a separate test agent can build mocks and integration fixtures
against the frozen contracts.

## 29.10 When multiple agents may work on one section

Yes, more than one agent may contribute to the **same work package**, but
their responsibilities should still be separated.

Good example for Voice Input:

```text
Agent A -> audio capture + buffering
Agent B -> VAD / endpoint detection
Agent C -> STT provider adapter
Agent D -> tests and audio fixtures
Agent E -> review
```

Less desirable:

```text
Agent A -> implements entire STT pipeline
Agent B -> independently implements same entire STT pipeline
Agent C -> independently rewrites both
```

Competing implementations can occasionally be useful for a short
benchmark/spike, but should be intentional rather than normal workflow.

## 29.11 Agent concurrency limit

More agents do not automatically mean more speed.

For early Project TARS development, a practical starting point is:

```text
2–4 implementation agents
+ 1 test/review role
+ 1 integration/lead role
```

The exact number should be increased only when there are enough genuinely
independent work packages.

Coordination overhead becomes counterproductive when agents spend more time
creating merge conflicts and incompatible assumptions than writing useful
code.

## 29.12 Merge gate / definition of agent-done

An agent task is not complete because code exists.

Before merge:

- [ ] Work-package acceptance criteria satisfied.
- [ ] Unit tests pass.
- [ ] Contract tests pass.
- [ ] Lint/type/static checks pass where configured.
- [ ] No secrets committed.
- [ ] Public interfaces documented.
- [ ] Independent review completed.
- [ ] Review findings resolved or explicitly accepted.
- [ ] Integration branch tests pass.
- [ ] Relevant hardware test completed when required.
- [ ] Roadmap/spec updated if implementation changed an assumption.

## 29.13 Human control

Coding agents may propose architecture changes, but architecture-changing
decisions should be explicitly reviewed before they become project truth.

Agents should not independently:

- weaken permissions;
- expose unrestricted shell access;
- commit credentials;
- change core event schemas casually;
- replace provider abstractions with vendor-specific coupling;
- remove tests merely to make a build pass;
- silently redefine acceptance criteria.

## 29.14 Expected schedule effect

Multi-agent development can reduce **elapsed** time substantially when work
packages are independent.

It does not divide time perfectly by the number of agents.

For example, three 3-FDD modules may potentially be implemented largely in
parallel, but integration and review still consume real elapsed time.

The roadmap should therefore track two quantities where useful:

```text
ENGINEERING EFFORT = total work across agents
ELAPSED TIME       = wall-clock/project time to integrated result
```

The purpose of multi-agent development is primarily to reduce **elapsed
time**, while maintaining or improving test and review quality.

---

# 30. AI-Assisted Development Productivity Model

Coding agents change where project time is spent.

Without agents, much effort goes into:

``` text
typing boilerplate
looking up APIs
writing repetitive tests
refactoring mechanically
documentation scaffolding
```

With agents, more of the human effort moves toward:

``` text
choosing architecture
writing acceptance criteria
reviewing diffs
running hardware tests
debugging integration
measuring latency
deciding what feels right
```

For well-specified isolated modules, agent assistance may reduce
implementation effort substantially.

For cross-module integration, physical audio, asynchronous bugs and
user-experience tuning, the improvement is smaller.

Therefore this roadmap does **not** apply a blanket "AI makes
development 5× faster" assumption.

------------------------------------------------------------------------

# 31. Time-Risk Multipliers

Increase an estimate when:

  Condition                                                           Suggested effect
  ----------------------------------------------------- ------------------------------
  API/library behaves differently on Pi than desktop                          +25--50%
  Audio echo/full-duplex issue                            +50--150% to voice debugging
  Undocumented hardware/driver issue                                         +25--100%
  Module interface changes after dependants exist                             +25--75%
  Agent-generated code requires architectural rewrite                         +20--50%
  New provider/API added behind stable adapter                                +10--25%
  New provider added without abstraction                    potentially major redesign
  Good automated tests already exist                         reduces regression effort
  Existing proven library solves module                       reduces prototype effort

------------------------------------------------------------------------

# 32. Definition of "First Useful Version"

The first useful version does **not** need vision, a local LLM, Codex
control or every personality feature.

It needs to:

1.  boot reliably;
2.  show a responsive face/state UI;
3.  accept touch and/or voice;
4.  recognize speech adequately;
5.  route a request through the orchestrator;
6.  use a real AI provider;
7.  stream an answer;
8.  speak the answer;
9.  allow interruption/cancellation;
10. expose failures honestly;
11. preserve the Project TARS identity;
12. recover cleanly enough for repeated desk use.

This prevents optional sophistication from delaying the moment the
companion becomes genuinely usable.

------------------------------------------------------------------------

# 33. Definition of v1

v1 should additionally have:

-   robust voice loop;
-   personality/policy runtime;
-   working-state/memory foundation;
-   tool permission framework;
-   useful workstation integration;
-   graceful offline/degraded modes;
-   diagnostics;
-   autostart/recovery;
-   configuration backup;
-   reasonable security;
-   documented deployment;
-   regression tests.

Vision and deep Codex integration may be v1.x features if they threaten
the core schedule.

------------------------------------------------------------------------

# 34. Review Gates

At the end of every iteration:

``` text
1. DEMO
2. MEASURE
3. TEST
4. LIST FAILURES
5. UPDATE SPEC
6. UPDATE ESTIMATE
7. DECIDE NEXT ITERATION
```

Questions:

-   Does it work?
-   Is it responsive?
-   Is the interface still modular?
-   What did we learn?
-   What assumptions were wrong?
-   What should be removed?
-   What is now blocking the critical path?
-   Has a purchase become justified by evidence?

------------------------------------------------------------------------

# 35. Timeline Interpretation

Under concentrated development, the first genuinely usable voice
companion is plausibly a **few focused weeks**, not many months.

A more complete and hardened software v1 is more realistically **50--75
focused development days**, with the calendar duration determined by how
often development sessions occur.

A personal project rarely progresses linearly. The roadmap therefore
values **small demonstrable milestones** over a single launch date.

The correct schedule is the one that changes when evidence changes.

------------------------------------------------------------------------

# 36. Current Next Actions

-   [ ] Establish canonical private code repository.
-   [ ] Record actual development toolchain and versions.
-   [ ] Decide initial Pi OS/runtime/Python baseline.
-   [ ] Define repository/module layout.
-   [ ] Define event schema.
-   [ ] Define service interfaces.
-   [ ] Create mock AI provider.
-   [ ] Create first display state prototype.
-   [ ] Formalize Gemini/Gemma provider adapter.
-   [ ] Build text-only orchestrator vertical slice.
-   [ ] Verify microphone/speaker candidates before committing voice
    implementation.
-   [ ] Update this dashboard after the first implementation session.

------------------------------------------------------------------------

# 37. Decision Log

## R001 --- Firmware/software roadmap uses Focused Development Days

**Status:** Adopted.

Calendar estimates are derived from actual development cadence rather
than assuming full-time work.

## R002 --- First usable companion precedes optional sophistication

**Status:** Adopted.

Vision, local LLM hosting and Codex integration must not unnecessarily
block the first working conversational companion.

## R003 --- Modular interfaces are schedule protection

**Status:** Adopted.

Providers, STT, TTS, vision, memory, tools and compute nodes must remain
replaceable behind explicit interfaces.

## R004 --- AI coding agents accelerate implementation, not engineering judgement

**Status:** Adopted.

Agent output remains subject to review, tests and integration
validation.

## R005 --- Parallelize modules, serialize architecture changes

**Status:** Adopted.

Multiple agents may work independently where contracts are stable;
competing architectural changes should not be merged blindly.

## R006 --- Estimates are revised after every meaningful prototype

**Status:** Adopted.

Measured progress replaces initial assumptions.

## R007 --- Multi-agent implementation is an explicit project strategy

**Status:** Adopted.

Independent coding agents may work concurrently where module boundaries and
interfaces are sufficiently stable.

## R008 --- Agent work requires maker/checker separation where practical

**Status:** Adopted.

An agent that did not author a change should review it before integration
when practical.

## R009 --- Tests run continuously, not only after all agents finish

**Status:** Adopted.

Unit and contract tests belong to module development; integration, system
and regression tests follow progressively.

## R010 --- Shared architecture has a single integration owner per cycle

**Status:** Adopted.

Parallel agents must not independently redefine shared contracts during the
same integration cycle.


## R011 --- Pi runtime uses Raspberry Pi OS Lite 64-bit by default

**Status:** Adopted.

The Pi should run only the packages/services required for Project TARS,
rather than carrying the overhead of a complete desktop environment.

## R012 --- Development and runtime environments are intentionally separated

**Status:** Adopted.

The Acer development machine is the primary engineering environment; the
Pi is a reproducible deployment target and appliance runtime.

------------------------------------------------------------------------

# 38. Version History

  -----------------------------------------------------------------------
  Version                 Date                    Notes
  ----------------------- ----------------------- -----------------------
  0.1                     2026-08-09              Initial modular
                                                  firmware/software
                                                  roadmap, dashboard,
                                                  critical path, FDD
                                                  estimates, AI-assisted
                                                  productivity model,
                                                  milestones and
                                                  definitions of done

  -----------------------------------------------------------------------
