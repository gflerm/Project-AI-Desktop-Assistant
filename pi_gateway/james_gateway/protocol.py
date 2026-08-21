from __future__ import annotations

from dataclasses import dataclass
import struct


PROTOCOL_VERSION = 1
MAGIC = b"JAM1"
HEADER_BYTES = 24
KIND_MICROPHONE = 1
KIND_TTS = 2
SAMPLE_RATE_HZ = 16_000
SAMPLE_BITS = 16
CHANNELS = 1
FRAME_MS = 20
SAMPLES_PER_FRAME = 320
BYTES_PER_FRAME = 640
FRAMES_PER_CHUNK = 5
PCM_BYTES_PER_CHUNK = BYTES_PER_FRAME * FRAMES_PER_CHUNK
HEADER = struct.Struct("!4sBBHIIIHH")


class ProtocolError(ValueError):
    def __init__(self, code: str, detail: str, *, retryable: bool = False):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.retryable = retryable


@dataclass(frozen=True)
class AudioChunk:
    kind: int
    utterance_id: int
    sequence: int
    timestamp_ms: int
    frame_count: int
    payload: bytes


def decode_audio_chunk(data: bytes, *, expected_kind: int | None = None) -> AudioChunk:
    if len(data) < HEADER_BYTES:
        raise ProtocolError("binary_header_short", "Binary message is shorter than 24 bytes")
    magic, version, kind, header_bytes, utterance_id, sequence, timestamp_ms, frame_count, payload_bytes = HEADER.unpack_from(data)
    if magic != MAGIC:
        raise ProtocolError("binary_magic", "Binary message magic is not JAM1")
    if version != PROTOCOL_VERSION:
        raise ProtocolError("binary_version", f"Unsupported binary version {version}")
    if header_bytes != HEADER_BYTES:
        raise ProtocolError("binary_header_size", f"Header size must be {HEADER_BYTES}")
    if expected_kind is not None and kind != expected_kind:
        raise ProtocolError("binary_kind", f"Expected audio kind {expected_kind}, received {kind}")
    payload = data[HEADER_BYTES:]
    if payload_bytes != len(payload):
        raise ProtocolError("binary_payload_size", "Declared payload size does not match message")
    if frame_count < 1 or payload_bytes != frame_count * BYTES_PER_FRAME:
        raise ProtocolError(
            "binary_frame_size",
            f"PCM payload must contain {BYTES_PER_FRAME} bytes per 20 ms frame",
        )
    return AudioChunk(kind, utterance_id, sequence, timestamp_ms, frame_count, payload)


def encode_audio_chunk(
    *,
    kind: int,
    utterance_id: int,
    sequence: int,
    timestamp_ms: int,
    payload: bytes,
) -> bytes:
    if kind not in (KIND_MICROPHONE, KIND_TTS):
        raise ProtocolError("binary_kind", f"Unsupported audio kind {kind}")
    if not payload or len(payload) % BYTES_PER_FRAME:
        raise ProtocolError(
            "binary_frame_size",
            f"PCM payload must be a non-empty multiple of {BYTES_PER_FRAME} bytes",
        )
    frame_count = len(payload) // BYTES_PER_FRAME
    return HEADER.pack(
        MAGIC,
        PROTOCOL_VERSION,
        kind,
        HEADER_BYTES,
        utterance_id,
        sequence,
        timestamp_ms & 0xFFFFFFFF,
        frame_count,
        len(payload),
    ) + payload


def pad_pcm_frames(pcm: bytes) -> bytes:
    remainder = len(pcm) % BYTES_PER_FRAME
    return pcm if remainder == 0 else pcm + bytes(BYTES_PER_FRAME - remainder)
