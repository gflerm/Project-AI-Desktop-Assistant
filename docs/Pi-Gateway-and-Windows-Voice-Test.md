# Project James — Pi Gateway and Windows Voice Test

**Status:** Deployed integration baseline

**Last verified:** 2026-08-21

> 🟠 **SOURCE RENAME READY; LIVE MIGRATION PENDING — 2026-08-21:** The repository
> now uses James package, service, configuration and storage names plus the
> `JAM1` wire identifier. The last verified Pi/P4 runtime remains on the legacy
> deployment until both ends can be changed together and rolled back safely.

> 🔴 **RUNTIME HOST DECISION PAUSED — 2026-08-20:** Continue treating this
> Windows tester and Pi gateway as the active phase-one prototype, but do not
> deploy a new inference host yet. The Pi's `qwen3:1.7b` is now an emergency
> fallback rather than the intended main conversational model. The candidate
> production split is Pi STT/TTS/tools/telemetry plus Intel NUC8i5BEH local-LLM
> inference. The user's Asus GPU workstation is manual development/test only
> and must never be selected automatically.

> 🟢 **READY FOR WINDOWS TESTING — 2026-08-20:** Select **auto** in the existing
> Windows push-to-talk tester. The deployed gateway is tools-first, local-first
> for routine prompts, cloud-first for current/complex/high-stakes prompts, and
> performs same-turn recovery. Forty-seven tests pass; no tester update is
> required.

The local response deadline is eight seconds. Local refusal, empty output,
HTTP failure or timeout escalates to Gemini. If grounded Gemini is unavailable
or returns HTTP 429, a focused Wikipedia query provides a bounded factual
fallback without another long local generation. Live checks returned real Pi
status in 466 ms and the correctly grounded incumbent-president response in
1,294 ms. Routing metadata is included in telemetry.

Cloud response capacity is 320 output tokens. The earlier 160-token limit was
raised after a correct three-incident nuclear-meltdown answer ended midway
through its Fukushima explanation. Personality prompting still asks for concise
spoken answers; the larger ceiling prevents requested multi-part answers from
being cut off.

The deployed read-only status tool reports temperature, fan RPM, PWM
percentage, cooling state, load averages, memory, disk, uptime and component
health. It reads fixed operating-system metrics and exposes no shell, command,
write, restart or control capability.

## Purpose

This document records the isolated Project James services on the Raspberry Pi 5
`titanium` and the Windows push-to-talk test workflow. It is the operational
companion to the P4-to-Pi protocol; the main project progress tracker remains
`Project-TODO-and-Verification.md`.

## Deployed service layout

| Service | Bind/port | Purpose | Isolation |
|---|---|---|---|
| `james-gateway.service` | LAN, TCP 8090 | Authenticated HTTP diagnostics/test API and `/ws/v1` P4 protocol | `/opt/james/gateway`, `/etc/james/james.env`, `/var/lib/james` |
| `piper-james.service` | localhost, TCP 5001 | James male speech synthesis | `/opt/james/models/piper` |
| Whisper Ember engine | localhost, TCP 8080 | Shared STT engine | Existing service; not modified |
| Ollama | localhost, TCP 11434 | Shared local model engine | Existing service; model choice belongs to James config |
| Ember gateway/Piper | TCP 8088 / localhost 5000 | Previous assistant | Not modified by James deployment |

The James gateway reads the existing Gemini credential environment without
copying or displaying its secret. The P4/James authentication token is separate
and is never committed.

## Conversation routing

`JAMES_LLM_PROVIDER=auto` is the currently deployed baseline, not the approved
final production-host policy:

1. route deterministic tools first for time, weather, Pi/network/inference
   status, capabilities and explicit memory operations;
2. route current, research, complex and safety-sensitive questions directly to
   `gemini-3.5-flash-lite`;
3. route routine private conversation to local `qwen3:1.7b` first, with a
   single-flight queue and an eight-second response deadline;
4. retry the same turn with Gemini when local inference refuses, times out,
   errors, or produces an empty/incomplete answer;
5. when Gemini Search is unavailable or rate-limited, use a bounded retrieved
   Wikipedia result for eligible factual questions; and
