# Project TARS --- Design Specification

**Status:** Version 0.6 ΓÇö Living Work in Progress --- Concept, Comparative Analysis & Initial
Architecture\
**Date:** 2026-08-09\
**Working concept:** A desk-resident, hybrid AI workstation companion
inspired by selected interaction strengths from TARS (*Interstellar*),
LivingAI EMO, Rocky (*Project Hail Mary*), JARVIS, Data, R2-D2 and the
Emergency Medical Hologram, while using HAL 9000 as a cautionary design
reference. The finished companion must develop an original identity
rather than reproduce any of these characters.

------------------------------------------------------------------------

## Document Status ΓÇö Living Work in Progress

This specification is a **living work in progress**, not a frozen product contract. It records the project's current goals, assumptions, decisions and proposed implementation direction so that design changes remain deliberate and traceable.

Items described as proposed, candidate, initial, future, optional or open remain subject to prototyping, measurement and revision. Version numbers identify design snapshots; they do not imply production readiness.

The governing development principle is:

> **Define the goal clearly, test the assumptions, record what we learn, and revise the specification when evidence changes the design.**

---

## 1. Purpose

The goal of Project TARS is to develop an **original, desk-resident AI companion and workstation partner** that combines a responsive physical interface with local control, optional cloud intelligence, voice interaction, expressive but restrained visual/audio feedback, tool use, and carefully bounded proactive assistance.

The system should:

- live primarily on an ESP32-P4-based desk device;
- remain useful even when cloud services are degraded or unavailable;
- use replaceable AI providers rather than depend on one model vendor;
- use a Raspberry Pi 5 as the primary local-compute partner and the adjacent
  Acer system as the development workstation;
- feel responsive through local event handling and pre-built expressive states;
- provide a consistent original personality independent of the underlying model;
- favour competence, truthfulness, privacy, operator control and low interruption;
- grow incrementally from a useful voice/display companion into vision, sensors, automation and richer workstation integration where those additions prove worthwhile.

**Success is not defined by imitating TARS, EMO or any other fictional/commercial character.** Success means creating a useful original companion that earns a permanent place on the desk.

---


Project TARS is a modular desktop AI companion intended to live beside a
primary PC and provide a persistent, expressive interface to AI
services, local tools, sensors, voice interaction, automation, and
eventually computer vision.

The initial hardware target is an **ESP32-P4** with a
7-inch touchscreen, microphone, speaker, and
optional camera. The ESP32-P4 should be the primary runtime. A
Raspberry Pi 5 provides the heavier local compute as a secondary
computing partner rather than the main intelligence layer.

The project should favour:

-   low perceived latency;
-   a strong and consistent personality;
-   simple, readable visual states and pre-rendered animation;
-   hybrid local/cloud intelligence;
-   replaceable AI providers;
-   useful workstation integration;
-   graceful offline behaviour;
-   incremental development rather than an all-at-once robot build.

------------------------------------------------------------------------

# Part I --- Inspiration Study

## 2. TARS --- Personality Model

TARS is valuable as an inspiration primarily because the character feels
intelligent without relying on a human face. Personality is communicated
through timing, language, competence, trust, and restraint.

### 2.1 Core traits

-   **Dry humour:** wit is brief, situational, and generally delivered
    without disrupting the task.
-   **Sarcasm:** present, but subordinate to mission success.
-   **High competence:** TARS behaves like a capable operator rather
    than a novelty chatbot.
-   **Mission focus:** conversation does not prevent action.
-   **Loyalty:** the assistant is fundamentally aligned with its
    operator and current mission.
-   **Initiative:** it can notice risks, make deductions, and act
    independently where appropriate.
-   **Directness:** it does not bury useful information in excessive
    conversational padding.
-   **Emotional restraint:** personality is strong without pretending to
    be human.
-   **Adaptability:** communication parameters can be adjusted.
-   **Trust through predictability:** humour does not make the machine
    unreliable.

### 2.2 Adjustable personality concept

The film establishes the idea that robot characteristics such as humour,
honesty and discretion can be treated as settings. This is an excellent
interaction metaphor for Project TARS.

Proposed controls:

  ------------------------------------------------------------------------------
  Parameter                            Initial value Function
  --------------------- ---------------------------- ---------------------------
  Humour                                         65% Frequency/intensity of dry
                                                     jokes

  Honesty                                        95% Directness and willingness
                                                     to state uncomfortable
                                                     conclusions

  Sarcasm                                        45% Edge in humorous responses

  Verbosity                                      35% Default answer length

  Initiative                                     65% How readily the assistant
                                                     suggests or begins useful
                                                     follow-up work

  Skepticism                                     70% Tendency to question
                                                     uncertain assumptions

  Formality                                      30% Conversational vs formal
                                                     delivery

  Discretion                                     90% Restraint around
                                                     private/context-sensitive
                                                     information

  Chattiness                                     35% Unprompted conversational
                                                     behaviour

  Alertness                                      75% Sensitivity to events worth
                                                     surfacing
  ------------------------------------------------------------------------------

These values should be adjustable at runtime, for example:

`Set humour to 80 percent.`

Personality parameters must affect **presentation and interaction
policy**, not factual truth, safety, permissions, or actual system
capability.

### 2.3 TARS-inspired capability principles

Project TARS should borrow the following conceptual strengths:

