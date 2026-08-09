# Project TARS --- Hardware Architecture & Inventory

**Status:** Version 0.10 --- Living Work in Progress\
**Date:** 2026-08-09\
**Document role:** Hardware inventory, node roles, interfaces,
constraints and hardware evolution plan\
**Companion to:** `Design-Specification.md`

------------------------------------------------------------------------

# 1. Document Status --- Living Work in Progress

This is a **living hardware specification**. It records hardware already
available, candidate hardware, intended responsibilities, interfaces,
assumptions, measurements and decisions.

Nothing in this document should be treated as a fixed bill of materials
until it has been physically verified and tested.

Hardware details should move through these states:

``` text
AVAILABLE -> IDENTIFIED -> VERIFIED -> BENCHMARKED -> ASSIGNED -> INTEGRATED
```

Where exact model numbers or capabilities are unknown, the document
should say so rather than guess.

------------------------------------------------------------------------

# 2. Hardware Goal

The hardware architecture should provide a responsive desk-resident AI
companion without forcing one small computer to perform every task.

The design favours **distributed capability**:

``` text
PHYSICAL COMPANION
Raspberry Pi 5
        |
        +------ OPTIONAL EDGE AI NODE
        |       NVIDIA Jetson Nano
        |
        +------ LOCAL COMPUTE NODE
        |       Intel NUC / Mini PC
        |
        +------ DEVELOPMENT / WORKSTATION NODE
        |       Acer i7 / NVIDIA laptop
        |
        +------ FABRICATION
        |       Creality K2 Pro + CFS
        |
        +------ CLOUD
                AI APIs / remote services
```

Each node should do the work it is best suited to perform.

The companion must degrade gracefully if another node is unavailable.

------------------------------------------------------------------------

# 3. Architectural Principle

**The Pi is the companion. Other computers are resources available to
the companion.**

The user should not need to think constantly about which machine is
answering.

Task routing should eventually be automatic, policy-driven and
observable.

------------------------------------------------------------------------

# 4. Node A --- Raspberry Pi 5

## 4.1 Role

**Primary physical companion / edge controller**

The Pi 5 is intended to remain the always-present device attached to the
display, microphone, speaker, camera and future sensors.

## 4.2 Proposed responsibilities

-   touchscreen UI;
-   animation engine;
-   visual state machine;
-   touch input;
-   microphone capture;
-   speaker output;
-   wake-word detection;
-   basic voice activity detection;
-   local event bus;
-   device state;
-   lightweight orchestration;
-   hardware control;
-   GPIO;
-   sensors;
-   camera acquisition;
-   local caching;
-   health monitoring;
-   network discovery;
-   fallback/offline UI;
-   selected lightweight AI tasks.

## 4.3 Tasks to avoid where possible

The Pi should not be forced to perform sustained heavy workloads that
damage responsiveness, including:

-   large LLM inference;
-   heavyweight vision inference;
-   large embedding/index jobs;
-   long software builds;
-   sustained CPU-intensive speech processing when another node is
    available.

## 4.4 Exact hardware details

  Item                 Current status
  -------------------- -------------------------------------------------
  Board                Raspberry Pi 5 Model B, revision 1.0
  CPU                  Four-core ARM Cortex-A76, up to 2.4 GHz
  RAM                  8 GB
  Primary storage      Samsung 256 GB NVMe boot drive
  Additional storage   64 GB microSD card
  Cooling              PWM-controlled cooling fan
  Ethernet             Gigabit Ethernet
  Wi-Fi                Built-in Wi-Fi
  Bluetooth            Built-in Bluetooth
  Hostname             `titanium`
  Power supply         **To verify**
  OS baseline          Raspberry Pi OS Lite 64-bit

------------------------------------------------------------------------


## 4.5 Raspberry Pi Operating-System Baseline

**Current baseline:** Raspberry Pi OS Lite 64-bit.

Project TARS should run the Pi as an appliance rather than as a conventional
desktop computer.

The preferred software stack is:

```text
Raspberry Pi OS Lite 64-bit
        |
minimal graphics / input / audio stack
        |
Project TARS fullscreen UI
        |
Project TARS services
        |
system service supervision / autostart
```

A complete desktop environment is **not required** for kiosk-style operation.

### 4.5.1 Why Lite is preferred

Potential benefits:

- lower idle RAM use;
- fewer background desktop processes;
- smaller update and attack surface;
- cleaner boot path;
- less competition for CPU/GPU resources;
- easier appliance-style deployment;
- more deterministic runtime environment.

### 4.5.2 Graphics-stack decision remains open

The UI still needs a display/rendering stack.

Candidate approaches include:

- a lightweight Wayland compositor plus fullscreen application;
- a minimal X/Wayland session if the selected UI framework requires it;
- direct DRM/KMS rendering where the chosen framework supports it well.

The exact choice should be driven by the selected UI framework and measured
latency/stability, not ideology.

### 4.5.3 Development model

Primary development should occur on the Acer development machine.

The Pi should be treated as a deployment/runtime target and administered
primarily through SSH and automated deployment.

This reduces configuration drift and helps keep the runtime image
reproducible.

### 4.5.4 Appliance behaviour

The Pi should eventually:

- boot directly into Project TARS;
- start required services automatically;
- restart failed services;
- expose a local diagnostics path;
- allow safe shutdown/restart;
- remain operable without a conventional desktop shell.

---

# 5. Primary Display --- Raspberry Pi 7-inch Touch Display

## 5.1 Known information

A first-generation Raspberry Pi 7-inch touchscreen is currently
available and known to operate with a Raspberry Pi 4.

The display uses the Raspberry Pi display interface rather than acting
as a generic HDMI-only monitor.

## 5.2 Intended role

The display becomes the companion's primary physical face and touch
interface.

It may show:

-   expressive animation;
-   listening/thinking/speaking states;
-   system status;
-   notifications;
-   tool progress;
-   touch controls;
-   specialist-mode indicators;
-   camera/privacy state;
-   degraded/offline state.

## 5.3 Verification required

Before committing the enclosure/UI design:

-   identify exact display revision;
-   verify Pi 5 physical/electrical compatibility;
-   verify required DSI cable/adapter;
-   verify touch support;
-   verify display orientation;
-   verify brightness control;
-   measure usable resolution;
-   test boot-to-UI behaviour;
-   test animation performance.

**Status:** Available; Pi 5 compatibility still to be physically
verified.

------------------------------------------------------------------------


