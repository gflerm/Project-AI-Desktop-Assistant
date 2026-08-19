# Project TARS --- Hardware Architecture & Inventory

**Status:** Version 0.12 --- Living Work in Progress\
**Date:** 2026-08-19\
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
ESP32-P4
        |
        +------ OPTIONAL EDGE AI NODE
        |       NVIDIA Jetson Nano
        |
        +------ LOCAL COMPUTE NODE
        |       Raspberry Pi 5
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

**The ESP32-P4 is the companion. Other computers are resources available
to the companion.**

The user should not need to think constantly about which machine is
answering.

Task routing should eventually be automatic, policy-driven and
observable.

------------------------------------------------------------------------

# 4. Node A --- ESP32-P4

## 4.1 Role

**Primary physical companion / edge controller**

The ESP32-P4 is intended to remain the always-present device attached to
the display, microphone, speaker, camera and future sensors.

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

The ESP32-P4 should not be forced to perform sustained heavy workloads
that damage responsiveness, including:

-   large LLM inference;
-   heavyweight vision inference;
-   large embedding/index jobs;
-   long software builds;
-   sustained CPU-intensive speech processing when another node is
    available.

## 4.4 Exact hardware details

  Item                 Current status
  -------------------- -------------------------------------------------
  Board                Waveshare ESP32-P4-WIFI6 Kit A (SKU 32021);
                       ESP32-P4NRW32 package
  CPU                  Dual-core RISC-V, up to 360 MHz
  Memory               32 MB in-package PSRAM (ESP32-P4NRW32)
  Primary storage      32 MB NOR flash
  Cooling              **To verify** (passive expected at 360 MHz)
  Wi-Fi                ESP32-C6 ESP-Hosted coprocessor over four-bit
                       SDIO; 2.4 GHz Wi-Fi 6
  Bluetooth            Via ESP32-C6 coprocessor **to verify**
  Display interface    MIPI-DSI and parallel RGB LCD; HDMI bridge as an
                       alternative
  Camera interface     MIPI-CSI (Kit A ships an OV5647 camera)
  Audio                Onboard ES8311 codec; speaker and microphone
  Hostname             `titanium`
  Power supply         USB-C (programming/power port) **to verify**
  OS baseline          ESP-IDF / FreeRTOS (native ESP-IDF project;
                       verified with ESP-IDF 6.0.2)

**Silicon note:** this board reports ESP32-P4 silicon revision v1.3
(pre-v3). `sdkconfig.defaults` therefore sets
`CONFIG_ESP32P4_SELECTS_REV_LESS_V3=y` and `CONFIG_ESP32P4_REV_MIN_100=y`.
Revisions 3+ require different settings.

------------------------------------------------------------------------

## 4.5 Auxiliary 1.83-inch LCD modules

The image inventory contains a reference schematic for three 1.83-inch
SPI LCD modules intended to act as the companion's left eye, right eye and
mouth displays.

**Inventory status:** Wiring design documented; exact LCD controller/model,
module quantity on hand and physical operation are **to be verified**.

![ESP32-P4 three-LCD wiring reference](../images/ESP32%20LCD%20Wiring%20Reference%20Schematic.png)

### 4.5.1 Proposed bus allocation and pin map

| Display role | SPI host | VCC | GND | MOSI / DIN | SCLK / CLK | CS | DC / A0 | Reset | Backlight |
|---|---|---|---|---|---|---|---|---|---|
| Left eye | SPI2_HOST | 3V3 | GND | GPIO42 | GPIO43 | GPIO44 | GPIO45 | GPIO19 | GPIO18 |
| Right eye | SPI3_HOST | 3V3 | GND | GPIO16 | GPIO17 | GPIO5 | GPIO4 | GPIO15 | GPIO18 |
| Mouth | SPI2_HOST | 3V3 | GND | GPIO42 | GPIO43 | GPIO2 | GPIO45 | GPIO19 | GPIO18 |

The left-eye and mouth modules share the SPI2 MOSI and clock lines, as
well as DC, reset and backlight control, but use separate chip-select lines.
The right-eye module uses SPI3. Separate chip-select lines allow the three
displays to be addressed independently, subject to driver and signal-integrity
verification.

### 4.5.2 Electrical and integration notes

- The reference specifies 3.3 V logic and recommends powering each module
  from the board's 3V3 rail.
- Backlight control may be driven with PWM for brightness control.
- The schematic labels the module connector pins, top to bottom, as VCC,
  GND, DIN, CLK, CS, DC, RST and BL.
- GPIO18 is shown as a shared backlight signal for all three modules; this
  implies common brightness control unless the wiring is revised.
- GPIO19 is shown as a shared reset for the two SPI2 modules.
- Total 3V3 current, backlight current, connector pinout, LCD controller,
  SPI mode, maximum reliable clock rate and ESP-IDF pin conflicts must be
  checked before assembly.

### 4.5.3 Verification required

- confirm the exact 1.83-inch LCD module model and controller;
- confirm all three modules use 3.3 V power and 3.3 V-tolerant logic;
- measure combined logic and backlight current against the board's 3V3
  supply capacity;