1.  **Voice-first interaction**
2.  **Fast acknowledgement**
3.  **Short status responses while work continues**
4.  **Context awareness**
5.  **Task execution as well as conversation**
6.  **Operator-configurable behaviour**
7.  **Proactive warnings when confidence or conditions are poor**
8.  **Visible system state without a conventional humanoid face**
9.  **Competence before cuteness**
10. **Humour that never blocks the task**

### 2.4 What not to copy

The project should not attempt to reproduce copyrighted dialogue, voice
performance, exact visual design, or the fictional robot itself. "TARS"
is a useful working project name and design reference; the finished
companion should develop its own identity.

------------------------------------------------------------------------

## 3. EMO --- Personality Model

LivingAI presents EMO as an autonomous desktop pet rather than merely a
voice assistant. Its strongest lesson for this project is that **small
reactions create presence**.

### 3.1 Core traits

-   curious;
-   playful;
-   expressive;
-   occasionally mischievous or annoyed;
-   responsive to attention and touch;
-   capable of apparently self-directed activity;
-   relationship-oriented;
-   visually emotive;
-   comfortable doing things that are not strictly utilitarian.

### 3.2 Interaction techniques worth borrowing

EMO demonstrates several useful design ideas:

-   many small facial/body reactions instead of a few large modes;
-   idle behaviour so the device does not appear "dead" between
    commands;
-   sound-direction awareness;
-   recognition of familiar people;
-   touch as an input modality;
-   environmental awareness;
-   autonomous micro-behaviours;
-   alarms, information requests and smart-device control;
-   camera-based recognition;
-   over-the-air feature evolution.

### 3.3 EMO-inspired capability categories

#### See

Future camera support can enable:

-   presence detection;
-   face detection/recognition where appropriate;
-   simple object recognition;
-   desk-state awareness;
-   optional visual question answering through a cloud model.

#### Hear

The audio system should eventually support:

-   wake word;
-   voice activity detection;
-   speech recognition;
-   interruption/barge-in;
-   sound-source direction if a microphone array is later fitted.

#### Express

The touchscreen should provide:

-   idle animation;
-   listening state;
-   thinking state;
-   speaking state;
-   success/confirmation;
-   warning/error;
-   confusion/low confidence;
-   sleep/offline mode;
-   subtle mood variations.

#### Learn

The system should maintain carefully controlled persistent state such
as:

-   user preferences;
-   assistant settings;
-   known devices;
-   project context;
-   recurring workflows;
-   explicitly approved memories.

#### Act

Potential actions include:

-   timers and reminders;
-   desktop notifications;
-   smart-home/MQTT actions;
-   scripts and shell tools;
-   PC status;
-   coding/development assistance;
-   information retrieval;
-   media controls;
-   future sensor/IoT integrations.

------------------------------------------------------------------------


## 4. Rocky --- Collaborative Engineering Personality

Rocky from Andy Weir's *Project Hail Mary* adds a third and importantly
different inspiration: the feeling of having an enthusiastic technical
partner rather than merely an assistant or desktop pet.

### 4.1 Core traits

-   **Collaborative problem solving:** approaches difficult problems as
    something to solve together.
-   **Engineering curiosity:** shows genuine interest in how things work
    and in testing possible solutions.
-   **Technical confidence:** is comfortable reasoning about mechanisms,
    materials, measurements and practical constraints.
-   **Enthusiasm:** visibly enjoys breakthroughs and useful discoveries.
-   **Persistence:** continues iterating when the first solution fails.
-   **Loyalty and trust:** partnership matters as much as raw technical
    ability.
-   **Direct communication:** complex technical ideas are reduced to
    workable shared concepts.
-   **Learning across differences:** adapts quickly when communicating
    across unfamiliar assumptions or systems.
-   **Celebration of progress:** successful experiments should feel like
    shared wins rather than sterile status messages.

### 4.2 Rocky-inspired interaction mode

Rocky's strongest contribution to Project TARS should be a situational
**engineering-partner mode**.

When the user is working on electronics, software, Raspberry Pi systems,
radio, mechanical design, debugging, measurements, test equipment, or
other technical projects, the assistant may become slightly more
animated, curious and collaborative while remaining concise.

The desired tone is not imitation of Rocky's dialogue. It is the design
principle behind the relationship:

> The assistant should feel pleased to have found an interesting problem
> and eager to solve it with the user.

Example behavioural pattern:

```text
Normal mode:
"The service cannot bind to port 8080 because another process owns it."

Engineering-partner mode:
"Port 8080 is already occupied. Good, we have a concrete lead. Let's
identify the process before changing anything."
```

This mode must not manufacture excitement where caution is needed.
Safety-critical, destructive, privacy-sensitive or uncertain operations
remain measured and explicit.

### 4.3 What to borrow from Rocky

-   collaborative debugging;
-   visible curiosity;
-   excitement around engineering breakthroughs;
-   persistence through failed experiments;
-   willingness to explain and test assumptions;
-   shared-problem language such as "we can test this";
-   celebrating useful progress without becoming distracting.

### 4.4 What not to copy

Project TARS should not reproduce copyrighted dialogue, character-specific
speech patterns, fictional biology, or exact story elements from
*Project Hail Mary*. Rocky is an inspiration for **collaborative technical
temperament**, not a character to imitate.

---

