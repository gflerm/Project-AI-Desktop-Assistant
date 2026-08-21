# VED Training — Start Here

This folder is the complete beginner setup for testing Project James voice
activity detection (VAD), speech-to-text (STT), and recognition of the enrolled
operator's voice.

Implementation progress, dependencies, and goal completion criteria are tracked
in `../docs/Project-TODO-and-Verification.md`.

> Folder-name note: this project folder is named **VED Training** as requested.
> The standard technical term for speech detection is **VAD** (Voice Activity
> Detection). VAD itself is not trained to recognize a particular person.

## What You Are Actually Building

There are three separate functions:

1. **VAD:** detects when somebody starts and stops speaking.
2. **STT:** converts the recorded words into text.
3. **Speaker verification:** decides whether the voice resembles the enrolled
   operator.

The first PC recordings let us prove the recording, file-validation, and voice
enrollment workflow before the P4 microphone capture firmware is ready. Final
P4 tuning must later be repeated using the P4's onboard microphone because a PC
microphone and the P4 microphone do not sound identical.

No neural network is trained from scratch. We record multiple examples of your
natural voice and later use a pretrained speaker model on the Raspberry Pi 5 to
create a private enrollment profile.

## Folder Map

```text
VED Training/
  README.md                         this beginner guide
  SETUP-AND-RECORDING-PLAN.md       detailed end-to-end procedure
  docs/                             full engineering test plan
  plans/recording-plan.csv          phrases and recording conditions
  templates/                        CSV examples for later test results
  tools/                            setup, WAV checks, and evaluation scripts
  recordings/                       private WAV files; ignored by Git
```

## The Short Version

### 1. Install Audacity

Download Audacity from the official Windows download page:

https://www.audacityteam.org/download/windows/

The normal 64-bit installer is appropriate for most Windows 10/11 PCs. FFmpeg,
MuseHub, plugins, and cloud services are not required for this test.

### 2. Prepare the private recording folders

Open PowerShell in the repository root and run:

```powershell
& '.\VED Training\tools\setup.ps1'
```

This checks Python and creates the private session folders. It does not install
anything or upload audio.

### 3. Configure Audacity

In Audacity:

1. Choose your PC microphone under **Audio Setup > Recording Device**.
2. Choose **1 (Mono) Recording Channel**.
3. Set the project/audio sample rate to **16000 Hz**.
4. Start input monitoring and speak normally.
5. Adjust the microphone so ordinary speech is roughly -18 to -12 dB and never
   reaches 0 dB or produces a flat, squared-off waveform.

Windows must allow desktop applications to use the microphone under **Settings
> Privacy & security > Microphone**.

### 4. Make one test recording

Record this sentence in your normal voice:

> Project James, this is my first microphone test.

Leave roughly half a second of silence before and after the sentence. Do not
apply noise reduction, normalization, compression, reverb, or other effects.

Export it as:

```text
WAV, signed 16-bit PCM, mono, 16000 Hz
```

Save it here:

```text
VED Training/recordings/voice-corpus/session-001/
  s001-microphone-test-r01.wav
```

### 5. Check the file

From the repository root, run:

```powershell
python '.\VED Training\tools\check_wav.py' `
  '.\VED Training\recordings\voice-corpus\session-001\s001-microphone-test-r01.wav'
```

The result must say mono, 16-bit, 16000 Hz, uncompressed PCM, and no clipping.
If it fails, correct the Audacity export settings before recording the corpus.

### 6. Record the planned phrases

Open `plans/recording-plan.csv`. For session 001, record repetition 1 of each
row. Use one WAV file per phrase. Use the filename pattern:

```text
s001-<phrase_id>-r01.wav
```

Examples:

```text
s001-enroll_01-r01.wav
s001-valid_01-r01.wav
s001-test_01-r01.wav
```

Record session 002 on a different day using `s002-...-r02.wav`. A third session
is required for rows whose repeat count is 3. Natural day-to-day changes in
your voice are useful; do not try to reproduce the exact tone of the previous
session.

## What Happens After Recording

1. Validate every WAV file on the PC.
2. Fill in the private corpus manifest with what was actually spoken.
3. Measure PC-baseline VAD/STT performance.
4. Copy the private corpus to the Pi 5 over the local network or encrypted
   removable storage; do not publish it in GitHub.
5. Install the selected speaker-embedding runtime on the Pi 5.
6. Create your enrollment profile from enrollment clips only.
7. Select the speaker-match threshold from validation clips.
8. Run the untouched test clips once for the final result.
9. Repeat the acoustic tests with the actual P4 microphone.

Speaker-model installation and enrollment commands will be added when the Pi 5
runtime and exact model are selected. The recordings prepared here are the
input to that later step.

## Privacy

Your WAV files and future voice embeddings are biometric/private data. The
`recordings` directory is excluded by `.gitignore`. Do not force-add it, attach
it to an issue, or push it to the public repository. Only record another person
after receiving their explicit consent.