## 5.4 Display Options — Gen-1 DSI vs Touch Display 2 vs HDMI

Project TARS currently has three realistic display paths:

1. keep the existing first-generation official 7-inch DSI touchscreen;
2. upgrade later to the official Raspberry Pi 7-inch Touch Display 2;
3. use a third-party HDMI touchscreen/display.

The decision should be based on integration, resolution, cabling, touch
quality, enclosure fit and measured UI behaviour rather than assuming one
interface is inherently faster.

| Area | Gen-1 Raspberry Pi 7-inch Touch Display | Raspberry Pi 7-inch Touch Display 2 | HDMI touchscreen/display |
|---|---|---|---|
| Interface | DSI | DSI + GPIO power | HDMI; touch often via USB |
| Native resolution | 800×480 | 720×1280 portrait / 1280×720 landscape use | Varies widely |
| Display size | 7 inch | 7 inch | Varies |
| Colour | Older panel generation | 24-bit RGB | Varies |
| Touch | Integrated | Integrated five-point multitouch | Usually USB touch; capability varies |
| Pi 5 compatibility | Yes with correct 22-way to 15-way FFC | Officially supported; supplied Pi 5-compatible 22-way to 15-way FFC | Yes, subject to panel/USB support |
| Power | Separate display power arrangement | Powered from host Pi via GPIO cable | Usually separate panel power |
| Cabling | Compact | Compact; DSI + GPIO power | HDMI + often USB + power |
| Enclosure integration | Excellent | Excellent; slim integrated option | More connector/cable volume |
| UI pixel workload | Lowest | ~2.4× Gen-1 pixel count | Depends on chosen resolution |
| Text/diagnostic sharpness | Limited | Significantly improved | Potentially highest |
| Touch/UI flexibility | Good | Very good | Varies |
| Replaceability / panel choice | Limited | Limited to official panel | Excellent |
| Best Project TARS role | Initial prototype baseline | Preferred official upgrade candidate | Alternative if resolution/format needs exceed DSI options |

### 5.4.1 Touch Display 2 candidate

A concrete upgrade candidate has been identified:

**Raspberry Pi 7-inch Touch Display 2 — 720×1280 native portrait resolution.**

Reference retailer supplied during design review:

`https://www.pishop.co.za/store/displays/raspberry-pi-touch-display-2-720x1280-pixel-resolution`

Official Raspberry Pi documentation confirms the 7-inch Touch Display 2
provides:

- 720×1280 native resolution;
- 24-bit RGB;
- five-finger multitouch;
- integrated DSI video/touch connection;
- power from the host Raspberry Pi via the supplied GPIO power cable;
- Raspberry Pi 5 compatibility;
- supplied 22-way to 15-way FFC for Raspberry Pi 5;
- approximately 15 mm depth;
- 120 × 189.5 mm overall dimensions;
- 87 × 154.5 mm active area.

For landscape Project TARS UI design, the effective working orientation can
be treated as **1280×720** after rotation.

### 5.4.2 Why Touch Display 2 is attractive

Compared with the existing 800×480 panel, Touch Display 2 provides
substantially more usable pixels without moving to the HDMI/USB cabling
model.

Potential benefits:

- sharper text;
- more room for status overlays and diagnostics;
- richer animation assets;
- better split-screen/settings layouts;
- five-point multitouch;
- official Pi 5 support and supplied cable;
- cleaner enclosure integration than many HDMI touch panels;
- no separate display PSU.

This makes Touch Display 2 the **preferred official upgrade candidate** if
the existing display proves too restrictive.

### 5.4.3 Performance trade-off

The higher resolution is not free.

Approximate pixel counts:

```text
Gen-1 display:
800 × 480 = 384,000 pixels

Touch Display 2:
1280 × 720 = 921,600 pixels
```

Touch Display 2 therefore requires roughly **2.4 times as many pixels per
full frame** as the Gen-1 display.

This does not mean the Pi 5 will be slow. It means the UI benchmark should
verify that the additional visual quality is worth the additional rendering
load.

For Project TARS, animation architecture, compositor behaviour, asset
complexity and frame pacing may matter more than DSI versus HDMI alone.

### 5.4.4 Current recommendation

**Stage 1 — Use the existing Gen-1 DSI touchscreen.**

It is already owned, has the lowest rendering workload, and is sufficient
to prove the display architecture.

**Stage 2 — Benchmark the actual Project TARS UI.**

Measure:

```text
frame rate
frame-time consistency
touch-to-visual-response latency
CPU utilisation
GPU utilisation
memory use
temperature
boot-to-UI time
readability at desk distance
available UI space
```

**Stage 3 — Upgrade only if justified.**

If 800×480 is demonstrably restrictive, evaluate the 7-inch Touch Display 2
before moving to an HDMI panel.

### 5.4.5 When HDMI would still win

HDMI remains preferable if Project TARS later requires:

- a substantially larger panel;
- a resolution beyond available DSI options;
- a specialist aspect ratio;
- easier interchangeability with non-Pi computers;
- a panel with superior brightness/viewing characteristics;
- an enclosure design where HDMI cabling is acceptable;
- a display feature unavailable in the official DSI range.

### 5.4.6 Display decision hierarchy

The current display decision is therefore:

```text
1. EXISTING GEN-1 DSI
      |
      | benchmark actual UI
      v
2. TOUCH DISPLAY 2 (preferred upgrade candidate)
      |
      | only if requirements still unmet
      v
3. HDMI TOUCH PANEL
```

This preserves the project's reuse-first philosophy while identifying a
clear upgrade path.

### 5.4.7 Display decisions

**H010 — Existing Gen-1 DSI touchscreen remains the baseline prototype
display.**

Status: Adopted pending Pi 5 physical verification.

**H011 — Display upgrades remain benchmark-driven.**

Status: Architectural requirement.

**H012 — Raspberry Pi 7-inch Touch Display 2 is the preferred DSI upgrade
candidate.**

Status: Candidate / do not purchase until prototype benchmark.

Reason: it approximately doubles linear UI resolution while retaining
official Pi integration, multitouch and compact DSI cabling.

---

# 6. Audio Hardware

## 6.1 Microphone

**Hardware:** To be selected / existing hardware to inventory.

Requirements:

-   clear near-field speech capture;
-   acceptable desk-distance capture;
-   low noise;
-   reliable Linux support;
-   preferably USB or well-supported audio interface;
-   suitable for echo-cancellation experiments.

Future options may include a microphone array, but this is not required
for the first prototype.