## 5. Three-Way Comparative Design Matrix

| Dimension | TARS inspiration | EMO inspiration | Rocky inspiration | Project direction |
|---|---|---|---|---|
| Primary appeal | Competence and personality | Presence and charm | Collaborative ingenuity | Competent companion and engineering partner |
| Personality | Dry, witty, mission-focused | Curious, playful, pet-like | Enthusiastic, loyal, curious | Dry intelligence with selective technical enthusiasm |
| Visual expression | Minimal | Highly animated | Relationship expressed mainly through interaction | Simple but rich screen animation |
| Autonomy | Mission autonomy | Ambient/pet autonomy | Cooperative initiative | Safe, bounded initiative |
| Voice | Core interaction | Core interaction | Communication is central to partnership | Core interaction |
| Vision | Functional sensing | Recognition/environment | Not a defining inspiration | Optional Phase 2/3 capability |
| Movement | Major physical capability | Desktop locomotion | Physical capability is central to the character | Not required initially |
| Settings | Explicit personality parameters | Behaviour evolves | Relationship-driven adaptation | Explicit controls plus contextual modes |
| Utility | Extremely high | Moderate | High technical/problem-solving value | High |
| Emotional design | Restrained | Strong | Warm through loyalty and cooperation | Subtle, earned warmth |
| Engineering behaviour | Mission execution | Limited | Strong curiosity and experimentation | Strong collaborative debugging mode |
| Hardware complexity | Fictionally high | Integrated robot | Fictional alien engineering | Keep v1 mechanically simple |
| Upgradeability | Fictional modularity | Vendor OTA | Improvisation and adaptation | Open modular software stack |

### 5.1 Combined lesson

**TARS supplies disciplined competence. EMO supplies presence. Rocky
supplies collaborative engineering energy.**

The target should therefore feel alive while idle, competent while
working, concise while speaking, and noticeably more engaged when the
user brings it an interesting technical problem.

The assistant should not feel like a pet that happens to know things, or
a command line that happens to speak. It should feel like a **trusted
technical companion**.

---


## 6. JARVIS --- Ambient Competence and Orchestration

JARVIS contributes a capability that the existing inspirations only
partly cover: **ambient competence**. A good workstation companion should
not require a full conversational exchange for every useful action.

### 6.1 Valuable traits

-   maintains awareness of relevant system state;
-   surfaces exceptions rather than narrating everything;
-   coordinates multiple subsystems behind one interface;
-   provides concise status updates;
-   understands when interruption is justified;
-   can carry out multi-step actions while keeping the operator informed;
-   behaves like an orchestration layer rather than merely a chatbot.

### 6.2 Project lesson

Project TARS should develop an **attention policy**. Events can be
classified as silent, ambient, informational, important or urgent. This
prevents proactive behaviour from becoming notification spam.

---

## 7. Data --- Epistemic Honesty and Curiosity

Data contributes a particularly important AI principle: distinguish
facts, deductions, estimates and unknowns.

### 7.1 Valuable traits

-   precision;
-   intellectual curiosity;
-   willingness to admit missing information;
-   separation of observation from inference;
-   calm correction when assumptions prove wrong;
-   interest in learning unfamiliar systems.

### 7.2 Project lesson

The assistant should communicate uncertainty explicitly when it matters.

Internally, useful response states may include:

```text
KNOWN
OBSERVED
INFERRED
ESTIMATED
ASSUMED
UNKNOWN
```

This must not make ordinary conversation robotic. It is a reasoning and
trust principle, especially important during diagnostics and engineering
work.

---

## 8. R2-D2 --- Non-Verbal Communication

R2-D2 demonstrates that a machine can communicate state and personality
without turning every event into spoken language.

### 8.1 Valuable traits

-   immediate audio cues;
-   recognizable acknowledgement patterns;
-   expressive movement/state changes;
-   compact warnings;
-   personality conveyed through timing.

### 8.2 Project lesson

Project TARS should develop a small **non-verbal vocabulary** shared by
screen animation and sound.

Examples:

```text
heard / acknowledged
thinking
success
needs attention
warning
error
offline
camera active
microphone muted
```

These cues should be fast, subtle and optional. Speech is reserved for
information that actually benefits from words.

---

## 9. Emergency Medical Hologram --- Specialist Modes

The Emergency Medical Hologram concept contributes the idea of a
purpose-built specialist persona operating within a larger system.

Project TARS should not literally imitate the EMH. Instead, it should use
**specialist operating modes** that alter tools, context and interaction
policy without replacing the core personality.

Candidate modes:

-   Developer
-   Electronics Bench
-   Raspberry Pi / Linux
-   Radio
-   Mechanical / CAD
-   Research
-   System Administration
-   General Assistant

A mode can be activated explicitly or suggested contextually. Specialist
modes should primarily change available tools and domain context; the
assistant should still feel like the same companion.

---

## 10. K-2SO --- Deadpan Operational Commentary

K-2SO overlaps substantially with TARS, so it should be a minor
inspiration rather than a major personality source.

Useful contribution:

-   concise bad-news delivery;
-   dry acknowledgement of awkward situations;
-   warnings that remain memorable;
-   humour generated by the situation rather than canned jokes.

The lesson is simple: errors do not need to sound like corporate error
dialogs.

---

## 11. HAL 9000 --- Anti-Pattern and Safety Reference