6. keep local thinking disabled and conversation history bounded to reduce
   spoken-response latency.

The Windows tester can force `gemini` or `ollama` for comparison. Normal tester
and future P4 traffic uses `auto`. Read-only tools may run automatically for an
explicit request; any future state-changing tool still requires its own
permission and confirmation policy.

When host evaluation resumes, the tester should expose explicit **Production
NUC**, **Emergency Pi**, **Development Asus**, and **Cloud** modes. Development
Asus and Cloud must be opt-in, never silent fallbacks, and the UI must display
the active host, model and local/cloud status.

Current weather uses a deterministic Open-Meteo tool with Cape Town as the
configured default and named-place geocoding. Other freshness-sensitive public
queries selectively enable Gemini Google Search grounding. General knowledge
does not pay the search latency cost. Local Ollama remains explicitly offline
unless the gateway supplies a specific retrieved fallback source.

### Initial measured evidence

| Check | Result |
|---|---|
| Gemini model lookup | HTTP 200 |
| Gemini generation | HTTP 200, exact expected response, 1.02 s |
| `llama3.2:3b` | Correct arithmetic; about 5.8 generated tokens/s on conversational prompts |
| `qwen3:1.7b` | Correct arithmetic; about 6.9–7.8 generated tokens/s on conversational prompts |
| Selected local fallback | `qwen3:1.7b`, 2,048-token runtime context, thinking disabled |

These are short integration measurements, not the final fixed-corpus benchmark.
Record full latency, thermals, RAM, accuracy, and tool-call evidence under G7.

## Personality and voice

The gateway renders the project’s original personality specification into a
provider-independent prompt. Current defaults include honesty 98%, humour 65%,
sarcasm 28%, verbosity 38%, initiative 62%, skepticism 72%, discretion 95%,
and chattiness 25%. The trust policy forbids claiming that reminders, commands,
or device actions succeeded without an explicit tool result.

The Windows tester exposes all nine profile values through **Personality**.
Changes apply to Gemini and Ollama immediately and persist privately in
`/var/lib/james/personality.json`. Humour is slightly higher than the first
baseline, but the prompt explicitly keeps wit relevant, restrained, and out of
warnings or serious situations; all other default values remain unchanged.

The initial voice is `en_GB-northern_english_male-medium`, hosted by the
separate James Piper process. It is an original male presentation direction and
must not imitate an actor or copyrighted performance. Preserve the voice model
and source-dataset attribution/licence record before distributing it.
The deployed tuning uses length scale 0.94, noise scale 0.76, and phoneme-width
noise scale 0.90 for a quicker, less flat delivery.

## STT adaptation and correction learning

Ordinary prompts do not retrain Whisper. The deployed adaptation layer instead:

- supplies a private vocabulary/context prompt to Whisper;
- lets the operator edit the last PTT transcript and click **Teach STT from
  edited transcript**;
- learns the exact utterance and reusable one-word substitutions where the
  observed and corrected word counts align;
- applies learned corrections to later transcripts; and
- persists only hints/correction mappings in
  `/var/lib/james/speech-adaptation.json`, not audio recordings.

The known loopback error `Dateway` → `Gateway` is already enrolled. Use **STT
learning** to add names and technical vocabulary. This improves recurring
recognition errors but is not acoustic speaker fine-tuning; the tone/distance/
noise corpus remains required for measured WER and command-accuracy work.

## Windows push-to-talk test

Run:

```powershell
.\tools\Launch-James-Tester.ps1
```

Then:

1. Click **Load token via SSH**. The app uses the existing `id_ed25519` key,
   masks the token, and does not store it.
2. Click **Check gateway** and require a healthy result.
3. Select `auto`, `gemini`, or `ollama`.
4. Press and hold **Hold to talk** while speaking.
5. Release the button to send the captured 16 kHz, 16-bit, mono PCM.
6. Verify the displayed Whisper transcript, James reply, and male audio playback.
7. Record the capture, STT, LLM/tool, TTS, release-to-audio, and Pi-side timings
   shown at the bottom of the tester.
