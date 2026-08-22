# Project James — P4-to-Pi Audio Protocol

**Status:** Version 0.4 — James/JAM1 deployment and physical PTT round trip verified

**Date:** 2026-08-22

**Scope:** Reliable utterance transport between the ESP32-P4 and Raspberry Pi 5

> 🟢 **JAMES/JAM1 DEPLOYED — 2026-08-22:** The matching James Pi services and P4
> firmware are live. The coordinated deployment passed the Pi test suite and a
> fresh physical BOOT-button voice round trip; the previous services remain
> disabled and retained for rollback.

> 🟢 **PHYSICAL INTEGRATION RESUMED — 2026-08-21:** The first P4 client uses
> GPIO35 BOOT as active-low push-to-talk, the onboard microphone and the
> attached speaker. Camera, displays and automatic VAD are intentionally absent
> from this bounded test. The Windows client remains a diagnostic fallback.

---

# 1. Purpose

The P4 owns microphone capture, bounded buffering, primary VAD endpointing and
the visible interaction state. The Pi 5 owns speech-to-text, speaker
verification, LLM orchestration and text-to-speech generation. This contract
keeps those responsibilities testable independently and prevents network stalls
from blocking the P4 audio task.

The first implementation should use one authenticated WebSocket connection over
the trusted LAN. UTF-8 JSON text messages carry control and results; binary
messages carry PCM audio. TLS or an authenticated private overlay is required
before using the protocol outside the trusted development LAN.

# 2. Audio Format

Version 1 accepts one capture format:

| Field | Value |
|---|---|
| Encoding | Signed PCM, little-endian |
| Sample rate | 16,000 Hz |
| Sample width | 16 bits |
| Channels | 1 (mono) |
| Firmware frame | 20 ms / 320 samples / 640 PCM bytes |

No container header is sent in the live stream. A receiver may construct a WAV
header after `audio.end` using the declared format and received byte count.

# 3. Session and Turn Sequence

```text
P4                                      Pi 5
 |--- hello ---------------------------->|
 |<-- hello.ack -------------------------|
 |--- audio.start (utterance_id) -------->|
 |--- binary audio chunks, seq 0..N ---->|
 |--- audio.end (reason, counters) ------>|
 |<-- stt.partial (optional) ------------|
 |<-- stt.final -------------------------|
 |<-- assistant.text --------------------|
 |<-- tts.start -------------------------|
 |<-- binary TTS audio / URL ------------|
 |<-- tts.end ---------------------------|
```

Only one user utterance is active in version 1. `session_id` changes after a P4
boot or explicit reconnect. `utterance_id` increases monotonically within that
session. The Pi must reject stale audio from an older session.

# 4. Control Messages

Every JSON message contains `v`, `type`, `session_id`, and `message_id`.
Timestamps are monotonic microseconds since P4 boot unless named `utc_*`.

```json
{
  "v": 1,
  "type": "audio.start",
  "session_id": "7f31c9a2",
  "message_id": 18,
  "utterance_id": 4,
  "timestamp_us": 28400210,
  "sample_rate_hz": 16000,
  "sample_bits": 16,
  "channels": 1,
  "preroll_frames": 25
}
```

Required P4-to-Pi types:

- `hello`: firmware/protocol version, device ID and supported audio formats;
- `audio.start`: opens one utterance before its first binary chunk;
- `audio.end`: supplies `end_reason`, last sequence, frame count, dropped-frame
  count and capture timestamps;
- `audio.cancel`: abandons a turn after user cancellation, overrun or reset;
- `ping`: connection-health probe.

Required Pi-to-P4 types:

- `hello.ack`: selected protocol/audio format and Pi capability flags;
- `ack`: highest contiguous accepted audio sequence;
- `stt.partial` and `stt.final`: transcript updates for an utterance;
- `assistant.text`: final response text used by state and display logic;
- `tts.start` and `tts.end`: playback boundaries and audio metadata;
- `error`: stable error code, related message/utterance and retry guidance;
- `pong`: health response.

Valid `audio.end.end_reason` values are `silence`, `maximum_utterance`,
`push_to_talk_release`, and `cancelled`. An overrun uses `audio.cancel` with
reason `capture_overrun` because incomplete speech must not silently reach STT.

# 5. Binary Audio Chunk

Each WebSocket binary message begins with a fixed 24-byte, network-byte-order
header, followed by PCM bytes:

| Offset | Size | Field | Meaning |
|---:|---:|---|---|
| 0 | 4 | magic | ASCII `JAM1` |
| 4 | 1 | version | `1` |
| 5 | 1 | kind | `1` = microphone PCM, `2` = TTS PCM |
| 6 | 2 | header_bytes | `24` |
| 8 | 4 | utterance_id | Active turn identifier |
| 12 | 4 | sequence | Starts at zero, increments by one |
| 16 | 4 | timestamp_ms | Low 32 bits of capture time in milliseconds |
| 20 | 2 | frame_count | Number of 20 ms frames in payload |
| 22 | 2 | payload_bytes | PCM byte count following header |

