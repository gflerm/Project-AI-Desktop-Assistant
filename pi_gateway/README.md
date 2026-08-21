# Project James Pi 5 Gateway

> 🟠 **RENAME MIGRATION PENDING — 2026-08-21:** Repository source now uses the
> `james_gateway` package, `/etc/james`, `/opt/james`, `/var/lib/james`, James
> service units and the `JAM1` wire identifier. The working Pi/P4 deployment has
> deliberately not been switched yet; deploy the Pi services and flash the P4
> as one coordinated, rollback-safe change.

> 🔴 **DEPLOYMENT HOLD — 2026-08-20:** Do not change the production inference
> host while the user reviews the architecture. The intended direction is to
> retain Pi-hosted STT, TTS, tools and telemetry, demote Pi
> `qwen3:1.7b` to emergency fallback, and benchmark the existing Intel
> NUC8i5BEH as the always-on LLM host. The user's Asus GPU workstation is
> development-only and must not be an automatic route.

> **Live routing baseline — 2026-08-20:** `auto` now runs deterministic tools
> first, uses local Ollama for routine requests, sends current/complex/high-risk
> requests to Gemini, and escalates local failures after eight seconds. Focused
> Wikipedia grounding handles Gemini quota/network failure. The authenticated
> `system.status.readonly` tool reports Pi temperature, fan, load, RAM, disk,
> uptime and service health without exposing command execution or writes.

The existing Windows tester is compatible: select `auto`. The deployed suite
contains 47 passing gateway tests plus five Windows feedback/capture/replay tests.
Audio remains 16 kHz, signed 16-bit mono in both
directions. `qwen3:4b-instruct` is installed only for comparison; its Pi
benchmark was correct but too slow for the default spoken path.

This is the isolated Raspberry Pi 5 service for the Project James ESP32-P4. It
implements version 1 of `docs/P4-Pi-Audio-Protocol.md` over an authenticated
WebSocket while reusing the Pi's existing localhost-only Whisper, Piper and
Ollama engines. The default `auto` route uses deterministic tools first, local
Ollama for routine requests, and Gemini for current, complex or high-risk
requests, with bounded same-turn recovery. `gemini` and `ollama`
can also be selected explicitly for comparison, privacy, or offline testing.

Current weather uses a deterministic Open-Meteo adapter. Other freshness-
sensitive queries selectively enable Gemini Google Search grounding; ordinary
questions avoid its latency overhead. A rate-limited grounded request has an
eight-second deadline and five-minute circuit breaker, then uses a retrieved
Wikipedia result with local Ollama where possible. Local Ollama otherwise stays
explicitly offline and must not invent live data or unavailable actions.

It does not replace or modify the earlier Ember gateway. The two application
services use different directories, tokens, ports and conversation state:

| Service | Port | API |
|---|---:|---|
| Ember | 8088 | Existing multipart WAV API |
| Project James | 8090 | `/health`, `/capabilities`, `/ws/v1` |

James also owns a separate male Piper process on localhost port 5001. Ember's
existing voice service remains on port 5000.

## Pi installation

Copy this directory to the Pi and run:

```bash
sudo ./scripts/install-pi.sh
sudo ./scripts/smoke-test-pi.sh
```

The installer writes application code under `/opt/james/gateway`, creates a
private token in `/etc/james/james.env`, stores runtime data under
`/var/lib/james`, and installs `james-gateway.service`. It deliberately uses the
existing `/opt/ember/venv` Python environment and the existing local model
services during the first integration phase. It reads the existing Gemini key
from `/etc/ember/ember.env` without copying or displaying the secret. James keeps
its own provider choices and private device token in `/etc/james/james.env`.

The selected local fallback is `qwen3:1.7b` with thinking disabled. On the Pi 5
it was materially faster than `llama3.2:3b` on short spoken-assistant prompts,
while retaining the same correctness in the integration benchmark. Disabling
extended thinking avoids unnecessary latency before TTS playback.

The initial male voice is `en_GB-northern_english_male-medium`. Treat the voice
as a replaceable prototype asset and retain its model/dataset attribution and
licence information during any future distribution review.

## Windows response tester

Run `tools/Launch-James-Tester.ps1` from the repository. The native lightweight
tester uses Python's standard library plus the small `sounddevice` microphone
package supplied by the launcher. Click **Load token via SSH**, then **Check
gateway**, and select `auto`, `gemini`, or `ollama`. You can send typed text or
press and hold **Hold to talk**. Releasing the button sends 16 kHz mono PCM to
Whisper, displays its transcript, obtains the selected LLM response, and plays
the male Piper voice. The timing display reports capture, STT, LLM/tool, TTS,
and release-to-audio latency, including Pi-side processing times. The token is
masked in memory and is not written to disk.

**Personality** opens live sliders backed by private persistent Pi state. **STT
learning** manages Whisper vocabulary hints. After a recognition error, edit
the displayed transcript and click **Teach STT from edited transcript** to save
an exact and, where safe, reusable word correction. This is deterministic
adaptation, not automatic acoustic-model retraining.

The tester defaults to `auto`, records schema-v2 diagnostic sessions only while the
visible **Record private test sessions** switch is enabled, and stores those
captures locally under the repository's ignored `captures/james-sessions/`
directory. Feedback is bound to its immutable turn UUID and separates verified
speech correction from answer rating, critique, preferred answer, expected
route/tool and explicit approvals. **Flag shortcomings** can optionally teach
an approved preferred answer as a private Pi-local lesson; this is off by
default. Relevant lessons are retrieved for Ollama only and are never
included in Gemini requests. The gateway has no OpenAI/ChatGPT API route.

Explicit `remember`, `what do you remember`, and soft `forget` commands use a
separate private Pi-local memory store with cloud sharing disabled by default.
Read-only network and inference-queue endpoints expose bounded health evidence
without providing shell execution or configuration writes.

Do not copy the token into Git. Provision it into the P4's protected persistent
configuration when the Wi-Fi session is implemented.

## Authentication

HTTP diagnostics require `X-James-Token`. The WebSocket accepts either that
header or `Authorization: Bearer <token>`. The service is intended for the
trusted development LAN; TLS or an authenticated private overlay is required
before exposure outside that LAN.

## Protocol behaviour

- one session per WebSocket connection;
- one active utterance in protocol version 1;
- 16 kHz, 16-bit, mono PCM with 20 ms frames;
- strict sequence validation and contiguous acknowledgements;
- STT final text, assistant text/expression, and binary TTS PCM responses;
- bounded utterance memory and per-device bounded conversation history;
- stable error codes for stale sessions, gaps, invalid audio, and service faults.