## 6.2 Speaker

**Hardware:** To be selected / existing hardware to inventory.

Requirements:

-   intelligible speech;
-   compact desktop form;
-   controllable volume;
-   low latency;
-   minimal microphone feedback;
-   acceptable Linux support.

## 6.3 Raspberry Pi 5 Audio Capabilities

The Raspberry Pi 5 provides digital audio paths but does **not** include
an onboard microphone, speaker, conventional analogue microphone input, or
3.5 mm analogue audio-output jack.

Available audio paths relevant to Project TARS include:

| Audio path | Input | Output | Project TARS relevance |
|---|---:|---:|---|
| USB audio | Yes | Yes | **Preferred first-prototype path** |
| I2S / GPIO audio hardware | Yes with suitable codec/mic | Yes with DAC/amplifier | **Preferred integrated-design candidate** |
| HDMI audio | No | Yes | Useful but not preferred for companion audio |
| Bluetooth audio | Yes, device-dependent | Yes | Optional; latency/reliability must be tested |
| HDMI display audio | No | Yes, if display supports it | Convenient temporary output only |

### Prototype recommendation

Use a well-supported **USB microphone / USB audio interface and speaker**
for the first voice prototype where suitable hardware is available.

Reasons:

- fastest path to working Linux audio;
- avoids custom electronics during software development;
- easy to replace;
- allows STT/TTS latency work to begin before enclosure/audio-board design;
- useful baseline against which an integrated audio solution can be measured.

### Integrated enclosure candidate

After the conversational voice loop is stable, evaluate an **I2S-based
microphone/codec/DAC/amplifier solution** for the final enclosure.

Potential advantages:

- compact internal wiring;
- dedicated embedded audio path;
- controllable amplifier/speaker design;
- no external USB audio dongle;
- potential microphone-array integration.

The exact I2S hardware must not be selected until microphone placement,
speaker placement, echo behaviour and Linux driver support are tested.

### HDMI and Bluetooth

HDMI audio is a valid digital output but is not the preferred Project TARS
voice path because it does not solve microphone capture and ties audio
output to the display chain.

Bluetooth should remain optional rather than the baseline because wireless
audio can add latency, codec negotiation and reconnection behaviour that is
undesirable in a low-latency conversational appliance.

---

## 6.4 Audio design issue

Full-duplex conversation may require:

-   acoustic echo cancellation;
-   careful speaker/microphone placement;
-   software echo reference;
-   push-to-talk fallback during early development.

Audio quality should be measured before blaming speech-recognition
models.

------------------------------------------------------------------------

# 7. Camera

## 7.1 Available hardware

A Raspberry Pi camera is believed to be available.

**Exact model:** To identify.

## 7.2 Intended future roles

-   user presence detection;
-   optional face/person recognition subject to privacy design;
-   object inspection;
-   electronics/workbench vision;
-   visual question answering;
-   QR/barcode reading;
-   environmental context.

## 7.3 Privacy requirement

Camera activity must be clearly visible in the UI.

A hardware privacy mechanism should be considered.

Vision is **not required for Phase 1**.

------------------------------------------------------------------------


# 8. Node B --- NVIDIA Jetson Nano

## 8.1 Known hardware

| Item | Current information |
|---|---|
| Device | NVIDIA Jetson Nano, first generation |
| CPU | Quad-core processor |
| RAM | 4 GB |
| CUDA cores | Believed to be 128; **verify exact board specification** |
| Storage | **To identify** |
| JetPack / OS | **To identify** |
| Power supply | **To identify** |
| Cooling | **To identify** |
| Status | Available; hardware reported working, detailed verification pending |

## 8.2 Proposed role

**Optional vision / CUDA edge-inference node**

The Jetson Nano should be evaluated primarily for workloads that benefit
from its NVIDIA GPU ecosystem rather than as the project's main LLM host.

Candidate responsibilities:

- CUDA-accelerated computer vision;
- OpenCV pipelines;
- TensorRT inference;
- object/person detection;
- camera preprocessing;
- selected lightweight neural-network inference;
- experimental vision services;
- comparison against Pi CPU, AI HAT candidate, NUC and workstation vision.

With only 4 GB of RAM, it should not be assumed to be a useful host for
modern general-purpose LLM workloads.

## 8.3 Architectural value

The Nano is already owned, so it should be benchmarked before purchasing
additional vision hardware. It may provide a useful dedicated vision
service while leaving the Pi responsive.

The project should avoid forcing the Jetson into the architecture merely
because it is available. Its role must be justified by measured latency,
throughput, software compatibility, power and reliability.

## 8.4 Verification checklist

- [ ] Record exact Jetson Nano board/dev-kit revision.
- [ ] Verify CPU and 128-CUDA-core specification.
- [ ] Record storage / microSD configuration.
- [ ] Record JetPack and Ubuntu versions.
- [ ] Record power supply and power mode.
- [ ] Record cooling arrangement.
- [ ] Test Ethernet/Wi-Fi connectivity as fitted.
- [ ] Verify CUDA.
- [ ] Verify OpenCV acceleration.
- [ ] Verify TensorRT.
- [ ] Benchmark representative vision model.
- [ ] Measure sustained temperature and power.
- [ ] Compare vision latency with Pi/NUC alternatives.

---

# 9. Node C --- Intel NUC / Mini PC

## 9.1 Identified hardware

The NUC has now been identified from the chassis label as:

**Intel NUC8i5BEH**  
**Product code:** BOXNUC8i5BEH  
**Regulatory model:** NUC8BEH  
**Date of manufacture:** 01/2020

The installed memory has been upgraded to **16 GB total RAM**.

| Item | Current information |
|---|---|
| Device | Intel NUC8i5BEH ("Bean Canyon") |
| Product code | BOXNUC8i5BEH |
| CPU | Intel Core i5-8259U |
| CPU generation | 8th Generation Intel Core |
| CPU topology | 4 cores / 8 threads |
| Base frequency | 2.30 GHz |
| Maximum turbo | Up to 3.80 GHz |
| Cache | 6 MB |
| TDP | 28 W |
| RAM | **16 GB installed** |
| Platform RAM support | Up to 32 GB DDR4-2400 |
| Integrated GPU | Intel Iris Plus Graphics 655 |
| GPU eDRAM | 128 MB |
| Ethernet | Intel Gigabit Ethernet |
| Wi-Fi | Intel Wireless-AC 9560, 2×2 802.11ac |
| Bluetooth | Bluetooth 5-class capability via installed wireless module |
| HDMI | HDMI 2.0a |
| USB-C / Thunderbolt | Thunderbolt 3 / USB-C |
| USB-A | Multiple USB 3.x ports |
| Storage capability | M.2 2242/2280 SSD plus 2.5-inch SATA bay in BEH chassis |
| Installed storage | **To verify** |
| Power input | 19 V DC, 4.74 A on chassis label |
| Approx. PSU class | ~90 W |
| OS | **To decide / verify installed state** |
| Status | Available; platform identified, detailed runtime verification pending |

