#!/usr/bin/env python3
"""Native Windows push-to-talk tester for Project James."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
import urllib.error
import urllib.request
import uuid
import wave
import winsound

from james_feedback import empty_feedback, migrate_record, update_turn as save_turn_feedback

try:
    import sounddevice as sd
except ImportError:
    sd = None


class JamesTester(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Project James Voice Tester — PTT and Timing")
        self.geometry("900x640")
        self._audio_path = None
        self._input_stream = None
        self._recorded_chunks = []
        self._capture_started = 0.0
        self._last_raw_transcript = ""
        self._last_turn_path = None
        self._active_feedback_turn_id = None
        self._turn_paths = {}
        self._turn_raw_transcripts = {}
        self._personality_values = None
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.url = tk.StringVar(value="http://192.168.8.107:8090")
        self.ssh_host = tk.StringVar(value="georg@192.168.8.107")
        self.token = tk.StringVar()
        self.provider = tk.StringVar(value="auto")
        self.record_sessions = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Load the token, check the gateway, then hold Push to Talk.")
        self.metrics = tk.StringVar(value="Timing: no completed turn yet.")
        frame = ttk.Frame(self, padding=14)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(6, weight=1)
        self._entry(frame, 0, "Gateway URL", self.url)
        self._entry(frame, 1, "SSH host", self.ssh_host)
        ttk.Label(frame, text="Token").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.token, show="*").grid(row=2, column=1, sticky="ew")
        ttk.Label(frame, text="Model route (Ollama is private/local)").grid(row=3, column=0, sticky="w")
        ttk.Combobox(frame, textvariable=self.provider, values=("auto", "gemini", "ollama"), state="readonly").grid(row=3, column=1, sticky="ew")
        top = ttk.Frame(frame)
        top.grid(row=4, column=0, columnspan=2, sticky="w", pady=10)
        ttk.Button(top, text="Load token via SSH", command=self._load_token).pack(side="left")
        ttk.Button(top, text="Check gateway", command=self._check).pack(side="left", padx=8)
        ttk.Button(top, text="Stop voice", command=self._stop_audio).pack(side="left")
        ttk.Button(top, text="Telemetry summary", command=self._telemetry_summary).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(top, text="Personality", command=self._personality_controls).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(top, text="STT learning", command=self._speech_settings).pack(
            side="left", padx=(8, 0)
        )
        ttk.Label(frame, text="Prompt / Whisper transcript").grid(row=5, column=0, columnspan=2, sticky="w")
        self.prompt = tk.Text(frame, height=5, wrap="word")
        self.prompt.grid(row=6, column=0, columnspan=2, sticky="nsew", pady=5)
        self.prompt.insert("1.0", "Introduce yourself briefly and report whether you are ready.")
        actions = ttk.Frame(frame)
        actions.grid(row=7, column=0, columnspan=2, sticky="ew", pady=8)
        actions.columnconfigure((0, 1), weight=1)
        ttk.Button(actions, text="Ask typed prompt", command=self._ask_typed).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.ptt = ttk.Button(actions, text="Hold to talk")
        self.ptt.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.ptt.bind("<ButtonPress-1>", self._ptt_start)
        self.ptt.bind("<ButtonRelease-1>", self._ptt_stop)
        self.ptt.bind("<KeyPress-space>", self._ptt_start)
        self.ptt.bind("<KeyRelease-space>", self._ptt_stop)
        ttk.Button(
            actions,
            text="Teach STT from edited transcript",
            command=self._teach_stt,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        capture_controls = ttk.Frame(actions)
        capture_controls.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Checkbutton(
            capture_controls,
            text="Record private test sessions (input, transcript, response, timings)",
            variable=self.record_sessions,
        ).pack(side="left")
        ttk.Button(
            capture_controls, text="Flag shortcomings", command=self._flag_shortcomings
        ).pack(side="left", padx=8)
        ttk.Button(
            capture_controls, text="Analyze recordings", command=self._analyze_recordings
        ).pack(side="left")
        ttk.Label(frame, text="James response").grid(row=8, column=0, columnspan=2, sticky="w")
        self.response = tk.Text(frame, height=6, wrap="word", state="disabled")
        self.response.grid(row=9, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Label(frame, textvariable=self.metrics).grid(row=10, column=0, columnspan=2, sticky="w")
        ttk.Label(frame, textvariable=self.status).grid(row=11, column=0, columnspan=2, sticky="w")

    @staticmethod
    def _entry(frame, row, label, variable) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w")
        ttk.Entry(frame, textvariable=variable).grid(row=row, column=1, sticky="ew")

    def _background(self, label, action) -> None:
        self.status.set(label)
        threading.Thread(target=self._run_action, args=(action,), daemon=True).start()

    def _run_action(self, action) -> None:
        try:
            result = action()
            self.after(0, lambda: self.status.set(result or "Done."))
        except Exception as error:
            self.after(0, lambda: messagebox.showerror("Project James", str(error)))
            self.after(0, lambda: self.status.set("Test failed."))

    def _load_token(self) -> None:
        def action():
            key, hosts = Path.home()/".ssh"/"id_ed25519", Path.home()/".ssh"/"known_hosts"
            command = ["ssh", "-i", str(key), "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", f"UserKnownHostsFile={hosts}", self.ssh_host.get().strip(), "sudo -n sed -n 's/^JAMES_TOKEN=//p' /etc/james/james.env"]
            token = subprocess.run(command, capture_output=True, text=True, timeout=15, check=True).stdout.strip()
            if len(token) < 24:
                raise RuntimeError("The James token could not be loaded over SSH.")
            self.after(0, lambda: self.token.set(token))
            return "Token loaded securely; it is masked and not saved."
        self._background("Loading token over SSH...", action)

    def _request(
        self, path, payload=None, content_type="application/json", extra_headers=None,
        method=None,
    ):
        token = self.token.get().strip()
        if not token:
            raise RuntimeError("Load or paste the James token first.")
        data = payload if isinstance(payload, bytes) or payload is None else json.dumps(payload).encode()
        headers = {"X-James-Token": token, "Content-Type": content_type}
        headers.update(extra_headers or {})
        request = urllib.request.Request(
            f"{self.url.get().rstrip('/')}{path}", data=data, headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                headers = {key.lower(): value for key, value in response.headers.items()}
                return response.read(), response.headers.get_content_type(), headers
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"Gateway returned HTTP {error.code}: {error.read().decode(errors='replace')}") from error

    def _check(self) -> None:
        def action():
            health = json.loads(self._request("/health")[0])
            return "Gateway healthy." if health.get("ok") else f"Gateway degraded: {health}"
        self._background("Checking gateway...", action)

    def _telemetry_summary(self) -> None:
        def action():
            summary = json.loads(self._request("/v1/telemetry/summary")[0])
            self.after(0, lambda: self._show_json_window("James Telemetry Summary", summary))
            return f"Loaded {summary.get('total_events', 0)} recorded telemetry events."
        self._background("Loading telemetry summary...", action)

    def _personality_controls(self) -> None:
        def action():
            profile = json.loads(self._request("/v1/settings/personality")[0])
            self.after(0, lambda: self._show_personality_window(profile["values"]))
            return "Loaded live personality controls."
        self._background("Loading personality controls...", action)

    def _show_personality_window(self, values) -> None:
        self._personality_values = dict(values)
        window = tk.Toplevel(self)
        window.title("James Personality — live controls")
        window.geometry("560x630")
        body = ttk.Frame(window, padding=14)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        controls = {}
        labels = {
            "honesty": "Factual candour (keep high)",
            "humour": "Frequency of restrained dry wit",
            "sarcasm": "Sharpness of the wit",
            "verbosity": "Answer detail and length",
            "initiative": "Readiness to suggest a useful next step",
            "skepticism": "Strength of assumption checking",
            "formality": "Formal versus conversational delivery",
            "discretion": "Privacy and restraint (keep high)",
            "chattiness": "Amount of optional conversation",
        }
        for row, (name, value) in enumerate(values.items()):
            variable = tk.IntVar(value=value)
            controls[name] = variable
            ttk.Label(body, text=labels.get(name, name.title())).grid(
                row=row * 2, column=0, sticky="w"
            )
            ttk.Scale(body, from_=0, to=100, variable=variable).grid(
                row=row * 2 + 1, column=0, sticky="ew", pady=(0, 6)
            )
            ttk.Label(body, textvariable=variable, width=4).grid(
                row=row * 2 + 1, column=1, padx=(8, 0)
            )

        def apply():
            selected = {name: int(variable.get()) for name, variable in controls.items()}
            self._personality_values = dict(selected)
            def action():
                self._request(
                    "/v1/settings/personality",
                    {"values": selected},
                    method="PUT",
                )
                return "Personality updated immediately and saved on the Pi."
            self._background("Applying personality controls...", action)

        ttk.Button(body, text="Apply immediately", command=apply).grid(
            row=len(values) * 2, column=0, columnspan=2, sticky="ew", pady=(10, 0)
        )

    def _speech_settings(self) -> None:
        def action():
            settings = json.loads(self._request("/v1/settings/speech")[0])
            self.after(0, lambda: self._show_speech_window(settings))
            return "Loaded STT adaptation settings."
        self._background("Loading STT adaptation settings...", action)

    def _show_speech_window(self, settings) -> None:
        window = tk.Toplevel(self)
        window.title("James STT learning")
        window.geometry("620x360")
        body = ttk.Frame(window, padding=14)
        body.pack(fill="both", expand=True)
        ttk.Label(
            body,
            text="Vocabulary and names Whisper should expect (comma-separated is fine):",
        ).pack(anchor="w")
        hints = tk.Text(body, height=7, wrap="word")
        hints.pack(fill="both", expand=True, pady=8)
        hints.insert("1.0", settings.get("hints", ""))
        learned = ", ".join(settings.get("learned_words", [])) or "none yet"
        ttk.Label(
            body,
            text=(
                f"Saved corrections: {settings.get('phrase_corrections', 0)} phrases, "
                f"{settings.get('word_corrections', 0)} words. Learned: {learned}"
            ),
            wraplength=580,
        ).pack(anchor="w", pady=(0, 8))

        def save():
            value = hints.get("1.0", "end").strip()
            def action():
                self._request(
                    "/v1/settings/speech/hints", {"hints": value}, method="PUT"
                )
                return "Speech hints saved and active for the next recording."
            self._background("Saving speech hints...", action)

        ttk.Button(body, text="Save speech hints", command=save).pack(fill="x")

    def _teach_stt(self) -> None:
        turn_id = self._active_feedback_turn_id
        path = self._turn_paths.get(turn_id)
        observed = str(self._turn_raw_transcripts.get(turn_id) or "").strip()
        corrected = self.prompt.get("1.0", "end").strip()
        if not observed or not turn_id or not path:
            messagebox.showinfo(
                "Project James", "Record one PTT utterance first, then edit its transcript here."
            )
            return
        if not corrected or corrected == observed:
            messagebox.showinfo(
                "Project James", "Edit the transcript to what you actually said, then teach it."
            )
            return

        def action():
            result = json.loads(self._request(
                "/v1/settings/speech/corrections",
                {
                    "turn_id": turn_id,
                    "observed": observed,
                    "corrected": corrected,
                    "audio_verified": True,
                },
            )[0])
            record = migrate_record(json.loads(path.read_text(encoding="utf-8")))
            feedback = record["feedback"]
            feedback["transcript"].update(
                {
                    "corrected": corrected,
                    "audio_verified": True,
                    "approved_for_speech_dictionary": True,
                }
            )
            save_turn_feedback(path, turn_id, feedback)
            return (
                f"Correction for turn {turn_id[:8]} learned and audio-verified: "
                f"{result.get('word_corrections', 0)} reusable word corrections saved."
            )
        self._background("Teaching the STT correction...", action)

    def _show_json_window(self, title, payload) -> None:
        window = tk.Toplevel(self)
        window.title(title)
        window.geometry("760x600")
        content = tk.Text(window, wrap="none")
        content.pack(fill="both", expand=True)
        content.insert("1.0", json.dumps(payload, indent=2))
        content.configure(state="disabled")

    def _ask_typed(self) -> None:
        prompt = self.prompt.get("1.0", "end").strip()
        if prompt:
            self._ask(prompt)

    def _chat_and_speak(self, prompt, turn_id):
        llm_started = time.perf_counter()
        result = json.loads(self._request("/v1/test/chat", {
            "text": prompt, "device_id": "windows-tester",
            "provider": self.provider.get(), "turn_id": turn_id,
        })[0])
        llm_wall_ms = round((time.perf_counter() - llm_started) * 1000)
        self.after(0, lambda: self._show_response(result["text"]))
        tts_started = time.perf_counter()
        wav, content_type, headers = self._request(
            "/v1/test/speech", {"text": result["text"], "turn_id": turn_id}
        )
        tts_wall_ms = round((time.perf_counter() - tts_started) * 1000)
        if content_type != "audio/wav" or not wav.startswith(b"RIFF"):
            raise RuntimeError("The gateway did not return a valid WAV response.")
        self._play_wav(wav)
        return result, {
            "llm_wall_ms": llm_wall_ms,
            "llm_server_ms": result.get("server_ms"),
            "tts_wall_ms": tts_wall_ms,
            "tts_server_ms": int(headers.get("x-james-server-ms", 0)),
            "output_audio_bytes": len(wav),
            "output_audio_duration_ms": max(0, round((len(wav) - 44) / 32)),
        }, wav

    def _ask(self, prompt) -> None:
        record_enabled = self.record_sessions.get()
        def action():
            started = time.perf_counter()
            turn_id = str(uuid.uuid4())
            result, timing, response_wav = self._chat_and_speak(prompt, turn_id)
            timing["total_ms"] = round((time.perf_counter() - started) * 1000)
            self._record_client_turn(turn_id, result["route"], timing)
            if record_enabled:
                self._save_recorded_turn(
                    turn_id=turn_id,
                    mode="typed",
                    prompt=prompt,
                    raw_transcript=None,
                    adapted_transcript=None,
                    result=result,
                    timing=timing,
                    input_pcm=None,
                    response_wav=response_wav,
                )
            self.after(0, lambda: self._show_metrics(timing))
            return f"Response received via {result['route']} route and playing."
        self._background("James is preparing a response...", action)

    def _ptt_start(self, _event=None) -> None:
        if self._input_stream is not None:
            return
        if sd is None:
            messagebox.showerror("Project James", "Microphone support needs sounddevice. Use Launch-James-Tester.ps1.")
            return
        self._recorded_chunks = []
        def callback(indata, _frames, _time, status):
            if status:
                self.after(0, lambda: self.status.set(f"Microphone: {status}"))
            self._recorded_chunks.append(bytes(indata))
        try:
            self._input_stream = sd.RawInputStream(samplerate=16000, blocksize=320, channels=1, dtype="int16", callback=callback)
            self._input_stream.start()
            self._capture_started = time.perf_counter()
            self.ptt.configure(text="Recording — release to send")
            self.status.set("Recording 16 kHz mono PCM...")
        except Exception as error:
            self._input_stream = None
            messagebox.showerror("Project James", f"Could not open the microphone: {error}")

    def _ptt_stop(self, _event=None) -> None:
        if self._input_stream is None:
            return
        self._input_stream.stop(); self._input_stream.close(); self._input_stream = None
        capture_ms = round((time.perf_counter() - self._capture_started) * 1000)
        turn_started = time.perf_counter()
        self.ptt.configure(text="Hold to talk")
        pcm = b"".join(self._recorded_chunks); self._recorded_chunks = []
        record_enabled = self.record_sessions.get()
        def action():
            stt_started = time.perf_counter()
            turn_id = str(uuid.uuid4())
            stt_result = json.loads(self._request(
                "/v1/test/stt", pcm, "application/octet-stream",
                {"X-James-Turn-Id": turn_id},
            )[0])
            stt_wall_ms = round((time.perf_counter() - stt_started) * 1000)
            transcript = stt_result.get("transcript", "").strip()
            self._last_raw_transcript = stt_result.get("raw_transcript", transcript).strip()
            if not transcript:
                raise RuntimeError("Whisper did not detect speech. Hold the button and try again.")
            self.after(0, lambda: self._show_prompt(transcript))
            result, timing, response_wav = self._chat_and_speak(transcript, turn_id)
            timing.update({
                "capture_ms": capture_ms,
                "stt_wall_ms": stt_wall_ms,
                "stt_server_ms": stt_result.get("server_ms"),
                "total_ms": round((time.perf_counter() - turn_started) * 1000),
                "input_audio_bytes": len(pcm),
                "input_audio_duration_ms": round(len(pcm) / 32),
            })
            self._record_client_turn(turn_id, result["route"], timing)
            if record_enabled:
                self._save_recorded_turn(
                    turn_id=turn_id,
                    mode="ptt",
                    prompt=transcript,
                    raw_transcript=self._last_raw_transcript,
                    adapted_transcript=transcript,
                    result=result,
                    timing=timing,
                    input_pcm=pcm,
                    response_wav=response_wav,
                )
            self.after(0, lambda: self._show_metrics(timing))
            return f'Heard: "{transcript}" — {result["route"]} response is playing.'
        self._background("Sending audio to Whisper...", action)

    def _record_client_turn(self, turn_id, route, timing) -> None:
        self._request(
            "/v1/telemetry/client",
            {
                "turn_id": turn_id,
                "route": route,
                "capture_ms": timing.get("capture_ms"),
                "stt_wall_ms": timing.get("stt_wall_ms"),
                "llm_wall_ms": timing.get("llm_wall_ms"),
                "tts_wall_ms": timing.get("tts_wall_ms"),
                "total_ms": timing["total_ms"],
                "audio_bytes": timing.get("input_audio_bytes"),
                "audio_duration_ms": timing.get("input_audio_duration_ms"),
                "status": "ok",
            },
        )

    @staticmethod
    def _captures_root() -> Path:
        return Path(__file__).resolve().parents[1] / "captures" / "james-sessions"

    def _save_recorded_turn(
        self,
        *,
        turn_id,
        mode,
        prompt,
        raw_transcript,
        adapted_transcript,
        result,
        timing,
        input_pcm,
        response_wav,
    ) -> None:
        if self._personality_values is None:
            try:
                profile = json.loads(self._request("/v1/settings/personality")[0])
                self._personality_values = dict(profile.get("values", {}))
            except Exception:
                # A capture must still be retained if optional settings lookup fails.
                pass
        stamp = datetime.now(timezone.utc)
        directory = self._captures_root() / f"{stamp:%Y%m%dT%H%M%SZ}_{turn_id[:8]}"
        directory.mkdir(parents=True, exist_ok=False)
        if input_pcm:
            with wave.open(str(directory / "input.wav"), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(16000)
                output.writeframes(input_pcm)
        (directory / "response.wav").write_bytes(response_wav)
        record = {
            "schema": 2,
            "turn_id": turn_id,
            "recorded_at_utc": stamp.isoformat(timespec="seconds"),
            "mode": mode,
            "prompt": prompt,
            "raw_transcript": raw_transcript,
            "adapted_transcript": adapted_transcript,
            "response_text": result.get("text"),
            "route": result.get("route"),
            "provider": result.get("provider"),
            "fallback_used": result.get("fallback_used", False),
            "grounding_source": result.get("grounding_source"),
            "routing_reason": result.get("routing_reason"),
            "route_components": result.get("route_components", []),
            "finish_reason": result.get("finish_reason"),
            "answer_complete": result.get("answer_complete"),
            "personality": self._personality_values,
            "timing_ms": timing,
            "files": {
                "input": "input.wav" if input_pcm else None,
                "response": "response.wav",
            },
            "feedback": empty_feedback(),
        }
        path = directory / "turn.json"
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        if "_turn_paths" not in self.__dict__:
            self._turn_paths = {}
        if "_turn_raw_transcripts" not in self.__dict__:
            self._turn_raw_transcripts = {}
        self._last_turn_path = path
        self._active_feedback_turn_id = turn_id
        self._turn_paths[turn_id] = path
        self._turn_raw_transcripts[turn_id] = raw_transcript

    def _update_last_turn(self, changes) -> None:
        path = self._last_turn_path
        if not path or not path.is_file():
            return
        record = json.loads(path.read_text(encoding="utf-8"))
        record.update(changes)
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    def _feedback_target(self):
        turn_id = self._active_feedback_turn_id
        path = self._turn_paths.get(turn_id)
        if not turn_id or not path or not path.is_file():
            return None, None, None
        record = migrate_record(json.loads(path.read_text(encoding="utf-8")))
        if record.get("turn_id") != turn_id:
            raise RuntimeError("The displayed turn no longer matches its private recording.")
        return turn_id, path, record

    def _flag_shortcomings(self) -> None:
        turn_id, path, record = self._feedback_target()
        if not turn_id:
            messagebox.showinfo(
                "Project James", "Complete a recorded turn before flagging its shortcomings."
            )
            return
        window = tk.Toplevel(self)
        window.title("Flag James shortcomings")
        window.geometry("620x740")
        body = ttk.Frame(window, padding=14)
        body.pack(fill="both", expand=True)
        tags = {}
        for label in (
            "STT misheard me",
            "Answer was incorrect",
            "Answer was incomplete",
            "Answer ignored context",
            "Response was too slow",
            "Voice sounded bland",
            "Voice pronunciation problem",
            "Personality felt wrong",
            "Too much or misplaced humour",
        ):
            variable = tk.BooleanVar(value=False)
            tags[label] = variable
            ttk.Checkbutton(body, text=label, variable=variable).pack(anchor="w")
        ttk.Label(body, text=f"Feedback target: {turn_id}").pack(anchor="w", pady=(8, 0))
        rating = tk.StringVar(value="wrong")
        ttk.Label(body, text="Answer rating:").pack(anchor="w", pady=(8, 0))
        ttk.Combobox(
            body,
            textvariable=rating,
            values=("correct", "partial", "wrong"),
            state="readonly",
        ).pack(fill="x")
        ttk.Label(body, text="Why it failed:").pack(
            anchor="w", pady=(10, 0)
        )
        notes = tk.Text(body, height=7, wrap="word")
        notes.pack(fill="both", expand=True, pady=6)
        ttk.Label(body, text="Preferred answer:").pack(anchor="w")
        preferred = tk.Text(body, height=5, wrap="word")
        preferred.pack(fill="both", expand=True, pady=6)
        expected_route = tk.StringVar(value="")
        ttk.Label(body, text="Expected route (optional):").pack(anchor="w")
        ttk.Combobox(
            body,
            textvariable=expected_route,
            values=("", "tool", "local", "cloud", "multi"),
            state="readonly",
        ).pack(fill="x", pady=(0, 6))
        expected_tool = tk.StringVar(value="")
        ttk.Label(body, text="Expected tool ID (optional):").pack(anchor="w")
        ttk.Entry(body, textvariable=expected_tool).pack(fill="x", pady=(0, 6))
        approve_regression = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            body,
            text="Approve this turn as a regression case",
            variable=approve_regression,
        ).pack(anchor="w")
        teach_local = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            body,
            text="Approve preferred answer as a private Ollama-only lesson",
            variable=teach_local,
        ).pack(anchor="w", pady=(0, 6))

        def save():
            guidance = notes.get("1.0", "end").strip()
            preferred_answer = preferred.get("1.0", "end").strip()
            feedback = record["feedback"]
            feedback["answer"].update(
                {
                    "rating": rating.get(),
                    "issue_tags": [name for name, selected in tags.items() if selected.get()],
                    "critique": guidance,
                    "preferred_answer": preferred_answer,
                    "approved_for_local_lesson": bool(teach_local.get()),
                }
            )
            feedback["expected"]["route"] = expected_route.get() or None
            feedback["expected"]["tool"] = expected_tool.get().strip() or None
            feedback["review"].update(
                {
                    "status": "reviewed",
                    "approved_for_regression": bool(approve_regression.get()),
                }
            )
            save_turn_feedback(path, turn_id, feedback)
            window.destroy()
            if teach_local.get() and preferred_answer:
                def action():
                    result = json.loads(self._request(
                        "/v1/settings/local-learning/lessons",
                        {
                            "prompt": record.get("prompt", ""),
                            "response": record.get("response_text", ""),
                            "guidance": (
                                f"Preferred answer: {preferred_answer}"
                                + (f"\nReason: {guidance}" if guidance else "")
                            ),
                        },
                    )[0])
                    return (
                        "Shortcoming saved and taught locally; "
                        f"{result.get('lesson_count', 0)} Ollama-only lessons retained."
                    )
                self._background("Saving private local lesson...", action)
            else:
                self.status.set(f"Feedback saved against immutable turn {turn_id[:8]}.")

        ttk.Button(body, text="Save feedback", command=save).pack(fill="x")

    def _analyze_recordings(self) -> None:
        def action():
            script = Path(__file__).with_name("analyze_james_sessions.py")
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                timeout=60,
                check=True,
            )
            report = Path(result.stdout.strip())
            if not report.is_file():
                raise RuntimeError("The analysis report was not created.")
            self.after(0, lambda: os.startfile(report))
            return f"Analysis complete: {report}"
        self._background("Analyzing private test recordings...", action)

    def _show_prompt(self, text) -> None:
        self.prompt.delete("1.0", "end"); self.prompt.insert("1.0", text)

    def _show_response(self, text) -> None:
        self.response.configure(state="normal"); self.response.delete("1.0", "end")
        self.response.insert("1.0", text); self.response.configure(state="disabled")

    def _show_metrics(self, timing) -> None:
        parts = []
        labels = (
            ("capture_ms", "capture"), ("stt_wall_ms", "STT"),
            ("llm_wall_ms", "LLM/tool"), ("tts_wall_ms", "TTS"),
            ("total_ms", "release→audio"),
        )
        for key, label in labels:
            if timing.get(key) is not None:
                parts.append(f"{label} {timing[key] / 1000:.2f}s")
        server = []
        for key, label in (("stt_server_ms", "STT"), ("llm_server_ms", "LLM"), ("tts_server_ms", "TTS")):
            if timing.get(key) is not None:
                server.append(f"{label} {timing[key] / 1000:.2f}s")
        self.metrics.set("Timing: " + " | ".join(parts) + ("  (Pi: " + ", ".join(server) + ")" if server else ""))

    def _play_wav(self, wav) -> None:
        self._stop_audio()
        with tempfile.NamedTemporaryFile(prefix="james-response-", suffix=".wav", delete=False) as output:
            output.write(wav); self._audio_path = output.name
        winsound.PlaySound(self._audio_path, winsound.SND_FILENAME | winsound.SND_ASYNC)

    def _stop_audio(self) -> None:
        winsound.PlaySound(None, winsound.SND_PURGE)
        if self._audio_path:
            try: os.unlink(self._audio_path)
            except OSError: pass
            self._audio_path = None

    def _close(self) -> None:
        if self._input_stream is not None:
            self._input_stream.stop(); self._input_stream.close()
        self._stop_audio(); self.destroy()


if __name__ == "__main__":
    JamesTester().mainloop()