The initial sender should batch five firmware frames per network chunk: 100 ms,
1,600 samples and 3,200 payload bytes. Batching may be tuned later without
changing capture or endpoint frame sizes.

# 6. Backpressure and Recovery

- Core 1 capture never waits for the socket or Pi.
- The local capture queue is bounded and retains newest audio by dropping the
  oldest queued frame when its consumer stalls.
- A separate PSRAM utterance ring will hold pre-roll and unsent network chunks.
- If any frame belonging to an active utterance is lost, the P4 sends
  `audio.cancel` with counters, resets endpoint/VAD state and remains locally
  responsive.
- The Pi acknowledges the highest contiguous sequence. The P4 limits unacked
  data by bytes and time; it does not accumulate an unbounded retransmit queue.
- After disconnect, stale utterances are discarded. A new session begins with
  `hello`; live conversation does not replay old speech.

# 7. Implementation and Test Order

1. Save deterministic generated PCM through a PC receiver and verify format,
   sequence and checksum.
2. Stream push-to-talk microphone audio without automatic VAD. **Implemented
   and physically verified on 2026-08-21.**
3. Add endpoint start/end and the 500 ms pre-roll path.
4. Connect Pi STT and measure end-to-final-transcript latency.
5. Add response text and TTS playback.
6. Exercise disconnects, delayed acknowledgements, Pi restart, queue pressure,
   maximum turns and cancellation before enabling automatic conversation.

## 7.1 Current deployment

| Setting | Deployed value |
|---|---|
| Host | `titanium` / `192.168.8.107` |
| WebSocket | `ws://192.168.8.107:8090/ws/v1` |
| HTTP diagnostics | `/health`, `/capabilities` |
| Authentication | `X-James-Token` or `Authorization: Bearer`; secret in `/etc/james/james.env` |
| TTS response | Binary 16 kHz mono PCM, kind `2` |
| Conversation route | `auto`: Gemini primary, local Ollama fallback |
| Live information | Open-Meteo current weather; intent-aware Gemini Google Search grounding |
| Spoken assistant identity | James; Project James remains the internal protocol/project label |
| Temporary PTT input | GPIO35 BOOT, active-low; hold to capture and release to send |
| P4 audio mode | Half-duplex; capture is gated while response PCM plays |
| P4 speaker level | ES8311 95%; NS4150B has fixed hardware gain and GPIO53 enable only |
| Firmware secrets | Git-ignored `main/james_private_config.h`; never Kconfig or tracked source |
| Capture buffering | 25 × 20 ms frames = 500 ms; 16,400 B PCM/frame metadata plus queue overhead |
| Network chunk | Five frames / 100 ms / 3,200 PCM bytes plus 24-byte header |
| Playback buffering | 8 KiB WebSocket assembly buffer; chunks write directly to ES8311/I2S |

The receiver implements strict 24-byte header parsing, contiguous sequence
acknowledgements, stale-session rejection, bounded utterance size, cancellation,
STT final text, assistant text/expression, and streamed TTS PCM. Unit and mocked
integration tests pass. The P4 client builds, flashes and opens both ES8311
audio directions successfully. Live microphone levels are present and
unclipped. It implements Wi-Fi
reconnect, authenticated hello, PTT capture, 100 ms binary microphone chunks,
response PCM validation and speaker playback. The physical P4 joined
`WETOHOST2.4`, received `192.168.8.131`, authenticated to Titanium and reached
“Gateway ready.” A live BOOT hold/speak/release turn then sent 2.50 seconds of
unclipped microphone PCM, produced an exact STT transcript, returned the
deterministic James identity answer and completed 16 kHz speaker playback. The
remaining protocol work is reconnect/failure injection, detailed latency
measurement, repeated-turn testing and automatic VAD endpointing.
`tts.end.timings_ms` reports Pi transcription, conversation/tool, synthesis,
and total gateway durations. The Windows PTT harness additionally records
capture and LAN round-trip timing for pre-P4 integration measurements.

The post-migration acceptance turn on 2026-08-22 captured 2.14 seconds of audio,
produced an exact transcript and deterministic identity answer 2.29 seconds
after release, began 16 kHz playback after 3.82 seconds and completed playback
15.02 seconds after release.

See [Pi Gateway and Windows Voice Test](Pi-Gateway-and-Windows-Voice-Test.md)
for deployment, provider, voice, and push-to-talk test procedures.
