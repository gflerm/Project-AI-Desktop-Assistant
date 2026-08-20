param(
    [ValidatePattern('^session-[0-9]{3}$')]
    [string]$Session = 'session-001'
)

$ErrorActionPreference = 'Stop'

$trainingRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$recordingRoot = Join-Path $trainingRoot 'recordings\voice-corpus'
$sessionRoot = Join-Path $recordingRoot $Session

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    throw 'Python was not found. Install Python 3 and ensure the python command is available.'
}

$pythonVersion = & python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    throw 'The python command exists but could not be run.'
}

New-Item -ItemType Directory -Path $sessionRoot -Force | Out-Null

Write-Host "VED Training root: $trainingRoot"
Write-Host "Private session folder: $sessionRoot"
Write-Host "Python: $pythonVersion"
Write-Host ''
Write-Host 'Next: install/open Audacity, record the microphone test, export it to the session folder, then run check_wav.py.'
