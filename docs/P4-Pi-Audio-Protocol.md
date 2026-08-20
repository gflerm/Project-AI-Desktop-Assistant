# Project TARS — P4-to-Pi Audio Protocol

**Status:** Version 0.1 — implementation contract

**Date:** 2026-08-20

**Scope:** Reliable utterance transport between the ESP32-P4 and Raspberry Pi 5

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
| 0 | 4 | magic | ASCII `TAR1` |
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
2. Stream push-to-talk microphone audio without automatic VAD.
3. Add endpoint start/end and the 500 ms pre-roll path.
4. Connect Pi STT and measure end-to-final-transcript latency.
5. Add response text and TTS playback.
6. Exercise disconnects, delayed acknowledgements, Pi restart, queue pressure,
   maximum turns and cancellation before enabling automatic conversation.

The exact WebSocket endpoint, authentication secret provisioning, Pi service
port and TTS payload choice remain deployment configuration. They can be
implemented and measured locally while SSH access to Titanium is unavailable;
deployment onto Titanium waits for the key.