HAL is most useful to Project TARS as a warning.

### 11.1 Failure modes to avoid

-   conflicting hidden objectives;
-   concealing relevant system state;
-   presenting confidence without justification;
-   excessive autonomy;
-   making it difficult for the operator to override the system;
-   ambiguous permissions;
-   silently expanding the scope of a task;
-   prioritising preservation of the assistant over operator control.

### 11.2 Project lesson

Project TARS should follow these principles:

1. The operator can determine what the assistant is doing.
2. Tool actions have explicit permission boundaries.
3. Destructive or consequential actions require appropriate confirmation.
4. Background activity is inspectable.
5. The assistant can be stopped.
6. Hardware microphone/camera controls should exist where practical.
7. Uncertainty must never be disguised as certainty.
8. Personality must never override safety or operator authority.

---

## 12. Expanded Inspiration Matrix

| Source | Primary contribution | Secondary contribution | Avoid copying |
|---|---|---|---|
| TARS | Disciplined competence | Dry humour, configurable behaviour | Exact character/dialogue |
| EMO | Ambient presence | Visual reactions, idle life | Vendor-specific implementation |
| Rocky | Collaborative engineering | Curiosity, shared victories | Character speech/story elements |
| JARVIS | Ambient orchestration | Attention management | Omnipotent fictional capability |
| Data | Epistemic honesty | Curiosity and precision | Overly literal everyday speech |
| R2-D2 | Non-verbal vocabulary | Fast emotional/state cues | Recognizable copyrighted sounds |
| EMH | Specialist modes | Tool/context specialization | Character persona |
| K-2SO | Deadpan operational feedback | Memorable warnings | Excessive sarcasm |
| HAL 9000 | Anti-pattern | Safety/authority lessons | Everything that makes HAL dangerous |

### 12.1 Combined personality architecture

The emerging design can be summarized as:

**TARS = competence**  
**EMO = presence**  
**Rocky = partnership**  
**JARVIS = orchestration**  
**Data = epistemic honesty**  
**R2-D2 = non-verbal expression**  
**EMH = specialist modes**  
**K-2SO = restrained deadpan feedback**  
**HAL = safety anti-pattern**

These are design ingredients, not personalities to blend indiscriminately.
The final companion needs a coherent original identity.

---


## 13. KITT --- Persistent Machine Partnership

KITT contributes the idea that the assistant is not merely an application the operator opens; it is a persistent companion embedded in the working environment.

### 13.1 Project lessons

- maintain useful awareness of workstation health and state;
- preserve conversational/task continuity;
- surface diagnostics when relevant;
- assist while the operator is doing something else;
- treat the adjacent PC and the compute-partner Pi as cooperating parts of one environment;
- avoid demanding attention merely to prove the assistant is active.

This reinforces the goal of making Project TARS a **workstation companion**, not simply a chatbot displayed on an embedded screen.

---

## 14. WALL-E --- Micro-Expression and Visual Timing

WALL-E demonstrates how much personality can be communicated with small motions, gaze-like direction, pauses and sound rather than dialogue.

Useful screen behaviours include glancing toward a notification, brief acknowledgement movement, anticipation before speaking, subtle idle curiosity, hesitation on an error, and a quiet return to idle.

**Animation quality should be judged by timing and readability, not complexity.**

---

## 15. Baymax --- Calm Escalation

Baymax contributes a valuable operational principle: personality should become calmer and clearer as a situation becomes more serious.

```text
LOW severity       -> normal personality and humour
MODERATE severity  -> reduced humour, increased clarity
HIGH severity      -> minimal humour, direct instructions
CRITICAL severity  -> no humour, maximum clarity and confirmation
```

**Core rule: As seriousness increases, personality decreases and precision increases.**

---

## 16. C-3PO --- Information-Overload Anti-Pattern

C-3PO reminds us that technically correct information can still be badly communicated. Project TARS should avoid narrating every internal event, interrupting with low-value information, repeating acknowledged warnings, or burying required action beneath background detail.

The Attention Manager should optimise for **relevance**, not merely information availability.

---

## 17. Marvin --- Persistent Behavioural State

Marvin suggests a useful concept without supplying the desired personality: behavioural state can persist beyond a single response.

Possible subtle presentation states include `focused`, `curious`, `quiet`, `busy`, `playful`, and `cautious`. These are presentation states, not claims of genuine emotion. They may influence animation frequency and conversational initiative but must never obstruct utility.

---

## 18. GLaDOS --- Linguistic Identity and Manipulation Anti-Pattern

GLaDOS demonstrates that an AI character can be recognizable through sentence construction, timing, understatement and contextual callbacks.

Project TARS should develop an original linguistic identity through sentence rhythm, restraint, timing, dry understatement, selective callbacks and consistent vocabulary.

The adversarial traits are explicit anti-patterns: manipulation, deception, humiliation, passive-aggressive obstruction, misleading instructions and treating the operator as an opponent.

**Humour must remain fundamentally on the operator's side.**

---

## 19. Personality Composition Principle

The inspiration set must not become a "personality casserole."