- check GPIO2, GPIO4, GPIO5, GPIO15--GPIO19 and GPIO42--GPIO45 against all
  other board peripherals and boot constraints;
- bench-test each module individually before connecting the shared SPI2 bus;
- verify independent chip selection with the left eye and mouth connected;
- test simultaneous animation, frame rate, bus contention and signal integrity;
- decide whether shared reset/backlight control is acceptable for the final
  enclosure and fault-recovery design.

------------------------------------------------------------------------


## 4.6 ESP32-P4 Firmware Baseline (ESP-IDF / FreeRTOS)

**Current baseline:** ESP-IDF / FreeRTOS.

Project TARS should run the ESP32-P4 as a purpose-built embedded appliance
rather than as a conventional Linux desktop. The ESP32-P4 is **not a Linux
host**: it runs bare-metal/RTOS firmware built with ESP-IDF and FreeRTOS.

The preferred software stack is:

```text
ESP-IDF / FreeRTOS
        |
display / touch / audio / networking drivers
        |
Project TARS embedded UI
        |
Project TARS services
        |
firmware task supervision / watchdog
```

A complete desktop environment is **not required** (and is not applicable)
on the ESP32-P4.

### 4.6.1 Why the RTOS baseline is preferred

Potential benefits:

- low idle memory use (MB-class, not GB-class);
- deterministic task scheduling and timing;
- minimal update and attack surface;
- clean boot path;
- tightly controlled resource allocation;
- appliance-style deployment;
- predictable, low-latency runtime behaviour.

### 4.6.2 Display/rendering stack decision remains open

The UI still needs a display/rendering stack.

Candidate approaches include:

- MIPI-DSI or parallel RGB LCD driven directly by the ESP32-P4;
- an HDMI bridge as an alternative display path.

The exact choice should be driven by the selected UI framework and measured
latency/stability, not ideology.

### 4.6.3 Development model

Primary development should occur on the Acer development machine.

The ESP32-P4 should be treated as a firmware build/flash target,
administered through flashing and provisioning rather than interactive
shell administration.

This reduces configuration drift and helps keep the firmware image
reproducible.

### 4.6.4 Appliance behaviour

The ESP32-P4 should eventually:

- boot directly into Project TARS;
- start required services automatically;
- restart failed tasks via watchdog/supervision;
- expose a local diagnostics path;
- allow safe shutdown/restart;
- remain operable without a conventional desktop shell.

---

# 5. Primary Display --- Raspberry Pi 7-inch Touch Display

## 5.1 Known information

A first-generation Raspberry Pi 7-inch touchscreen is currently
available and known to operate with a Raspberry Pi 4.

The display uses a dedicated display interface rather than acting as a
generic HDMI-only monitor. Driven by the ESP32-P4, it can be connected
via MIPI-DSI or parallel RGB, with an HDMI bridge as an alternative.

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
-   verify ESP32-P4 physical/electrical compatibility;
-   verify required display interface (MIPI-DSI / parallel RGB / HDMI bridge) and adapter;
-   verify touch support;
-   verify display orientation;
-   verify brightness control;
-   measure usable resolution;
-   test boot-to-UI behaviour;
-   test animation performance.

**Status:** Available; ESP32-P4 display-interface compatibility still to
be physically verified.

------------------------------------------------------------------------


## 5.4 Display Options ΓÇö Gen-1 DSI vs Touch Display 2 vs HDMI

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
| Native resolution | 800├ù480 | 720├ù1280 portrait / 1280├ù720 landscape use | Varies widely |
| Display size | 7 inch | 7 inch | Varies |
| Colour | Older panel generation | 24-bit RGB | Varies |
| Touch | Integrated | Integrated five-point multitouch | Usually USB touch; capability varies |
| ESP32-P4 interface | DSI via MIPI-DSI or parallel RGB | DSI + GPIO power via MIPI-DSI or parallel RGB | HDMI bridge as alternative; touch often via USB |
| Power | Separate display power arrangement | Powered from host board via GPIO/display cable | Usually separate panel power |
| Cabling | Compact | Compact; DSI + GPIO power | HDMI + often USB + power |
| Enclosure integration | Excellent | Excellent; slim integrated option | More connector/cable volume |
| UI pixel workload | Lowest | ~2.4├ù Gen-1 pixel count | Depends on chosen resolution |
| Text/diagnostic sharpness | Limited | Significantly improved | Potentially highest |
| Touch/UI flexibility | Good | Very good | Varies |
| Replaceability / panel choice | Limited | Limited to official panel | Excellent |
| Best Project TARS role | Initial prototype baseline | Preferred official upgrade candidate | Alternative if resolution/format needs exceed DSI options |

### 5.4.1 Touch Display 2 candidate

A concrete upgrade candidate has been identified:

**Raspberry Pi 7-inch Touch Display 2 ΓÇö 720├ù1280 native portrait resolution.**

Reference retailer supplied during design review:

`https://www.pishop.co.za/store/displays/raspberry-pi-touch-display-2-720x1280-pixel-resolution`