8. Use **Personality** to adjust and immediately save the nine style controls.
9. After an STT mistake, correct the prompt text and click **Teach STT from
   edited transcript**; use **STT learning** to maintain vocabulary hints.

Typed prompts remain available to isolate LLM/TTS behaviour from the
microphone and STT path.

### Private diagnostic recordings

The tester now defaults to **Record private test sessions** for the requested
diagnostic phase. Each recorded turn is stored under the Git-ignored
`captures/james-sessions/<timestamp>_<turn-id>/` directory with:

- `input.wav` for PTT turns and `response.wav` for every turn;
- raw and adapted transcripts plus schema-v2 audio-verified transcript feedback;
- prompt, response text, provider/route/fallback/grounding metadata;
- capture, STT, LLM, TTS, and total timing; and
- separate answer rating, issue tags, critique, preferred answer, expected
  route/tool and regression/local-lesson approvals.

The switch is visible and can be disabled at any time. **Flag shortcomings**
records categories such as STT error, incorrect/incomplete answer, latency,
voice, pronunciation, context, personality, or misplaced humour. **Analyze
recordings** runs a completely local report covering audio level/clipping,
audio-verified WER, timings, refusals, duplicate answers, issue counts, notes, and
per-turn file locations.

Feedback is now bound to the immutable turn UUID displayed by the tester. A
speech correction requires explicit audio verification. Legacy corrections are
quarantined rather than included in WER, and the private
`captures/james-review-queue.json` contains all 60 historical turns with zero
automatic promotion to training or regression data.

### Deployed teaching and orchestration upgrade — 2026-08-21

- capability questions are answered from a live registry of enabled tools,
  providers, component health, persistent memory and inference queue state;
- compound requests are split into clauses, safe tools run independently, and
  the remaining knowledge request is composed into one answer;
- weather matching rejects code-generation and model-temperature/settings
  questions rather than routing them to Open-Meteo;
- all deterministic and model answers enter the same bounded conversation
  ledger, including numbered-item replay;
- Gemini finish reason is recorded; incomplete/max-token output receives one
  bounded continuation before TTS;
- Ollama is single-flight with active/waiting visibility and the existing
  eight-second automatic local deadline;
- explicit `remember`, `what do you remember`, and soft `forget` commands use
  `/var/lib/james/persistent-memory.json`; cloud sharing defaults off and chat
  cannot bulk-delete memory;
- `/v1/system/network` reports bounded hostname, DNS, outbound reachability and
  latency; `/v1/system/inference` reports model, active/waiting work and limit;
- nuclear accident/meltdown and radiation-safety questions route directly to
  the higher-quality cloud path.

All 47 tests passed in the Pi service environment. The live verifier proved
capabilities, weather+time composition, weather+time+model composition, the
settings/weather false-positive fix, memory remember/list/forget, network
health, queue status, rejection of unverified STT corrections, and the former
meltdown truncation case. An unnamed meltdown is now explicitly treated as
ambiguous and the final answer completed Three Mile Island, Chernobyl and
Fukushima with their dates and causes in a Gemini response with finish reason
`STOP`. Pre-upgrade source backups are retained under `/var/lib/james/backups/`.

### Private local learning

The Windows tester defaults to the `auto` route. The gateway does not contain
an OpenAI/ChatGPT API route and therefore consumes no ChatGPT API tokens.
Operator notes can be explicitly saved as Pi-local lessons. Keyword retrieval
adds relevant guidance only to Ollama system context; lesson content is never
sent to Gemini. Lessons persist in `/var/lib/james/local-lessons.json`.

This improves recurring response behaviour without silently changing model
weights. A lesson is not a tool: James still may not claim that a timer,
reminder, diagnostic, device action, or other side effect completed until the
corresponding capability is implemented and returns evidence.

### Telemetry and exports

Operational JSONL is stored on the Pi at `/var/lib/james/telemetry.jsonl`, with
three rotating backups and text/audio disabled by default. Local tools convert
an authorized private export to CSV and a Markdown analysis. The installed
Whisper endpoint currently returns only `text`; it exposes no confidence value,
so reports mark transcript confidence unavailable rather than inventing it.

## Live verification record