## 9.2 Proposed role

**Primary local compute / AI service node**

This NUC is well suited to work as the Pi 5's local compute partner.

Candidate responsibilities:

- Ollama-hosted local LLMs;
- llama.cpp local model serving;
- faster-whisper / whisper.cpp STT;
- local TTS;
- embeddings;
- SQLite/PostgreSQL/vector storage where justified;
- memory services;
- document/project indexing;
- background AI jobs;
- local tool services;
- optional vision inference where CPU performance is acceptable;
- local cache for models and speech assets.

The NUC should be regarded primarily as a **CPU inference node**. Its Intel
Iris Plus Graphics 655 is useful for media/graphics acceleration but should
not be assumed to provide NVIDIA/CUDA-class AI acceleration.

## 9.3 Why it complements the Pi 5

The architectural split is:

```text
PI 5
real-time physical interaction
display / touch / audio / wake / device state
        |
        | dedicated Ethernet
        v
NUC8i5BEH
heavier local compute
LLM / STT / TTS / memory / indexing
```

The NUC's 4-core/8-thread i5 and 16 GB RAM make it materially better suited
than the Pi for sustained CPU-heavy workloads while allowing the Pi to
remain responsive.

The NUC should add capability rather than become a single point of failure.

## 9.4 Installed-state verification checklist

- [x] Identify chassis/model: Intel NUC8i5BEH.
- [x] Identify CPU family: Intel Core i5-8259U.
- [x] Record installed RAM: 16 GB total.
- [ ] Verify exact RAM module arrangement and speed.
- [ ] Identify installed M.2 SSD model/capacity.
- [ ] Identify installed 2.5-inch SATA drive, if any.
- [ ] Record free storage capacity.
- [ ] Verify BIOS version.
- [ ] Verify Ethernet controller/driver.
- [ ] Verify Wi-Fi and Bluetooth operation.
- [ ] Decide/record operating system.
- [ ] Benchmark sustained CPU temperature.
- [ ] Benchmark power at idle and under inference load.
- [ ] Benchmark Ollama/llama.cpp model load and token speed.
- [ ] Benchmark faster-whisper / whisper.cpp STT.
- [ ] Benchmark local TTS.
- [ ] Measure Pi↔NUC network latency and throughput.

## 9.5 Initial workload guidance

The first NUC benchmarks should focus on realistic small-to-medium
quantized models rather than attempting the largest model that can
technically fit in memory.

Priorities:

```text
1. responsive local LLM serving
2. STT latency
3. TTS latency
4. memory/index services
5. sustained thermals
6. power consumption
```

A model that fits in 16 GB but produces poor conversational latency is not
a useful default.

---

# 10. Node D --- Acer Development Workstation

## 10.1 Role

**User workstation / heavyweight interactive compute / development
node**

The known Acer i7 / 32 GB / NVIDIA system is the primary development
workstation. It is not merely another server; it is the machine on which
the user works. Exact model, CPU, GPU and storage remain to be recorded.

## 10.2 Candidate responsibilities

-   Codex/development-agent execution;
-   IDE integration;
-   large builds;
-   local development tools;
-   project file access;
-   GPU inference if suitable hardware exists;
-   CAD;
-   browser/application automation where explicitly authorised;
-   heavyweight vision or media processing;
-   project repository;
-   debugging and deployment.

## 10.3 Boundary

Project TARS should not silently take control of workstation
applications.

Permissions and visible tool activity remain mandatory.

------------------------------------------------------------------------

# 11. Node E --- Cloud Services

## 11.1 Role

**Elastic high-capability intelligence**

Cloud providers may supply:

-   advanced LLM reasoning;
-   multimodal models;
-   speech services;
-   web/search services;
-   specialised APIs.

## 11.2 Design requirement

Cloud is a capability tier, not the identity of the assistant.

The architecture should permit provider replacement.

Possible providers may change during development.

------------------------------------------------------------------------

# 12. Proposed Compute Hierarchy

A task router may eventually choose:

``` text
LEVEL 0 — Pi
instant physical/UI/device work

LEVEL 1 — NUC
local private compute and medium workloads

LEVEL 2 — Workstation
heavy local tools / development / GPU work

LEVEL 3 — Cloud
highest-capability remote AI/services
```

Routing criteria may include:

-   latency;
-   privacy;
-   model capability;
-   task complexity;
-   current load;
-   availability;
-   power consumption;
-   cost;
-   user preference;
-   required tool access.

------------------------------------------------------------------------

# 13. Example Task Routing

  Task                      Preferred node      Fallback
  ------------------------- ------------------- -----------------------
  Touch input               Pi                  None
  UI animation              Pi                  None
  Wake word                 Pi                  NUC where appropriate
  Microphone capture        Pi                  None
  Local STT                 NUC                 Pi/cloud
  Local TTS                 NUC or Pi           Cloud
  Small local LLM           NUC                 Cloud
  Large reasoning task      Cloud/workstation   NUC where capable
  GPIO/sensor control       Pi                  None
  Camera capture            Pi                  None
  Vision inference          NUC/workstation     Cloud
  Embeddings                NUC                 workstation/cloud
  Vector database           NUC                 workstation
  Codex/development tools   Workstation         NUC where appropriate
  Long build/test           Workstation         NUC
  Offline status/UI         Pi                  None

This table is provisional and should be changed after benchmarking.

------------------------------------------------------------------------

# 14. Inter-Node Communication

Initial preference:

**Wired Ethernet where practical.**

Benefits:

-   low latency;
-   reliability;
-   predictable discovery;
-   better model/data transfer;
-   less dependence on Wi-Fi quality.

Candidate communication technologies:

-   HTTP/REST for simple services;
-   WebSocket for live state;
-   MQTT for lightweight events;
-   gRPC where strongly typed high-performance RPC becomes useful;
-   SSH for administration/deployment.

Do not introduce every protocol at once.

The first prototype should favour simplicity.

