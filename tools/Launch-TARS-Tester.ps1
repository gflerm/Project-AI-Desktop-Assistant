$ErrorActionPreference = 'Stop'
$tester = Join-Path $PSScriptRoot 'tars_windows_tester.py'
if (Get-Command uv -ErrorAction SilentlyContinue) {
    & uv run --with sounddevice python $tester
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -m pip install --user sounddevice
    & py -3 $tester
} else {
    & python -m pip install --user sounddevice
    & python $tester
}