Official Raspberry Pi documentation confirms the 7-inch Touch Display 2
provides:

- 720├ù1280 native resolution;
- 24-bit RGB;
- five-finger multitouch;
- integrated DSI video/touch connection;
- power from the host board via the supplied GPIO/display power cable;
- interfaceable with the ESP32-P4 via MIPI-DSI or parallel RGB (HDMI bridge as an alternative);
- approximately 15 mm depth;
- 120 ├ù 189.5 mm overall dimensions;
- 87 ├ù 154.5 mm active area.

For landscape Project TARS UI design, the effective working orientation can
be treated as **1280├ù720** after rotation.

### 5.4.2 Why Touch Display 2 is attractive

Compared with the existing 800├ù480 panel, Touch Display 2 provides
substantially more usable pixels without moving to the HDMI/USB cabling
model.

Potential benefits:

- sharper text;
- more room for status overlays and diagnostics;
- richer animation assets;
- better split-screen/settings layouts;
- five-point multitouch;
- MIPI-DSI or parallel RGB interface supported by the ESP32-P4;
- cleaner enclosure integration than many HDMI touch panels;
- no separate display PSU.

This makes Touch Display 2 the **preferred official upgrade candidate** if
the existing display proves too restrictive.

### 5.4.3 Performance trade-off

The higher resolution is not free.

Approximate pixel counts:

```text
Gen-1 display:
800 ├ù 480 = 384,000 pixels

Touch Display 2:
1280 ├ù 720 = 921,600 pixels
```

Touch Display 2 therefore requires roughly **2.4 times as many pixels per
full frame** as the Gen-1 display.

This does not mean the ESP32-P4 will be slow. It means the UI benchmark
should verify that the additional visual quality is worth the additional
rendering load.

For Project TARS, animation architecture, compositor behaviour, asset
complexity and frame pacing may matter more than DSI versus HDMI alone.

### 5.4.4 Current recommendation

**Stage 1 ΓÇö Use the existing Gen-1 DSI touchscreen.**

It is already owned, has the lowest rendering workload, and is sufficient
to prove the display architecture.

**Stage 2 ΓÇö Benchmark the actual Project TARS UI.**

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

**Stage 3 ΓÇö Upgrade only if justified.**

If 800├ù480 is demonstrably restrictive, evaluate the 7-inch Touch Display 2
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

**H010 ΓÇö Existing Gen-1 DSI touchscreen remains the baseline prototype
display.**

Status: Adopted pending ESP32-P4 physical verification.

**H011 ΓÇö Display upgrades remain benchmark-driven.**

Status: Architectural requirement.

**H012 ΓÇö Raspberry Pi 7-inch Touch Display 2 is the preferred DSI upgrade
candidate.**

Status: Candidate / do not purchase until prototype benchmark.

Reason: it approximately doubles linear UI resolution while retaining
an integrated display, multitouch and compact DSI cabling.

---

# 6. Audio Hardware

## 6.1 Microphone

**Hardware:** To be selected / existing hardware to inventory.

Requirements:

-   clear near-field speech capture;
-   acceptable desk-distance capture;
-   low noise;
-   reliable ESP-IDF / ESP32-P4 driver support;
-   preferably I2S or well-supported audio interface;
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
-   acceptable ESP-IDF / ESP32-P4 driver support.

## 6.3 ESP32-P4 Audio Capabilities

The ESP32-P4 provides multiple I2S interfaces for digital audio but does
**not** include an onboard microphone, speaker, conventional analogue
microphone input, or a 3.5 mm analogue audio-output jack.

Available audio paths relevant to Project TARS include:

| Audio path | Input | Output | Project TARS relevance |
|---|---:|---:|---|
| I2S / codec hardware | Yes with suitable codec/mic | Yes with DAC/amplifier | **Preferred integrated-design candidate** |
| USB audio | Yes with supported device | Yes with supported device | **Preferred first-prototype path** |
| Bluetooth audio | Yes, device-dependent | Yes | Optional; latency/reliability must be tested |
| HDMI display audio | No | Yes, if display supports it | Convenient temporary output only |

### Prototype recommendation

Use a well-supported **I2S microphone/codec/DAC/amplifier (or supported USB
audio device) and speaker** for the first voice prototype where suitable
hardware is available.

Reasons:

- fastest path to working audio on the ESP32-P4;
- avoids over-custom electronics during software development;
- easy to replace;
- allows STT/TTS latency work to begin before enclosure/audio-board design;
- useful baseline against which an integrated audio solution can be measured.

### Integrated enclosure candidate

After the conversational voice loop is stable, finalise an **I2S-based
microphone/codec/DAC/amplifier solution** for the final enclosure.

Potential advantages:

- compact internal wiring;
- dedicated embedded audio path;
- controllable amplifier/speaker design;
- no external USB audio dongle;
- potential microphone-array integration.

The exact I2S hardware must not be selected until microphone placement,
speaker placement, echo behaviour and ESP-IDF driver support are tested.

### Bluetooth

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