------------------------------------------------------------------------

# 15. Service Discovery

The Pi should eventually be able to determine which resources are
available.

Conceptual state:

``` text
NUC: ONLINE
WORKSTATION: ONLINE
CLOUD: ONLINE

LOCAL_LLM: AVAILABLE ON NUC
STT: AVAILABLE ON NUC
CODEX_TOOLS: AVAILABLE ON WORKSTATION
VISION: AVAILABLE ON NUC + CLOUD
```

Discovery may initially use static configuration before automatic
discovery is implemented.

------------------------------------------------------------------------

# 16. Failure Behaviour

Distributed hardware creates failure modes that must be intentional.

## NUC offline

-   Pi continues;
-   heavy local services marked unavailable;
-   eligible work rerouted.

## Workstation offline

-   development/workstation tools disappear;
-   normal companion functions continue.

## Internet offline

-   local Pi/NUC functions continue;
-   cloud-only capabilities are clearly unavailable.

## Pi failure

The physical companion is offline even if other compute nodes remain
available.

This is why critical configuration and project data should not exist
only on the Pi.

------------------------------------------------------------------------

# 17. Storage Strategy

Exact storage is still to be inventoried.

Possible allocation:

**Pi** - OS; - UI; - local configuration; - small caches; - device logs.

**NUC** - local models; - vector indexes; - databases; - larger
caches; - service logs.

**Workstation / repository** - source code; - master documentation; -
build artefacts; - development assets.

Backups must be defined before the system accumulates important
long-term memory.

------------------------------------------------------------------------

# 18. Power and Thermal Design

To verify:

-   Pi 5 power supply rating;
-   Pi cooling solution;
-   NUC power consumption;
-   whether NUC should run continuously;
-   display power source;
-   audio hardware power;
-   cable management;
-   UPS requirement or graceful shutdown strategy.

Thermal throttling should be measured during sustained workloads.

------------------------------------------------------------------------

# 19. Network and Security

Each compute node should be treated as a separate security boundary.

Requirements:

-   authenticated service calls;
-   no unauthenticated tool execution;
-   minimal exposed ports;
-   secrets outside source control;
-   firewall rules;
-   secure administration;
-   logs for consequential remote actions;
-   explicit trust relationship between Pi, NUC and workstation.

Remote access from outside the local network should not be enabled
casually.

------------------------------------------------------------------------

# 20. Hardware Inventory Register

This section should become the authoritative inventory.

| ID | Hardware | Status | Intended role | Known model/details | Remaining verification |
|---|---|---|---|---|---|
| HW-001 | Raspberry Pi 5 | Available | Physical companion | Model B Rev 1.0; 8 GB RAM; 4-core Cortex-A76 up to 2.4 GHz; Samsung 256 GB NVMe; 64 GB microSD; PWM fan; Gigabit Ethernet; Wi-Fi; Bluetooth; hostname `titanium` | PSU |
| HW-002 | Raspberry Pi 7-inch Touch Display Gen 1 | Available | Prototype UI | Exact revision to verify | Pi 5 cable, touch and UI benchmarks |
| HW-003 | Raspberry Pi Camera | Believed available | Future vision | To identify | Locate, identify and test |
| HW-004 | Intel NUC | Available | Primary local-compute baseline | NUC8i5BEH; Core i5-8259U; 16 GB RAM | Storage, RAM layout, BIOS, OS and benchmarks |
| HW-005 | Acer development system | Available | Workstation/development | i7; 32 GB RAM; NVIDIA GPU | Exact model, CPU, GPU, storage and OS |
| HW-006 | Microphone | To define | Voice input | TBD | Inventory and benchmark existing devices |
| HW-007 | Speaker | To define | Voice output | TBD | Inventory and benchmark existing devices |
| HW-008 | NVIDIA Jetson Nano | Available | Vision/edge evaluation | First-generation 4 GB class | Exact board revision and JetPack |
| HW-009 | Creality K2 Pro + CFS | Available | Enclosure fabrication | K2 Pro with CFS | Firmware and slicer workflow |

------------------------------------------------------------------------


# 20A. Pi 5 ↔ NUC Network Architecture

## 20A.1 Design intent

Project TARS should use two logically distinct network paths:

```text
                    HOME LAN / INTERNET
                         Wi-Fi
                    /             \
                 PI 5             NUC
                   \               /
                    \             /
                     === Ethernet ===
                    PRIVATE TARS LINK
```

The **direct wired Ethernet link** is the preferred Pi-to-NUC service
backbone.

The **Wi-Fi interfaces** remain available independently for development,
normal LAN access and cloud/internet services.

## 20A.2 Direct Ethernet role

The point-to-point Ethernet connection should carry latency-sensitive and
internal TARS traffic such as:

- STT audio/data streams;
- TTS audio/data streams;
- local LLM requests and streamed tokens;
- embeddings and memory queries;
- event/service messages;
- health checks;
- capability discovery;
- diagnostics between Pi and NUC.

A normal Ethernet patch cable should be sufficient on modern
auto-MDI/MDIX interfaces.

## 20A.3 Private subnet

Use a dedicated static subnet for the point-to-point connection.

Example only:

```text
Pi 5 Ethernet:  10.20.0.1/24
NUC Ethernet:   10.20.0.2/24
```

The exact addresses may change during implementation.

**Do not configure a default gateway on this private Ethernet interface.**

This prevents normal internet traffic from accidentally preferring the
private link.

## 20A.4 Wi-Fi role

Pi 5 and NUC Wi-Fi should connect to the normal trusted LAN and may be used
for:

- SSH/development access from the Acer;
- Git and source control;
- package/OS updates;
- model downloads;
- cloud AI inference;
- cloud STT/TTS;
- remote administration;
- normal internet access.

Cloud inference may originate directly from either Pi or NUC according to
the orchestrator's routing policy.

The NUC is therefore **not required to act as the Pi's internet gateway**.

## 20A.5 Service exposure

Where practical, NUC-hosted internal TARS services should bind to the
private Ethernet interface rather than being exposed broadly on the home
LAN.

Candidate private services include:

```text
/health
/capabilities
/stt
/tts
/llm
/embeddings
/memory
```

Actual service/API structure remains a firmware/software design decision.

## 20A.6 Failure behaviour

Loss of one network path should degrade gracefully.