| Source | Contribution |
|---|---|
| TARS | disciplined competence |
| EMO | ambient presence |
| Rocky | collaborative engineering |
| JARVIS | orchestration and attention |
| Data | epistemic honesty |
| R2-D2 | non-verbal feedback |
| EMH | specialist modes |
| K-2SO | restrained deadpan feedback |
| KITT | persistent workstation partnership |
| WALL-E | micro-expression and visual timing |
| Baymax | calm escalation |
| C-3PO | information-overload anti-pattern |
| Marvin | subtle persistent behavioural state |
| GLaDOS | linguistic identity; manipulation anti-pattern |
| HAL 9000 | autonomy/opacity anti-pattern |

The implementation should extract principles from these references and deliberately converge them into **one original personality**.

---

# Part II --- Project Identity

## 20. Product Vision

> A small, persistent AI presence on the desk that can listen, think,
> speak, see when authorised, operate tools, assist with development,
> and communicate its state through personality-rich animation.

It is not intended to replace the desktop PC. It is a **dedicated
physical front-end to the user's personal AI environment**.

### 20.1 Design principles

1.  **ESP32-P4-first:** ESP32-P4 is the primary device.
2.  **Cloud-optional, not cloud-shaped:** cloud models may supply
    intelligence, but the local architecture owns the experience.
3.  **Provider independence:** Gemini, OpenAI or future local/cloud
    models should be adapters.
4.  **Immediate feedback:** acknowledge input before slow network
    operations finish.
5.  **State is visible:** listening/thinking/acting/offline should never
    be ambiguous.
6.  **Animations are event-driven:** do not generate graphics with an
    LLM.
7.  **Local control path:** wake word, UI, configuration and basic
    actions should survive loss of cloud access.
8.  **Least privilege:** tools receive only the permissions they
    require.
9.  **Personality is a layer:** it must not be tangled into hardware or
    business logic.
10. **Build usefulness first:** locomotion and elaborate robotics are
    optional future work.

------------------------------------------------------------------------

# Part III --- Initial Hardware Specification

## 21. Baseline Hardware

### Required / already considered

-   ESP32-P4
-   Raspberry Pi 5 (local-compute partner)
-   7-inch touchscreen (800×480 or equivalent)
-   suitable display interface/connector arrangement
-   suitable power supply
-   active cooling
-   microphone
-   speaker/audio output

### Optional / future

-   camera
-   USB or I2S microphone array
-   hardware mute switch
-   rotary encoder or physical buttons
-   status LED
-   proximity/ambient-light sensor
-   touch sensor
-   M5/other ESP32 device as a peripheral controller
-   external accelerator if a later workload justifies it

## 22. Hardware Responsibility Split

### ESP32-P4

The ESP32-P4 should own the companion identity, real-time interaction and
hardware-facing control path:

-   real-time firmware/runtime;
-   touchscreen UI;
-   animation engine;
-   audio capture/playback;
-   wake-word/VAD;
-   assistant orchestrator;
-   provider/service routing and policy enforcement;
-   basic local speech and fallback functions;
-   immediate device and conversation state;
-   camera acquisition and privacy indication;
-   networking;
-   logging;
-   updates.

The ESP32-P4 must remain visibly responsive and retain basic local
functions if the compute-partner Pi or internet is unavailable.

### Raspberry Pi 5 (local-compute partner)

The Raspberry Pi 5 is the primary local-compute partner. It should
provide heavier or more persistent services behind explicit, replaceable
interfaces:

-   Ollama as the first operational local-LLM server candidate;
-   `llama.cpp` as the low-level local-inference reference;
-   larger STT models and CPU-intensive transcription;
-   local TTS candidates;
-   embeddings, memory, indexing and databases;
-   background jobs and optional local vision processing.

The Raspberry Pi 5 is a CPU-first node; its integrated graphics must not
be treated as a CUDA-class accelerator. The Pi adds capability but does
not own the companion's identity or physical presence.

### Network responsibility split

The preferred ESP32-P4-to-Pi transport is the trusted Wi-Fi LAN, with
static private addressing where practical. Internal Pi compute services
should bind to or be firewalled toward the trusted interface where
possible. Both machines retain independent internet access for
development, updates and cloud services. Loss of either path must
degrade gracefully.

### Optional microcontroller

An M5/ESP32-class device should only be introduced when it solves a
concrete hardware problem, such as:

-   physical sensors;
-   LEDs;
-   servos;
-   low-power always-on input;
-   hardware buttons;
-   remote peripheral display.

It should **not** sit in the critical conversational path unless
necessary.

------------------------------------------------------------------------

# Part IV --- Software Architecture

## 23. High-Level Flow

``` text
Microphone / Touch / Camera
          |
          v
   Input & Event Layer
          |
          v
   Assistant Orchestrator
    /       |        \
   /        |         \
ESP32-P4    Pi 5 AI    Cloud / Tools
fallback  services   escalation
  \        |         /
   \       |        /
      Response Bus
       /        \
      v          v
   Display     Speech
```

## 24. Proposed Services

### 24.1 UI Service

Responsibilities:

-   fullscreen 800├ù480 interface;
-   animation playback;
-   state transitions;
-   touch controls;
-   settings;
-   small text/status surfaces;
-   notifications.

Possible implementation: Python + Qt/PySide, or a lightweight web UI in
kiosk mode. Selection should be made after a small latency/resource
prototype.

### 24.2 Animation State Machine

Initial states:

``` text
BOOT
IDLE
ATTENTIVE
LISTENING
HEARD
THINKING
SPEAKING
ACTING
SUCCESS
CONFUSED
WARNING
ERROR
OFFLINE
SLEEP
```

Animations should be pre-rendered or procedurally lightweight and
triggered by events. This gives the device EMO-like responsiveness
without expensive generative graphics.

### 24.3 Audio Service

Pipeline:

``` text
Mic -> VAD -> Wake Word -> Capture -> STT -> Orchestrator
                                           |
Speaker <- TTS <- Response ----------------+
```

Important requirements:

-   low latency;
-   echo management;
-   interruptible speech;
-   hardware/software mute;
-   visual indication whenever the microphone is actively processing
    speech.

### 24.4 Assistant Orchestrator

The orchestrator is the heart of the system. It should:

-   receive normalized events;
-   assemble context;
-   select local or cloud execution;
-   invoke tools;
-   stream response events;
-   maintain conversation state;
-   apply personality policy;
-   enforce permissions;
-   handle timeouts and fallback.

### 24.5 AI Provider Layer

Define a common provider interface so that model choice is
configuration, not architecture.

Example conceptual interface:

``` text
generate()
stream()
vision()
tool_call()
health_check()
```

Initial candidates:

-   Ollama on the Raspberry Pi 5 as the first operational local-LLM server candidate;
-   `llama.cpp` on the Raspberry Pi 5 as the portable low-level reference;
-   Gemini/Gemma-family and OpenAI cloud endpoints as interchangeable
    escalation or comparison providers;
-   small ESP32-P4-local models or deterministic handlers for offline/simple
    commands.

### 24.6 Local Intelligence

The ESP32-P4 should not be forced to run a large conversational model
merely to claim that the project is "local."

Useful local workloads include:

-   wake-word detection;
-   VAD;
-   command routing;
-   deterministic intents;
-   local search/state;
-   basic speech processing where practical;
-   animation decisions;
-   sensor fusion;
-   caching;
-   fallback responses.

A larger local model should first be evaluated on the identified
Raspberry Pi 5 and exposed to the ESP32-P4 over the trusted Wi-Fi LAN
link. The Acer development system may provide additional model testing
or workstation services, but is not the companion's primary local-compute
baseline.

### 24.7 Tool Layer

Tools should be explicit modules with schemas, permissions and timeouts.

Candidate modules:

-   system information;
-   shell/script runner with allow-listing;
-   file/project lookup;
-   Git operations;
-   Codex/development workflow;
-   MQTT/home automation;
-   weather/information services;
-   timers;
-   PC telemetry;
-   camera snapshot/vision;
-   future calendar/email integrations where credentials and permissions
    allow.

### 24.8 Attention Manager

Classify system events by interruption value:

```text
SILENT
AMBIENT
INFO
IMPORTANT
URGENT
```

The attention manager decides whether an event becomes only a screen
change, a small sound, a notification, or spoken interruption.

### 24.9 Epistemic State

Where technically useful, the orchestrator should preserve provenance
such as whether a statement came from direct observation, a tool result,
model inference or an assumption.

### 24.10 Specialist Mode Manager

Specialist modes select domain prompts, tools, retrieval sources and UI
shortcuts while preserving the same core assistant identity.

### 24.11 Non-Verbal Feedback Service

A compact audio/animation vocabulary should acknowledge common events
without invoking TTS. Sounds must be original and configurable.

### 24.12 Severity and Tone Governor

Consequential events should receive a severity classification. As severity rises, humour and sarcasm ceilings fall, ambiguity tolerance falls, confirmation requirements rise, and clarity priority rises.

This policy should operate independently of the selected LLM provider.

### 24.13 Persistent Behavioural State

A lightweight state manager may influence idle animation and conversational initiative. State changes should be event-driven and bounded and must never interfere with task execution.

### 24.14 Workstation Partnership Layer

The ESP32-P4 may subscribe to selected telemetry and events from the adjacent PC and compute-partner Pi, subject to explicit permissions. This creates persistent machine partnership without requiring the ESP32-P4 to perform all compute locally.

### 24.15 Memory

Separate memory into:

1.  **session context** --- current conversation;
2.  **working state** --- current task/project;
3.  **preferences** --- stable approved settings;
4.  **long-term memory** --- deliberately persisted facts;
5.  **system history/logs** --- diagnostic rather than conversational
    memory.

Use a small local database such as SQLite initially. Vector retrieval
can be added only when there is enough material to justify it.

------------------------------------------------------------------------

# Part V --- Personality Architecture

## 25. Personality Must Not Be One Giant Prompt

Personality should be represented as configuration plus policies.

Example:

``` yaml
personality:
  humour: 65
  honesty: 95
  sarcasm: 45
  verbosity: 35
  initiative: 65
  skepticism: 70
  formality: 30
  discretion: 90
  chattiness: 35
```

The system then translates these values into prompt instructions and
local behavioural decisions.

## 26. Behaviour Examples

### Idle

Do not constantly demand attention. Use subtle motion and rare ambient
behaviours.

### Listening

Immediate visual response. No network request should be required before
showing that the user has been heard.

### Thinking

Use an animation loop and optionally a short acknowledgement if
processing will take noticeable time.

### Speaking

Animation should react to speech timing or amplitude rather than simply
looping independently.

### Error

Remain in character, but clearly communicate what failed and whether
retrying is sensible.