A camera is believed to be available.

**Exact model / interface:** To identify. The ESP32-P4 has a MIPI-CSI
camera interface, so candidate camera hardware should be assessed against
that interface.

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
- comparison against ESP32-P4, Pi 5 and workstation vision.

With only 4 GB of RAM, it should not be assumed to be a useful host for
modern general-purpose LLM workloads.

## 8.3 Architectural value

The Nano is already owned, so it should be benchmarked before purchasing
additional vision hardware. It may provide a useful dedicated vision
service while leaving the ESP32-P4 responsive.

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
- [ ] Compare vision latency with ESP32-P4 / Pi 5 alternatives.

---

# 9. Node C --- Raspberry Pi 5 (local-compute partner)

## 9.1 Identified hardware

The local-compute node is a **Raspberry Pi 5 Model B, revision 1.0**.

The installed memory is **8 GB total RAM**.

| Item | Current information |
|---|---|
| Device | Raspberry Pi 5 Model B, revision 1.0 |
| CPU | Four-core ARM Cortex-A76, up to 2.4 GHz |
| RAM | 8 GB |
| Primary storage | Samsung 256 GB NVMe boot drive |
| Additional storage | 64 GB microSD card |
| Cooling | PWM-controlled cooling fan |
| Ethernet | Gigabit Ethernet |
| Wi-Fi | Built-in Wi-Fi |
| Bluetooth | Built-in Bluetooth |
| Hostname | `titanium` |
| Power supply | **To verify** |
| OS | Raspberry Pi OS Lite 64-bit (target baseline) |
| Status | Available; runtime verification pending |

## 9.2 Proposed role

**Primary local compute / AI service node**

This Pi 5 is well suited to work as the ESP32-P4's local compute partner.

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

The Pi 5 should be regarded primarily as a **CPU inference node**. Its
integrated graphics is useful for media/graphics acceleration but should
not be assumed to provide NVIDIA/CUDA-class AI acceleration.

## 9.3 Why it complements the ESP32-P4

The architectural split is:

```text
ESP32-P4
real-time physical interaction
display / touch / audio / wake / device state
        |
        | trusted Wi-Fi LAN
        v
PI 5
heavier local compute
LLM / STT / TTS / memory / indexing
```

The Pi 5's quad-core Cortex-A76 and 8 GB RAM make it materially better
suited than the ESP32-P4 for sustained CPU-heavy workloads while allowing
the ESP32-P4 to remain responsive.

The Pi 5 should add capability rather than become a single point of
failure.

## 9.4 Installed-state verification checklist

- [x] Record exact model: Raspberry Pi 5 Model B, revision 1.0.
- [x] Record CPU: four-core ARM Cortex-A76, up to 2.4 GHz.
- [x] Record installed RAM: 8 GB.
- [x] Record primary storage: Samsung 256 GB NVMe boot drive.
- [x] Record additional storage: 64 GB microSD card.
- [ ] Record free storage capacity.
- [ ] Verify cooling fan operation and thermal behaviour.
- [ ] Verify Ethernet controller/driver.
- [ ] Verify Wi-Fi and Bluetooth operation.
- [ ] Install/verify Raspberry Pi OS Lite 64-bit baseline.
- [ ] Benchmark sustained CPU temperature.
- [ ] Benchmark power at idle and under inference load.
- [ ] Benchmark Ollama/llama.cpp model load and token speed.
- [ ] Benchmark faster-whisper / whisper.cpp STT.
- [ ] Benchmark local TTS.
- [ ] Measure ESP32-P4↔Pi 5 network latency and throughput.

## 9.5 Initial workload guidance

The first Pi 5 benchmarks should focus on realistic small-to-medium
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

A model that fits in 8 GB but produces poor conversational latency is not
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
LEVEL 0 ΓÇö ESP32-P4
instant physical/UI/device work

LEVEL 1 ΓÇö Pi 5
local private compute and medium workloads

LEVEL 2 ΓÇö Workstation
heavy local tools / development / GPU work

LEVEL 3 ΓÇö Cloud
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
  Touch input               ESP32-P4            None
  UI animation              ESP32-P4            None
  Wake word                 ESP32-P4            Pi 5 where appropriate
  Microphone capture        ESP32-P4            None
  Local STT                 Pi 5                ESP32-P4/cloud
  Local TTS                 Pi 5 or ESP32-P4    Cloud
  Small local LLM           Pi 5                Cloud
  Large reasoning task      Cloud/workstation   Pi 5 where capable
  GPIO/sensor control       ESP32-P4            None
  Camera capture            ESP32-P4            None
  Vision inference          Pi 5/workstation    Cloud
  Embeddings                Pi 5                workstation/cloud
  Vector database           Pi 5                workstation
  Codex/development tools   Workstation         Pi 5 where appropriate
  Long build/test           Workstation         Pi 5
  Offline status/UI         ESP32-P4            None

This table is provisional and should be changed after benchmarking.

------------------------------------------------------------------------

# 14. Inter-Node Communication

Initial preference:

**Trusted Wi-Fi LAN between the ESP32-P4 and Pi 5, with static private
addressing where practical.**

Benefits:

-   low latency on a trusted LAN;
-   reliability;
-   predictable discovery;
-   better model/data transfer;
-   a single Wi-Fi path serving both the service link and development/cloud access.

Candidate communication technologies:

-   HTTP/REST for simple services;
-   WebSocket for live state;
-   MQTT for lightweight events;
-   gRPC where strongly typed high-performance RPC becomes useful;
-   SSH for administration/deployment (on Linux hosts such as the Pi 5).

Do not introduce every protocol at once.

The first prototype should favour simplicity.

------------------------------------------------------------------------

# 15. Service Discovery

The ESP32-P4 should eventually be able to determine which resources are
available.

Conceptual state:

``` text
PI 5: ONLINE
WORKSTATION: ONLINE
CLOUD: ONLINE

LOCAL_LLM: AVAILABLE ON PI 5
STT: AVAILABLE ON PI 5
CODEX_TOOLS: AVAILABLE ON WORKSTATION
VISION: AVAILABLE ON PI 5 + CLOUD
```

Discovery may initially use static configuration before automatic
discovery is implemented.

------------------------------------------------------------------------

# 16. Failure Behaviour

Distributed hardware creates failure modes that must be intentional.

## Pi 5 offline

-   ESP32-P4 continues;
-   heavy local services marked unavailable;
-   eligible work rerouted.

## Workstation offline

-   development/workstation tools disappear;
-   normal companion functions continue.

## Internet offline

-   local ESP32-P4 / Pi 5 functions continue;
-   cloud-only capabilities are clearly unavailable.

## ESP32-P4 failure

The physical companion is offline even if other compute nodes remain
available.

This is why critical configuration and project data should not exist
only on the ESP32-P4.

------------------------------------------------------------------------

# 17. Storage Strategy

Exact storage is still to be inventoried.

Possible allocation:

**ESP32-P4** - firmware/config; - UI assets; - local configuration; -
small caches; - device logs.

**Pi 5** - local models; - vector indexes; - databases; - larger
caches; - service logs.

**Workstation / repository** - source code; - master documentation; -
build artefacts; - development assets.

Backups must be defined before the system accumulates important
long-term memory.

------------------------------------------------------------------------

# 18. Power and Thermal Design

To verify:

-   ESP32-P4 power supply rating;
-   ESP32-P4 cooling solution;
-   Pi 5 power consumption;
-   whether Pi 5 should run continuously;
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
-   explicit trust relationship between ESP32-P4, Pi 5 and workstation.

Remote access from outside the local network should not be enabled
casually.

------------------------------------------------------------------------

# 20. Hardware Inventory Register

This section should become the authoritative inventory.

| ID | Hardware | Status | Intended role | Known model/details | Remaining verification |
|---|---|---|---|---|---|
| HW-001 | ESP32-P4 | Identified | Physical companion | Waveshare ESP32-P4-WIFI6 Kit A (SKU 32021); ESP32-P4NRW32; dual-core RISC-V up to 360 MHz; 32 MB PSRAM; 32 MB flash; ESP32-C6 Wi-Fi 6 coprocessor (ESP-Hosted over SDIO); MIPI-DSI / parallel RGB; MIPI-CSI (OV5647); ES8311 audio; ESP-IDF / FreeRTOS | PSU, display-interface, touch and UI benchmarks |
| HW-002 | Raspberry Pi 7-inch Touch Display Gen 1 | Available | Prototype UI | Exact revision to verify | ESP32-P4 display-interface, touch and UI benchmarks |
| HW-003 | Camera (OV5647) | Included with Kit A | Future vision | OV5647 MIPI-CSI camera included with Waveshare Kit A | Camera driver/stream tests |
| HW-004 | Raspberry Pi 5 | Available | Primary local-compute baseline | Model B Rev 1.0; 8 GB RAM; 4-core Cortex-A76 up to 2.4 GHz; Samsung 256 GB NVMe; 64 GB microSD; PWM fan; Gigabit Ethernet; Wi-Fi; Bluetooth; hostname `titanium` | PSU, OS baseline and benchmarks |
| HW-005 | Acer development system | Available | Workstation/development | i7; 32 GB RAM; NVIDIA GPU | Exact model, CPU, GPU, storage and OS |
| HW-006 | Microphone | To define | Voice input | TBD | Inventory and benchmark existing devices |
| HW-007 | Speaker | To define | Voice output | TBD | Inventory and benchmark existing devices |
| HW-008 | NVIDIA Jetson Nano | Available | Vision/edge evaluation | First-generation 4 GB class | Exact board revision and JetPack |
| HW-009 | Creality K2 Pro + CFS | Available | Enclosure fabrication | K2 Pro with CFS | Firmware and slicer workflow |

------------------------------------------------------------------------


# 20A. ESP32-P4 ↔ Pi 5 Network Architecture

## 20A.1 Design intent

The ESP32-P4 and Pi 5 communicate over the **trusted Wi-Fi LAN**. The same
trusted Wi-Fi/LAN path also carries development, cloud and internet
traffic.