```text
PRIVATE ETHERNET FAILS
    -> attempt policy-approved LAN/Wi-Fi fallback
    -> preserve Pi-local companion functions

WI-FI / INTERNET FAILS
    -> Pi ↔ NUC private Ethernet remains operational
    -> local STT/TTS/LLM services remain available where configured

NUC FAILS
    -> Pi remains responsive
    -> use Pi-local functions and/or cloud via Pi Wi-Fi
```

## 20A.7 Network principle

> **Ethernet is the internal TARS backbone; Wi-Fi is the external/development path.**

This separation is intended to improve latency predictability,
troubleshooting, service isolation and resilience.

---

# 21. Hardware Benchmark Plan

Do not assign workloads based solely on specifications.

Benchmark real hardware.

## Pi 5

Measure:

-   boot time;
-   UI frame rate;
-   CPU temperature;
-   idle CPU/RAM;
-   wake-word latency;
-   audio latency;
-   camera performance;
-   network latency to NUC.

## NUC

Measure:

-   exact CPU;
-   available instruction sets;
-   RAM bandwidth/usage;
-   storage performance;
-   sustained temperature;
-   power usage;
-   candidate LLM tokens/second;
-   STT real-time factor;
-   TTS latency;
-   embedding throughput;
-   vision inference performance.

## Jetson Nano

Measure:

- CUDA/TensorRT availability;
- representative vision FPS and latency;
- CPU/GPU utilisation;
- sustained temperature;
- power consumption;
- network latency to Pi;
- stability under continuous camera inference.

## Workstation

Measure only what is relevant to tasks Project TARS may delegate.

------------------------------------------------------------------------

# 22. Immediate Hardware Verification Checklist

-   [x] Record exact Pi model: Raspberry Pi 5 Model B, revision 1.0.
-   [x] Record Pi CPU: four-core ARM Cortex-A76, up to 2.4 GHz.
-   [x] Record Pi 5 RAM size: 8 GB.
-   [x] Record Pi 5 storage: Samsung 256 GB NVMe boot drive and 64 GB microSD.
-   [x] Record Pi 5 cooling: PWM-controlled cooling fan.
-   [x] Record Pi networking: Gigabit Ethernet, built-in Wi-Fi and Bluetooth.
-   [x] Record Pi hostname: `titanium`.
-   [ ] Record Pi 5 PSU.
-   [ ] Install/verify Raspberry Pi OS Lite 64-bit baseline.
-   [ ] Record kernel/OS release used for the prototype.
-   [ ] Select minimal graphics stack required by the chosen UI framework.
-   [ ] Verify fullscreen UI autostart without conventional desktop.
-   [ ] Measure idle RAM/CPU before and after TARS services start.
-   [ ] Verify service restart and recovery behaviour.
-   [ ] Identify 7-inch display revision.
-   [ ] Confirm correct Pi 5 DSI cable/connector requirements.
-   [ ] Boot display on Pi 5.
-   [ ] Verify correct Pi 5 DSI ribbon/cable arrangement.
-   [ ] Verify touch.
-   [ ] Benchmark display frame rate and frame-time consistency.
-   [ ] Measure touch-to-visual-response latency.
-   [ ] Record CPU/GPU load during animation.
-   [ ] Evaluate readability and brightness at normal desk distance.
-   [ ] If Gen-1 resolution is limiting, compare UI at 800×480 vs 1280×720.
-   [ ] Confirm Touch Display 2 enclosure dimensions before any purchase.
-   [ ] Confirm GPIO power/cooling/HAT clearance with Touch Display 2 layout.
-   [ ] Locate Raspberry Pi camera.
-   [ ] Identify camera model.
-   [ ] Inventory available microphones.
-   [ ] Inventory available speakers.
-   [ ] Inventory available USB audio interfaces/headsets/microphones.
-   [ ] Verify USB audio capture/playback on Pi 5 OS Lite.
-   [ ] Measure USB microphone-to-STT latency.
-   [ ] Measure TTS-to-speaker playback latency.
-   [ ] Test simultaneous microphone capture and speaker playback.
-   [ ] Evaluate echo/feedback with proposed physical spacing.
-   [ ] Identify candidate I2S microphone/codec/DAC/amplifier hardware only after baseline testing.
-   [x] Record exact Intel NUC model: NUC8i5BEH.
-   [x] Record exact i5 CPU: Core i5-8259U.
-   [x] Record NUC RAM: 16 GB installed.
-   [ ] Record NUC RAM module arrangement/speed.
-   [ ] Record NUC storage devices/capacities.
-   [ ] Record NUC BIOS version.
-   [ ] Decide initial NUC operating system.
-   [ ] Record relevant Windows workstation specs.
-   [ ] Confirm wired-network options between nodes.
-   [ ] Connect Pi 5 and NUC directly by Ethernet.
-   [ ] Assign static private-link IP addresses.
-   [ ] Verify private Ethernet has no default gateway.
-   [ ] Measure Pi↔NUC latency and sustained throughput.
-   [ ] Test streamed STT/TTS/LLM traffic over private Ethernet.
-   [ ] Verify both nodes retain independent Wi-Fi internet/LAN access.
-   [ ] Verify Acer SSH/development access over trusted Wi-Fi/LAN.
-   [ ] Test graceful fallback if private Ethernet is disconnected.
-   [ ] Test local Pi↔NUC operation while Wi-Fi/internet is unavailable.
-   [ ] Identify exact Jetson Nano board revision and JetPack version.
-   [ ] Verify Jetson CUDA/OpenCV/TensorRT stack.
-   [ ] Identify exact Acer laptop model, i7 CPU and NVIDIA GPU.
-   [ ] Record Acer storage layout and OS.
-   [ ] Record Creality K2 Pro firmware/slicer workflow when enclosure work begins.
-   [ ] Create project image folders for hardware/enclosure photographs.

------------------------------------------------------------------------

# 23. Hardware Decision Log

## H001 --- Raspberry Pi 5 remains the physical companion

**Status:** Current direction.

The addition of more powerful computers does not move the
UI/device-control role away from the Pi.

## H002 --- Intel NUC is the local-compute node

**Status:** Adopted for prototyping.

The identified NUC8i5BEH is the primary local-compute baseline for local
AI, speech, embeddings, databases and background services. Its services
remain optional to the Pi's basic physical-companion operation.

## H003 --- Distributed operation must degrade gracefully

**Status:** Architectural requirement.

Loss of the NUC, workstation or internet should reduce capability rather
than unnecessarily kill the companion.

## H004 --- Benchmark before workload assignment

**Status:** Architectural requirement.

Exact routing decisions wait for real measurements.