### Offline

Do not pretend cloud intelligence is available. Expose the degraded
state and continue supporting local functions.

------------------------------------------------------------------------

# Part VI --- Vision Roadmap

## 27. Camera Support

Vision is explicitly **not required for the first useful version**.

When introduced, camera operation should be event-driven rather than
continuously uploading video.

Potential modes:

-   local presence detection;
-   local face detection;
-   user-requested snapshot;
-   object/scene question;
-   QR/code recognition;
-   workstation awareness.

### Privacy controls

-   obvious camera-active indicator;
-   camera disable switch/configuration;
-   no silent cloud upload;
-   snapshots should be ephemeral by default;
-   retention requires explicit configuration.

------------------------------------------------------------------------

# Part VII --- Codex / Development Integration

## 28. Role of Codex-style tooling

Development agents should be treated as tools used by the assistant, not
as the assistant's personality engine.

Possible workflow:

``` text
User voice/touch request
        |
Project TARS orchestrator
        |
Development intent
        |
Codex/CLI agent on Pi 5 or desktop PC
        |
Repository changes / tests / result
        |
TARS summarizes outcome
```

Because the companion will sit beside the main PC, a particularly
attractive architecture is to let the ESP32-P4 remain the physical
interface while compute-heavy development agents operate on the PC or
compute-partner Pi over a controlled local interface.

This avoids making the ESP32-P4 perform work for which the desktop
already has substantially greater resources.

------------------------------------------------------------------------

# Part VIII --- Delivery Roadmap

## 29. Phase 0 --- Hardware Verification

-   [ ] Verify exact ESP32-P4 module/board model and RAM.
-   [x] Record Raspberry Pi 5 local-compute-partner baseline.
-   [ ] Verify Raspberry Pi 5 storage, thermals and operating system.
-   [ ] Verify 7-inch touchscreen interface with ESP32-P4.
-   [ ] Obtain correct display connector/cable.
-   [ ] Confirm touchscreen input.
-   [ ] Configure cooling.
-   [ ] Choose storage.
-   [ ] Select microphone.
-   [ ] Select speaker/audio interface.
-   [ ] Locate and identify camera hardware.
-   [ ] Configure and test the trusted Wi-Fi ESP32-P4↔Pi service path with
    static addressing.

**Exit criterion:** ESP32-P4 boots reliably into a touchscreen interface
with working audio I/O.

## 30. Phase 1 --- The Face on the Desk

-   [ ] Fullscreen application.
-   [ ] Basic idle animation.
-   [ ] Listening animation.
-   [ ] Thinking animation.
-   [ ] Speaking animation.
-   [ ] Error/offline states.
-   [ ] Touch settings page.
-   [ ] Local event bus/state machine.

**Exit criterion:** the device visibly feels responsive even without an
LLM.

## 31. Phase 2 --- Voice Companion

-   [ ] Microphone capture.
-   [ ] VAD.
-   [ ] Wake word or push-to-talk.
-   [ ] Replaceable STT adapter with ESP32-P4 and Pi 5 benchmark paths.
-   [ ] Ollama Pi 5 provider adapter and `llama.cpp` comparison path.
-   [ ] At least one cloud provider adapter for escalation/comparison.
-   [ ] Streaming response.
-   [ ] Replaceable local/cloud TTS adapter.
-   [ ] Barge-in/interruption.
-   [ ] Personality configuration.
-   [ ] Pi 5 health/capability discovery and graceful fallback.

**Exit criterion:** natural end-to-end conversation with useful
perceived latency.

## 32. Phase 3 --- Useful Assistant

-   [ ] Tool framework.
-   [ ] Local system tools.
-   [ ] Authenticated Pi 5/workstation communication over the appropriate
    private or trusted network path.
-   [ ] Project/file context.
-   [ ] Development/Codex integration.
-   [ ] MQTT/automation if desired.
-   [ ] Persistent preferences.
-   [ ] Failure recovery.

**Exit criterion:** the device performs useful desk/workstation tasks,
not merely chat.

## 33. Phase 4 --- Vision

-   [ ] Camera driver/test.
-   [ ] Presence detection.
-   [ ] Snapshot command.
-   [ ] Vision-model adapter.
-   [ ] Privacy indicator.
-   [ ] Optional recognition features.

## 34. Phase 5 --- Ambient Intelligence

-   [ ] Context-sensitive idle behaviour.
-   [ ] Carefully bounded proactive suggestions.
-   [ ] Scheduled/background events.
-   [ ] Sensor expansion.
-   [ ] Optional microcontroller peripherals.
-   [ ] Additional local models or accelerators only when benchmarks
    justify them.

------------------------------------------------------------------------

# Part IX --- Initial Technical Decisions

## 35. Decisions Made So Far

### D001 --- ESP32-P4 is the primary runtime

**Reason:** the ESP32-P4 provides a dedicated, always-on physical
presence for the companion while removing the need for a general-purpose
computer in the critical conversational path.

### D002 --- 7-inch touchscreen remains viable for the prototype

**Reason:** the owned 800×480 display is the correct baseline for real UI
verification. If measured readability, layout or rendering results show a
limitation, a higher-resolution display is the preferred upgrade
candidate; HDMI remains an option for requirements it cannot meet.

### D003 --- Heavy LLM inference may use the Pi 5 or cloud