```text
                    HOME LAN / INTERNET
                         Wi-Fi
                    /             \
                 ESP32-P4        PI 5
                    \               /
                     \             /
                  TRUSTED WI-FI LAN
                     TARS SERVICE PATH
```

The **trusted Wi-Fi LAN** is the preferred ESP32-P4↔Pi 5 service path.

Both nodes use the same trusted LAN for development, normal LAN access and
cloud/internet services.

## 20A.2 Wi-Fi service role

The Wi-Fi connection should carry latency-sensitive and internal TARS
traffic such as:

- STT audio/data streams;
- TTS audio/data streams;
- local LLM requests and streamed tokens;
- embeddings and memory queries;
- event/service messages;
- health checks;
- capability discovery;
- diagnostics between ESP32-P4 and Pi 5.

A normal trusted Wi-Fi LAN connection should be sufficient, with static
private addressing where practical.

## 20A.3 Static private addressing

Use static private addressing for the ESP32-P4 and Pi 5 where practical so
service discovery and routing are predictable.

Example only:

```text
ESP32-P4:  10.20.0.10/24
Pi 5:      10.20.0.20/24
```

The exact addresses may change during implementation.

Wi-Fi remains the development/cloud/internet path as well; there is no
separate dedicated wired Ethernet link between the ESP32-P4 and Pi 5.

## 20A.4 Wi-Fi / LAN role

ESP32-P4 and Pi 5 Wi-Fi should connect to the normal trusted LAN and may be
used for:

- SSH/development access from the Acer (Linux hosts such as the Pi 5);
- Git and source control;
- package/OS updates;
- model downloads;
- cloud AI inference;
- cloud STT/TTS;
- remote administration;
- normal internet access.

Cloud inference may originate directly from either ESP32-P4 or Pi 5
according to the orchestrator's routing policy.

## 20A.5 Service exposure

Where practical, Pi 5-hosted internal TARS services should be restricted to
the trusted LAN rather than being exposed broadly to the internet.

Candidate internal services include:

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

Loss of the Wi-Fi/LAN path should degrade gracefully.

```text
WI-FI / LAN FAILS
    -> attempt reconnect / policy-approved fallback
    -> preserve ESP32-P4-local companion functions

INTERNET FAILS
    -> ESP32-P4 ↔ Pi 5 trusted LAN may remain operational
    -> local STT/TTS/LLM services remain available where configured

PI 5 FAILS
    -> ESP32-P4 remains responsive
    -> use ESP32-P4-local functions and/or cloud via Wi-Fi
```

## 20A.7 Network principle

> **The trusted Wi-Fi LAN is the ESP32-P4↔Pi 5 service path; Wi-Fi is also
> the development/cloud/internet path.**

This single trusted path is intended to keep configuration simple while
maintaining latency predictability, troubleshooting clarity and resilience.

---

# 21. Hardware Benchmark Plan

Do not assign workloads based solely on specifications.

Benchmark real hardware.

## ESP32-P4

Measure:

-   boot time;
-   UI frame rate;
-   temperature;
-   idle CPU/memory;
-   wake-word latency;
-   audio latency;
-   camera performance;
-   network latency to Pi 5.

## Raspberry Pi 5

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
- network latency to ESP32-P4;
- stability under continuous camera inference.

## Workstation

Measure only what is relevant to tasks Project TARS may delegate.

------------------------------------------------------------------------

# 22. Immediate Hardware Verification Checklist

