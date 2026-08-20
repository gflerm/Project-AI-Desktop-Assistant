# PC Setup and Recording Plan

## Goal

Produce a clean, repeatable private voice corpus on the Windows PC, verify that
every file has the expected format, and preserve separate enrollment,
validation, and test data for later processing on the Raspberry Pi 5.

This recording work is Goal G0 in
`../docs/Project-TODO-and-Verification.md`. Do not mark later P4 or Pi 5 goals complete
merely because the PC files pass validation.

## Phase 0 — Important Expectations

- A PC recording proves the workflow; it does not replace the later P4
  microphone test.
- VAD detects speech and does not learn your identity.
- Speaker verification uses enrollment recordings and a pretrained model.
- STT normally uses a pretrained model before any fine-tuning is considered.
- Different tones should be natural variations, not strained or theatrical
  voices.

## Phase 1 — PC Requirements

Required:

- Windows 10 or Windows 11;
- a working built-in, headset, or USB microphone;
- Audacity;
- Python 3 for the supplied checking scripts;
- enough local disk space for uncompressed WAV files.

Recommended for the first baseline:

- use the microphone you normally use at the desk;
- use the same room and normal sitting position;
- turn off artificial microphone effects if the device utility exposes them;
- note the microphone name so the same device can be selected later.

Do not buy a special microphone for this step. Once P4 capture works, the P4
onboard microphone becomes the important reference device.

## Phase 2 — Install and Check Audacity

1. Download Audacity only from its official site or Microsoft Store.
2. Install and start it.
3. If the microphone is missing, enable Windows microphone permission for
   desktop apps and use Audacity's rescan-audio-devices command.
4. Select the intended microphone, mono recording, and 16000 Hz.
5. Start monitoring before recording the first clip.

Level check:

- speak the quietest planned phrase and confirm that a visible waveform exists;
- speak the loudest natural phrase and confirm it does not touch 0 dB;
- lower input gain or move farther away if the meter enters the clipping region;
- keep the gain setting unchanged throughout one session.

## Phase 3 — First Technical Test

Record three separate files before starting the full plan:

| File | Content | Length |
|---|---|---:|
| `s001-room-silence-r01.wav` | No speech; sit normally | 10 seconds |
| `s001-microphone-test-r01.wav` | Normal test sentence | 3–6 seconds |
| `s001-quiet-test-r01.wav` | Same sentence, naturally quiet | 3–6 seconds |

For each clip:

1. press Record;
2. wait about 0.5 seconds;
3. say the phrase once;
4. wait about 0.5 seconds;
5. press Stop;
6. listen once for obvious faults;
7. export as WAV, signed 16-bit PCM;
8. delete/close the current track before recording the next clip.

Do not trim the surrounding silence. Do not process or improve the audio. If a
door slam or spoken mistake occurs, redo that take under a new filename or mark
it unusable; never silently alter the master recording.

Run:

```powershell
python '.\VED Training\tools\check_wav.py' `
  '.\VED Training\recordings\voice-corpus\session-001\*.wav'
```

Proceed only when the spoken files are valid and unclipped.

## Phase 4 — Session 001

Use `plans/recording-plan.csv` as the prompt sheet. Record the first repetition
of each applicable prompt. Keep one phrase per WAV file and use exact phrase IDs
in filenames.

Order:

1. room-silence and background-noise rows;
2. enrollment rows;
3. validation rows;
4. test rows;
5. playback/AEC rows only when speaker playback is available.

Take a short break if your voice becomes tired. Fatigue is a desired condition
only where explicitly requested; it should not contaminate every prompt.

At the end, record the following private session notes:

```text
date and local time:
room:
microphone/device name:
Windows input level:
approximate mouth-to-microphone distance:
unusual noises or interruptions:
```

## Phase 5 — Sessions 002 and 003

Wait until another day. Do not change session 001 after beginning session 002.

- Session 002 supplies repetition 2 and natural day-to-day voice variation.
- Session 003 supplies repetition 3 for the rows that request it.
- Preserve the intended enrollment/validation/test split.
- Never copy a difficult test recording into enrollment just to improve a
  result.

## Phase 6 — Metadata

Copy `templates/corpus-manifest.example.csv` into the private
`recordings/voice-corpus` directory and call it `manifest.csv`. Add one row per
WAV file.

Important fields:

- `file`: path to the WAV file;
- `split`: enrollment, validation, test, or noise;
- `speaker_id`: use `operator`, not your legal name;
- `session_id`: for example `session-001`;
- `phrase_id`: exact ID from the plan;
- `transcript`: words actually spoken, including deviations;
- `tone`, `distance_m`, `noise`, and `device`: actual conditions;
- `consent`: true for your own clips and only true for other people after
  explicit permission;
- `speech_start_ms` and `speech_end_ms`: later waveform annotations.

Then run the complete validator:

```powershell
python '.\VED Training\tools\validate_corpus.py' `
  '.\VED Training\recordings\voice-corpus\manifest.csv' `
  --report '.\VED Training\recordings\voice-corpus\validation-report.json'
```

## Phase 7 — Baseline and Pi 5 Enrollment

After the corpus is valid:

1. run VAD and STT against validation audio first;
2. keep the test split untouched while settings are adjusted;
3. transfer the private audio to the Pi 5 without using the public repository;
4. generate one speaker embedding per clean enrollment clip;
5. average and normalize the enrollment embeddings;
6. score validation recordings from the operator and consenting other speakers;
7. select an operating threshold based on false acceptance and false rejection;
8. run the held-out test split once;
9. repeat with audio recorded through the actual P4 microphone.

## Phase 8 — Success Criteria

The initial recording phase succeeds when:

- all tracked recordings are mono, 16-bit, 16000 Hz PCM WAV;
- there is no digital clipping;
- filenames and manifest rows agree;
- enrollment, validation, and test clips are distinct;
- at least two different recording days are represented in enrollment;
- private recordings remain outside Git;
- the P4 repeat-test requirement is clearly recorded.