### Controlled ten-question acceptance — 2026-08-21

The repeatable runner `pi_gateway/scripts/run-voice-acceptance.py` exercised
ten representative requests against the deployed gateway: South African time,
Cape Town weather plus time, model-temperature settings, capability reporting,
memory remember/list/forget, the formerly truncated nuclear-meltdown question,
weather-code generation, and combined Pi/network status. Every case passed its
route and content checks, produced a complete WAV response, and survived
synthesized Whisper loopback. Long responses are transcribed in bounded chunks
below the live utterance-size limit.

| Measure | Result |
|---|---:|
| Cases passed | 10/10 |
| Average chat/tool response | 2.61 s |
| Slowest chat response | 11.63 s — cloud Python-code request |
| Average chat + TTS + STT loopback | 12.11 s |
| Slowest full loop | 35.91 s — code response playback and transcription |

The private machine-readable evidence is stored at
`captures/james-voice-acceptance-2026-08-21.json` and excluded from Git. This
proves the server-side speech path, not the operator's microphone or accent.
For the final human check, launch the Windows tester, select **auto**, and speak
the same ten prompts using PTT while recording the private session.

On 2026-08-20:

- the Pi reported Debian GNU/Linux 12 (bookworm) on AArch64;
- all 19 gateway/protocol/personality/adaptation/local-learning/test-harness
  tests passed;
- `/health` reported Whisper, Piper, Ollama, Gemini, and aggregate LLM healthy;
- both James systemd services were enabled and active;
- Piper reported `en_GB-northern_english_male-medium`;
- a real `auto` turn returned a concise James introduction;
- forced `auto` and `ollama` turns both completed through the same provider-
  independent personality and male TTS path;
- Whisper loopback recovered the substantive sentence from both synthesized
  samples, but misheard the opening proper name/phrase; add “James” pronunciation
  and keyword accuracy to the fixed STT/TTS corpus;
- the response produced a valid 207,404-byte WAV file at
  `captures/james-response-test.wav` locally (ignored by Git).
- live Cape Town weather returned through Open-Meteo in 1.64 seconds server
  time and survived TTS/Whisper loopback;
- a grounded current-leadership query completed in 3.94 seconds server time and
  survived TTS/Whisper loopback.
- privacy-safe rotating JSONL telemetry was enabled with transcript/response
  content disabled; the tester exposes aggregate count, route, provider,
  grounding, fallback, error, and timing distributions;
- warm integration measurements were approximately 1.5–1.8 s for ordinary
  Gemini chat plus speech, 1.6 s for cached current weather plus speech,
  4.1–4.6 s for Wikipedia-grounded local fallback plus speech, 1.9–2.0 s for a
  warm direct local turn, and 2.0–2.3 s for STT loopback;
- concurrent Windows-client inference produced 56–66 s queueing outliers during
  benchmarking. These are retained in telemetry and identify concurrency/load
  control as the next latency task rather than being discarded.
- the refreshed privacy-safe dataset contained 390 events: 115 chat, 110 TTS,
  82 correlated client turns, 58 STT, nine speech-correction, eight personality-
  update, five local-lesson, two speech-hint, and one deliberately verified HTTP
  error event. Total latency was 4.01 s p50 and 42.79 s p95; LLM time was 1.28 s
  p50 and 41.24 s p95, confirming that provider/model queueing—not median STT or
  TTS—is the dominant tail-latency problem.

This proves the Windows/Pi integration harness. The later physical ESP32-P4
test on 2026-08-21 also completed G2's first end-to-end BOOT-button PTT turn:
2.50 seconds of captured speech produced exact STT, a deterministic James
identity response and returned speaker audio. G5 still requires automatic VAD
endpointing, detailed timing, reconnect/failure injection and repeated turns.

## Deployment and diagnostics

Source lives under `pi_gateway/`. On the Pi:

```bash
sudo systemctl status james-gateway.service piper-james.service
sudo /home/georg/james-gateway-deploy/scripts/smoke-test-pi.sh
```

The externally reachable gateway is for the trusted development LAN. Add TLS or
an authenticated private overlay before exposure outside that boundary.