-   [ ] Record exact ESP32-P4 board/module model and revision.
-   [ ] Record ESP32-P4 CPU: dual-core RISC-V, up to 400 MHz.
-   [ ] Record ESP32-P4 memory: SRAM + PSRAM size.
-   [ ] Record ESP32-P4 flash/storage configuration.
-   [ ] Record ESP32-P4 cooling arrangement (if any).
-   [ ] Record ESP32-P4 networking: Wi-Fi/BLE via external companion RF module.
-   [ ] Record ESP32-P4 hostname: `titanium`.
-   [ ] Record ESP32-P4 power supply.
-   [x] Record ESP32-P4 board: Waveshare ESP32-P4-WIFI6 Kit A (SKU 32021).
-   [x] Record ESP32-P4 CPU: dual-core RISC-V, up to 360 MHz.
-   [x] Record ESP32-P4 memory: 32 MB in-package PSRAM.
-   [x] Record ESP32-P4 flash: 32 MB NOR flash.
-   [x] Record ESP32-P4 Wi-Fi: ESP32-C6 ESP-Hosted coprocessor over SDIO (Wi-Fi 6).
-   [x] Record ESP32-P4 audio: onboard ES8311 codec, speaker and microphone.
-   [x] Record ESP32-P4 camera: OV5647 MIPI-CSI included with Kit A.
-   [x] Record ESP32-P4 silicon revision: v1.3 (pre-v3; see sdkconfig.defaults).
-   [ ] Record ESP32-P4 PSU (USB-C).
-   [ ] Install/verify ESP-IDF / FreeRTOS baseline (ESP-IDF 6.0.2 verified).
-   [ ] Record ESP-IDF version/toolchain used for the prototype.
-   [ ] Select display interface required by the chosen UI framework (MIPI-DSI / parallel RGB / HDMI bridge).
-   [ ] Verify firmware autostart and boot into Project TARS UI.
-   [ ] Measure idle memory/CPU before and after TARS tasks start.
-   [ ] Verify task restart and watchdog recovery behaviour.
-   [ ] Identify 7-inch display revision and interface.
-   [ ] Confirm correct ESP32-P4 display-interface/connector requirements.
-   [ ] Boot display on ESP32-P4.
-   [ ] Verify correct display-interface/ribbon/cable arrangement.
-   [ ] Verify touch.
-   [ ] Benchmark display frame rate and frame-time consistency.
-   [ ] Measure touch-to-visual-response latency.
-   [ ] Record CPU load during animation.
-   [ ] Evaluate readability and brightness at normal desk distance.
-   [ ] If Gen-1 resolution is limiting, compare UI at 800├ù480 vs 1280├ù720.
-   [ ] Confirm display enclosure dimensions before any purchase.
-   [ ] Confirm display/interface power/cooling clearance with enclosure layout.
-   [ ] Identify camera model and interface (OV5647 MIPI-CSI).
-   [ ] Verify camera capture on the ESP32-P4.
-   [ ] Inventory available microphones.
-   [ ] Inventory available speakers.
-   [ ] Inventory available audio interfaces/headsets/microphones.
-   [ ] Verify I2S/USB audio capture/playback on the ESP32-P4.
-   [ ] Measure microphone-to-STT latency.
-   [ ] Measure TTS-to-speaker playback latency.
-   [ ] Test simultaneous microphone capture and speaker playback.
-   [ ] Evaluate echo/feedback with proposed physical spacing.
-   [ ] Identify candidate I2S microphone/codec/DAC/amplifier hardware only after baseline testing.
-   [x] Record exact Pi 5 model: Raspberry Pi 5 Model B, revision 1.0.
-   [x] Record Pi 5 CPU: four-core ARM Cortex-A76, up to 2.4 GHz.
-   [x] Record Pi 5 RAM: 8 GB installed.
-   [x] Record Pi 5 primary storage: Samsung 256 GB NVMe boot drive.
-   [x] Record Pi 5 additional storage: 64 GB microSD card.
-   [ ] Record Pi 5 storage devices/capacities.
-   [ ] Record Pi 5 cooling arrangement.
-   [ ] Install/verify Raspberry Pi OS Lite 64-bit baseline on the Pi 5.
-   [ ] Record relevant Windows workstation specs.
-   [ ] Confirm trusted Wi-Fi/LAN connectivity between nodes.
-   [ ] Connect ESP32-P4 and Pi 5 over the trusted Wi-Fi LAN.
-   [ ] Assign static private IP addresses where practical.
-   [ ] Measure ESP32-P4↔Pi 5 latency and sustained throughput.
-   [ ] Test streamed STT/TTS/LLM traffic over the trusted Wi-Fi LAN.
-   [ ] Verify ESP32-P4 and Pi 5 retain trusted LAN/internet access.
-   [ ] Verify Acer SSH/development access over trusted Wi-Fi/LAN.
-   [ ] Test graceful fallback if the trusted LAN is disconnected.
-   [ ] Test local ESP32-P4↔Pi 5 operation while internet is unavailable.
-   [ ] Identify exact Jetson Nano board revision and JetPack version.
-   [ ] Verify Jetson CUDA/OpenCV/TensorRT stack.
-   [ ] Identify exact Acer laptop model, i7 CPU and NVIDIA GPU.
-   [ ] Record Acer storage layout and OS.
-   [ ] Record Creality K2 Pro firmware/slicer workflow when enclosure work begins.
-   [ ] Create project image folders for hardware/enclosure photographs.

------------------------------------------------------------------------

# 23. Hardware Decision Log

## H001 --- ESP32-P4 is the physical companion

**Status:** Current direction.

The addition of more powerful computers does not move the
UI/device-control role away from the ESP32-P4.

## H002 --- Raspberry Pi 5 is the local-compute node

**Status:** Adopted for prototyping.

The Raspberry Pi 5 is the primary local-compute baseline for local
AI, speech, embeddings, databases and background services. Its services
remain optional to the ESP32-P4's basic physical-companion operation.

## H003 --- Distributed operation must degrade gracefully

**Status:** Architectural requirement.

Loss of the Pi 5, workstation or internet should reduce capability rather
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

**Status:** Adopted pending ESP32-P4 verification.

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

If the Gen-1 800├ù480 display proves limiting, evaluate Raspberry Pi
Touch Display 2 before moving to a generic HDMI panel. HDMI remains
available if resolution, size or integration requirements still are not
met.

## H013 --- ESP-IDF / FreeRTOS is the baseline runtime firmware

**Status:** Adopted for prototyping.

The ESP32-P4 should run ESP-IDF / FreeRTOS with only the display, input,
audio, networking and service components required by Project TARS.