## H005 --- Prefer existing hardware during early prototypes

**Status:** Current strategy.

Do not buy hardware merely to satisfy an untested architectural
assumption.

## H006 --- Evaluate the owned Jetson Nano before purchasing vision acceleration

**Status:** Adopted for prototyping.

The existing first-generation Jetson Nano should be tested for
CUDA/OpenCV/TensorRT vision workloads before purchasing hardware whose
role would substantially overlap.

## H007 --- Treat enclosure fabrication as an iterative engineering workstream

**Status:** Adopted.

The available large-volume 3D printer enables rapid enclosure, bracket
and jig iteration. Mechanical design should prioritise maintainability
and modular replacement.

## H008 --- New purchases require measured justification

**Status:** Project strategy.

Existing hardware should be benchmarked first. New purchases must solve a
demonstrated limitation rather than precede measurement.

## H009 --- Development environments should be reproducible

**Status:** Architectural/development requirement.

Important toolchains and versions should be documented so a development
machine can be rebuilt without relying on undocumented local state.

## H010 --- Existing DSI touchscreen is the baseline prototype display

**Status:** Adopted pending Pi 5 verification.

The first-generation 7-inch Raspberry Pi DSI touchscreen should be used
for the initial prototype before purchasing an HDMI or newer DSI panel.

A replacement display must be justified by measured limitations in
resolution, touch behaviour, visibility, enclosure fit or performance.

## H011 --- Display upgrades are benchmark-driven

**Status:** Architectural requirement.

DSI versus HDMI should not be decided on assumed interface speed alone.
Project TARS should measure actual frame timing, input latency, resource
usage and usability with the intended UI.

## H012 --- Touch Display 2 is the preferred official display upgrade candidate

**Status:** Candidate; do not purchase until prototype benchmarking.

If the Gen-1 800×480 display proves limiting, evaluate Raspberry Pi
Touch Display 2 before moving to a generic HDMI panel. HDMI remains
available if resolution, size or integration requirements still are not
met.

## H013 --- Raspberry Pi OS Lite 64-bit is the baseline runtime OS

**Status:** Adopted for prototyping.

The Pi should use Raspberry Pi OS Lite 64-bit with only the graphical,
input, audio and service components required by Project TARS.

A complete desktop environment should not be installed unless a measured
requirement later justifies it.

## H014 --- Pi is a runtime appliance, not the primary development desktop

**Status:** Adopted.

Development should primarily occur on the Acer development machine, with
the Pi treated as a reproducible deployment target administered via SSH
and automated tooling.

## H015 --- USB audio is the first-prototype baseline

**Status:** Adopted for prototyping.

Where suitable existing USB audio hardware is available, use USB
microphone/audio devices to establish the first reliable voice loop before
committing to custom integrated audio electronics.

## H016 --- I2S audio is the preferred integrated-design candidate

**Status:** Candidate pending acoustic and driver testing.

Evaluate I2S microphone/codec/DAC/amplifier hardware after the voice
software stack is stable. Final selection must account for echo
cancellation, microphone/speaker geometry, Linux support and enclosure
constraints.

## H017 --- Direct Ethernet is the preferred Pi-to-NUC transport

**Status:** Adopted for prototyping.

Use a dedicated point-to-point Ethernet subnet for normal internal TARS
service traffic between Pi 5 and NUC.

The private Ethernet interface should have static addressing and no default
internet gateway.

## H018 --- Wi-Fi remains the external and development path

**Status:** Adopted for prototyping.

Pi 5 and NUC Wi-Fi may independently provide trusted-LAN access,
development/SSH access, updates, model downloads and cloud AI inference.

Neither node must route its normal internet traffic through the other's
private Ethernet interface.

## H019 --- Internal NUC services should prefer the private interface

**Status:** Architectural requirement.

Where practical, internal TARS APIs should bind to or firewall toward the
private Pi↔NUC network rather than being unnecessarily exposed across the
general LAN.

## H020 --- NUC8i5BEH is the primary local compute baseline

**Status:** Adopted for prototyping.

The identified Intel NUC8i5BEH with Core i5-8259U and 16 GB RAM becomes
the baseline local compute node for Project TARS.

Its initial evaluation should prioritize local LLM serving, STT, TTS,
memory/index services and sustained CPU performance.

## H021 --- Treat NUC AI workloads as CPU-first

**Status:** Architectural guidance.

The integrated Intel Iris Plus Graphics 655 should not be relied upon as a
CUDA-class AI accelerator. Workload decisions should be based on measured
CPU inference performance and supported acceleration paths.

------------------------------------------------------------------------

# 24. Open Hardware Questions

-   Exact Pi 5 power-supply model and rating?
-   Which minimal graphics path best suits the final UI framework: lightweight Wayland, X/Wayland session, or direct DRM/KMS?
-   What is the minimum package set required for display, touch, audio and networking?
-   Which OS should the NUC run?
-   Which supported Intel CPU/iGPU acceleration paths materially improve
    measured NUC inference without harming stability?
-   Exact workstation specifications?
-   Which microphone gives acceptable desk-range capture?
-   Which speaker arrangement minimises echo?
-   Is the first-generation display satisfactory on Pi 5?
-   Does 800×480 provide enough usable UI space after real prototype testing?
-   Would a newer DSI panel materially improve the experience?
-   Would an HDMI panel justify its extra cabling and enclosure complexity?
-   Does Touch Display 2 provide enough additional UI space to justify ~2.4× pixel workload?
-   Would Touch Display 2 mounting geometry improve or complicate the final enclosure?
-   Can Touch Display 2 coexist cleanly with planned cooling and any PCIe/AI accelerator hardware?
-   Is a camera physically useful in the final enclosure?
-   Should the NUC remain powered continuously?
-   Is Ethernet practical for all three local nodes?
-   Will a UPS or coordinated shutdown system be worthwhile?
-   How should physical privacy controls for microphone/camera work?
-   Exact Jetson Nano board revision, JetPack version and power mode?
-   Does the Jetson materially improve vision enough to justify keeping it powered?
-   Exact Acer laptop CPU/GPU/model and storage layout?
-   Which enclosure material should be used for prototype and final revisions?
-   What internal modular mounting standard should the enclosure use?
-   Which existing hardware can be reused before any new purchase is approved?

------------------------------------------------------------------------

# 25. Hardware Success Criteria

The architecture succeeds if:

1.  the Pi interface remains responsive during heavy AI work;
2.  the NUC meaningfully improves local capability;
3.  the system automatically survives loss of optional compute nodes;
4.  the user does not need to manually select a machine for ordinary
    tasks;
5.  consequential routing/tool activity remains inspectable;
6.  local processing is preferred where it provides adequate capability
    and meaningful privacy/latency benefit;
7.  cloud capability remains available when local hardware is
    insufficient;
8.  hardware can be replaced without redesigning the personality or
    entire software stack.

------------------------------------------------------------------------


# 26. Enclosure, Fabrication & Development Tools

## 26.1 Enclosure workstream

The physical enclosure is part of the hardware architecture and should
be treated as a replaceable, serviceable subsystem rather than decoration.

Design goals:

- original appearance;
- accommodate Pi, display, audio and cooling cleanly;
- provide access to serviceable components;
- permit camera and sensor additions;
- manage cables and strain relief;
- preserve ventilation;
- provide physical microphone/camera privacy controls where practical;
- allow modules to be upgraded without reprinting the entire enclosure;
- use iterative prototypes before committing to a final shell.

**Maintainability-first rule:** prefer modular brackets, panels and
replaceable subassemblies over a single monolithic print.

## 26.2 Creality K2 Pro with CFS

**Role:** Primary additive-manufacturing / enclosure fabrication tool.

| Item | Current information |
|---|---|
| Printer | Creality K2 Pro |
| Material system | CFS |
| Build volume | 300 × 300 × 300 mm |
| Nozzles available | 0.4 mm, 0.6 mm, 0.8 mm |
| Material capability | Broad filament capability; exact validated materials to record |
| Status | Available / working |

Candidate uses:

- enclosure prototypes;
- final enclosure components;
- display bezels;
- Pi/NUC/Jetson brackets;
- camera mounts;
- speaker and microphone mounts;
- cable guides;
- sensor brackets;
- test jigs;
- service panels.

For each enclosure revision, retain where practical:

```text
CAD source
STL/3MF export
slicer project
material
nozzle
layer height
print time
mass
revision
fit/test notes
photos
```

## 26.3 Hardware photography

Hardware photographs should be included in this Markdown document as the
inventory is verified.

Recommended image types:

- overall device;
- manufacturer/model label;
- relevant connectors;
- internal layout where useful;
- power-supply label;
- cooling arrangement;
- wiring;
- enclosure prototype revisions.

Use a project-relative image structure such as:

```text
images/hardware/
images/enclosure/
images/wiring/
```

Avoid publishing sensitive serial numbers, credentials or other
unnecessary identifiers.

---

# 27. Development Workstation / Tooling Node

## 27.1 Acer development PC / laptop

**Role:** Primary development, CAD, fabrication preparation and project
engineering workstation.

| Item | Current information |
|---|---|
| Manufacturer | Acer |
| Exact model | **To identify** |
| CPU | Intel Core i7, reported 20-core; exact model/topology to verify |
| RAM | 32 GB |
| GPU | NVIDIA GPU, 4 GB VRAM; exact model to identify |
| Storage | Approximately 1.5 TB total; layout to verify |
| USB-C | Available |
| USB-A | Available |
| HDMI | Available |
| Ethernet | Available |
| Wi-Fi | Available |
| Status | Available / working |

Candidate responsibilities:

- source-code development;
- Codex and development-agent workflows;
- Git/repository work;
- documentation;
- CAD;
- 3D slicing;
- Pi toolchains;
- Jetson toolchains;
- remote administration;
- build/test work;
- backups;
- model and service experimentation where hardware permits.

## 27.2 Reproducible development environment

The development machine should eventually have a reproducible environment
record containing versions/configuration for relevant tools such as:

```text
Operating system
Git
Python
IDE/editor
Docker/container runtime
Pi tooling
Jetson tooling
CUDA (where applicable)
CAD software
Slicer
SSH configuration
Project build/test dependencies
```

**Development principle:** every important development machine should be
rebuildable from documented configuration rather than relying on an
accidental collection of installed software.

---

# 28. Version History

  -----------------------------------------------------------------------
  Version                 Date                    Notes
  ----------------------- ----------------------- -----------------------
  0.10                    2026-08-09              Recorded confirmed Pi 5
                                                  Model B Rev 1.0 hardware,
                                                  8 GB RAM, Cortex-A76 CPU,
                                                  NVMe/microSD storage,
                                                  PWM fan, Ethernet, Wi-Fi,
                                                  Bluetooth and hostname

  0.9                     2026-08-09              Reconciled the authoritative
                                                  inventory, Acer identity,
                                                  completed NUC facts,
                                                  decision ordering and
                                                  section numbering

  0.8                     2026-08-09              Identified Intel NUC8i5BEH,
                                                  Core i5-8259U, 16 GB RAM,
                                                  platform I/O/network/storage
                                                  capability; added NUC
                                                  verification and H020-H021

  0.7                     2026-08-09              Added dedicated Pi 5↔NUC
                                                  point-to-point Ethernet
                                                  backbone, independent Wi-Fi
                                                  dev/cloud path, network
                                                  fallback and H017-H019

  0.6                     2026-08-09              Documented Raspberry Pi 5
                                                  digital audio capabilities,
                                                  USB prototype baseline,
                                                  I2S integrated-audio
                                                  candidate and H015-H016

  0.5                     2026-08-09              Adopted Raspberry Pi OS Lite
                                                  64-bit baseline, minimal
                                                  graphics stack, appliance
                                                  boot/autostart model and
                                                  decisions H013-H014

  0.4                     2026-08-09              Added Raspberry Pi 7-inch
                                                  Touch Display 2 as preferred
                                                  DSI upgrade candidate;
                                                  expanded Gen-1 vs Display 2
                                                  vs HDMI comparison and H012

  0.3                     2026-08-09              Added DSI vs HDMI display
                                                  comparison, baseline DSI
                                                  recommendation, performance
                                                  benchmark criteria and
                                                  decisions H010-H011

  0.2                     2026-08-09              Added owned Jetson Nano,
                                                  Creality K2 Pro + CFS,
                                                  Acer development laptop,
                                                  enclosure/fabrication
                                                  workstream, hardware photo
                                                  policy and reuse-first
                                                  decisions H006-H009

  0.1                     2026-08-09              Initial living hardware
                                                  architecture and
                                                  inventory; Pi 5, 7-inch
                                                  display, camera, i5/16
                                                  GB Intel NUC,
                                                  workstation and cloud
                                                  compute hierarchy

  -----------------------------------------------------------------------