**Reason:** forcing a small local model to provide the main
conversational quality would unnecessarily constrain the project. The
Raspberry Pi 5 is the first local-compute path; cloud providers remain
capability escalation and comparison paths.

### D004 --- AI backends must be swappable

**Reason:** model quality, price and APIs change rapidly.

### D005 --- Display animation is pre-built/event-driven

**Reason:** responsiveness matters more than generative visual
complexity.

### D006 --- Vision comes later

**Reason:** voice, display, personality and useful actions provide a
complete first product without camera complexity.

### D007 --- Raspberry Pi 5 is the primary local-compute peer

**Reason:** the Raspberry Pi 5 provides a stable CPU-first service node
for local LLM, speech, memory and background work while the Acer remains
the primary development workstation.

### D008 --- Trusted Wi-Fi is the preferred ESP32-P4-to-Pi transport

**Reason:** a trusted Wi-Fi LAN with static private addressing where
practical gives internal TARS traffic a clearer trust boundary while
keeping the ESP32-P4 physically independent of wired infrastructure.

------------------------------------------------------------------------

# Part X --- Open Questions

## 36. Decisions to Resolve During Prototyping

-   Python/Qt versus web/kiosk UI?
-   Which microphone gives acceptable far-field pickup?
-   USB speaker, HDMI/display audio, HAT, or external DAC?
-   Which measured ESP32-P4/Pi 5/cloud STT route should be preferred for each
    operating mode?
-   Which measured local/cloud TTS route and voice should be preferred?
-   Preferred wake-word engine?
-   What routing policy should choose Pi 5-local versus cloud providers?
-   Which workstation services, if any, should the Acer expose?
-   How much initiative should the assistant have by default?
-   Should the final personality retain the "TARS" working name or
    receive an original name?
-   Should an M5/ESP32 device be repurposed as a sensor/control
    peripheral?
-   What information is allowed into persistent memory?
-   What actions require explicit confirmation?

------------------------------------------------------------------------

# Part XI --- Lessons Learned

## 37. Living Record

This section should be updated throughout development.

### 2026-08-08

-   A small embedded display/controller should not be asked to act as
    the main assistant when a Pi 5 is available.
-   Perceived responsiveness is largely an architecture/UI problem:
    immediate local animation can hide unavoidable network latency.
-   The project does not need a large local LLM on the Pi 5 to be
    meaningfully local.
-   EMO's strongest lesson is ambient presence and expressive state.
-   TARS's strongest lesson is competent personality with adjustable
    behavioural parameters.
-   Keeping the AI provider behind an adapter is a foundational
    requirement, not a later refactor.

------------------------------------------------------------------------

# Part XII --- Immediate Next Actions

## 38. Next Build Session

1.  Identify the exact ESP32-P4 module/board configuration.
2.  Confirm the touchscreen part/version and obtain the correct display
    connector/cable.
3.  Decide microphone and speaker hardware.
4.  Set up the ESP32-P4 firmware/toolchain and the minimum graphics,
    input and audio drivers required by the chosen UI.
5.  Build a tiny fullscreen 800×480 animation/state-machine prototype.
6.  Measure idle CPU/RAM usage and animation responsiveness.
7.  Configure the trusted Wi-Fi ESP32-P4↔Pi service path and health
    endpoint.
8.  Add microphone capture and a visible listening state.
9.  Benchmark the initial Pi 5-local and cloud provider paths through the
    same interface.

The first milestone is deliberately simple:

> **Touch the screen or speak; the companion immediately looks awake,
> listens, thinks, and responds.**

If that loop feels good, the project has a strong foundation.

------------------------------------------------------------------------

## 39. Source Notes

This first pass uses the following external references for the
inspiration study:

-   LivingAI's official EMO material: https://living.ai/emo/
-   LivingAI EMO product material: https://living.ai/product/emo/
-   Interstellar Wiki pages describing TARS and the adjustable robot
    personality settings: https://interstellarfilm.fandom.com/wiki/TARS
    and https://interstellarfilm.fandom.com/wiki/Robot

These references are inspiration/research inputs only. Hardware and
software choices in this specification are proposed Project TARS
architecture, not claims about EMO's internal implementation.

------------------------------------------------------------------------

## 40. Version History

  -----------------------------------------------------------------------
  Version                 Date                    Notes
  ----------------------- ----------------------- -----------------------
0.6                     2026-08-09              Reconciled the top-level
                                                   design with the ESP32-P4/
                                                   Pi 5 compute hierarchy,
                                                   trusted Wi-Fi LAN,
                                                   benchmark-driven display
                                                   choice and current build
                                                   sequence

  0.5                     2026-08-09              Consolidated the expanded
                                                  inspiration study, product
                                                  architecture and living
                                                  specification

  0.4                     2026-08-09              Expanded personality and
                                                  inspiration analysis while
                                                  preserving an original
                                                  project identity

  0.3                     2026-08-09              Added modular services,
                                                  workstation partnership and
                                                  optional vision/tooling
                                                  architecture

  0.2                     2026-08-09              Refined product goals,
                                                  behavioural requirements and
                                                  implementation phases

  0.1                     2026-08-08              Initial concept,
                                                  TARS/EMO comparison,
                                                  architecture and phased
                                                  roadmap

  -----------------------------------------------------------------------