A conventional Linux desktop is not applicable on the ESP32-P4.

## H014 --- ESP32-P4 is a firmware runtime appliance, not the primary development desktop

**Status:** Adopted.

Development should primarily occur on the Acer development machine, with
the ESP32-P4 treated as a reproducible firmware build/flash target
administered via provisioning and automated tooling.

## H015 --- I2S/USB audio is the first-prototype baseline

**Status:** Adopted for prototyping.

Where suitable existing audio hardware is available, use an I2S
microphone/codec/DAC/amplifier (or a supported USB audio device) to
establish the first reliable voice loop before committing to custom
integrated audio electronics.

## H016 --- I2S audio is the preferred integrated-design candidate

**Status:** Candidate pending acoustic and driver testing.

Evaluate I2S microphone/codec/DAC/amplifier hardware after the voice
software stack is stable. Final selection must account for echo
cancellation, microphone/speaker geometry, ESP-IDF driver support and
enclosure constraints.

## H017 --- Trusted Wi-Fi is the preferred ESP32-P4-to-Pi 5 transport

**Status:** Adopted for prototyping.

Use the trusted Wi-Fi LAN for normal internal TARS service traffic
between ESP32-P4 and Pi 5, with static private addressing where practical.

## H018 --- Trusted Wi-Fi LAN serves both the service and external paths

**Status:** Adopted for prototyping.

ESP32-P4 and Pi 5 connect over the trusted Wi-Fi LAN, which serves both
internal TARS service traffic and development/SSH access, updates, model
downloads and cloud AI inference.

## H019 --- Internal Pi 5 services should stay on the trusted LAN

**Status:** Architectural requirement.

Where practical, internal TARS APIs on the Pi 5 should bind to or firewall
toward the trusted LAN rather than being unnecessarily exposed to the
internet.

## H020 --- Raspberry Pi 5 is the primary local compute baseline

**Status:** Adopted for prototyping.

The Raspberry Pi 5 with quad-core Cortex-A76 and 8 GB RAM becomes the
baseline local compute node for Project TARS.

Its initial evaluation should prioritize local LLM serving, STT, TTS,
memory/index services and sustained CPU performance.

## H021 --- Treat Pi 5 AI workloads as CPU-first

**Status:** Architectural guidance.

The integrated graphics should not be relied upon as a CUDA-class AI
accelerator. Workload decisions should be based on measured CPU inference
performance and supported acceleration paths.

------------------------------------------------------------------------

# 24. Open Hardware Questions

-   Exact ESP32-P4 power-supply model and rating?
-   Which display interface best suits the final UI framework: MIPI-DSI, parallel RGB, or an HDMI bridge?
-   What is the minimum component set required for display, touch, audio and networking on the ESP32-P4?
-   Which OS baseline should the Pi 5 run as the local-compute node?
-   Which supported Pi 5 CPU/acceleration paths materially improve
    measured inference without harming stability?
-   Exact workstation specifications?
-   Which microphone gives acceptable desk-range capture?
-   Which speaker arrangement minimises echo?
-   Is the first-generation display satisfactory on the ESP32-P4?
-   Does 800├ù480 provide enough usable UI space after real prototype testing?
-   Would a newer DSI panel materially improve the experience?
-   Would an HDMI panel justify its extra cabling and enclosure complexity?
-   Does Touch Display 2 provide enough additional UI space to justify ~2.4├ù pixel workload?
-   Would Touch Display 2 mounting geometry improve or complicate the final enclosure?
-   Can Touch Display 2 coexist cleanly with planned cooling and any PCIe/AI accelerator hardware?
-   Is a camera physically useful in the final enclosure?
-   Should the Pi 5 remain powered continuously?
-   Is the trusted Wi-Fi LAN practical for the local nodes?
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

1.  the ESP32-P4 interface remains responsive during heavy AI work;
2.  the Pi 5 meaningfully improves local capability;
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
- accommodate ESP32-P4, display, audio and cooling cleanly;
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
| Build volume | 300 ├ù 300 ├ù 300 mm |
| Nozzles available | 0.4 mm, 0.6 mm, 0.8 mm |
| Material capability | Broad filament capability; exact validated materials to record |
| Status | Available / working |

Candidate uses:

- enclosure prototypes;
- final enclosure components;
- display bezels;
- ESP32-P4 / Pi 5 / Jetson brackets;
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
- ESP32-P4 toolchains;
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
ESP32-P4 tooling
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
  0.12                    2026-08-19              Added the image-inventory
                                                  wiring reference for the
                                                  proposed left-eye,
                                                  right-eye and mouth
                                                  1.83-inch SPI LCD modules,
                                                  including GPIO allocation,
                                                  electrical notes and
                                                  verification requirements

  0.11                    2026-08-18              Repurposed ESP32-P4 as the
                                                  primary physical companion,
                                                  Raspberry Pi 5 as the
                                                  local-compute partner, and
                                                  switched the ESP32-P4↔Pi 5
                                                  link to trusted Wi-Fi

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
