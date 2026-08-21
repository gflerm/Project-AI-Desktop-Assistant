from __future__ import annotations

import unittest

from james_gateway.protocol import (
    BYTES_PER_FRAME,
    KIND_MICROPHONE,
    ProtocolError,
    decode_audio_chunk,
    encode_audio_chunk,
    pad_pcm_frames,
)


class ProtocolTests(unittest.TestCase):
    def test_binary_round_trip(self) -> None:
        payload = bytes(index % 256 for index in range(BYTES_PER_FRAME * 5))
        encoded = encode_audio_chunk(
            kind=KIND_MICROPHONE,
            utterance_id=7,
            sequence=3,
            timestamp_ms=120,
            payload=payload,
        )
        decoded = decode_audio_chunk(encoded, expected_kind=KIND_MICROPHONE)
        self.assertEqual(decoded.utterance_id, 7)
        self.assertEqual(decoded.sequence, 3)
        self.assertEqual(decoded.timestamp_ms, 120)
        self.assertEqual(decoded.frame_count, 5)
        self.assertEqual(decoded.payload, payload)

    def test_rejects_truncated_payload(self) -> None:
        encoded = encode_audio_chunk(
            kind=KIND_MICROPHONE,
            utterance_id=1,
            sequence=0,
            timestamp_ms=0,
            payload=bytes(BYTES_PER_FRAME),
        )
        with self.assertRaisesRegex(ProtocolError, "payload size"):
            decode_audio_chunk(encoded[:-1])

    def test_pcm_padding_uses_complete_frames(self) -> None:
        padded = pad_pcm_frames(b"\x01\x02" * 321)
        self.assertEqual(len(padded) % BYTES_PER_FRAME, 0)
        self.assertTrue(padded.startswith(b"\x01\x02" * 321))


if __name__ == "__main__":
    unittest.main()
