[CmdletBinding()]
param(
    [switch]$Clean,
    [string]$IdfPath = 'C:\esp\v6.0.2\esp-idf',
    [string]$IdfToolsPath = 'C:\Users\zs1gf\.espressif',
    [string]$IdfPythonEnvPath = 'C:\Espressif\tools\python\v6.0.2\venv'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$buildPath = [IO.Path]::GetFullPath((Join-Path $projectRoot 'build'))
$expectedBuildPath = Join-Path $projectRoot 'build'

if ($buildPath -ne $expectedBuildPath) {
    throw "Unexpected build path: $buildPath"
}

foreach ($requiredPath in @(
        $IdfPath,
        $IdfToolsPath,
        $IdfPythonEnvPath,
        (Join-Path $IdfPath 'export.ps1'),
        (Join-Path $IdfPath 'tools\idf.py'),
        (Join-Path $IdfPythonEnvPath 'Scripts\python.exe')
    )) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required ESP-IDF path does not exist: $requiredPath"
    }
}

if ($Clean -and (Test-Path -LiteralPath $buildPath)) {
    $buildItem = Get-Item -LiteralPath $buildPath -Force
    if (-not $buildItem.PSIsContainer) {
        throw "Build target is not a directory: $buildPath"
    }
    if ($buildItem.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw "Refusing to remove a linked/reparse-point build directory: $buildPath"
    }
    if ((Split-Path -Parent $buildItem.FullName) -ne $projectRoot -or
        (Split-Path -Leaf $buildItem.FullName) -ne 'build') {
        throw "Refusing to remove unexpected path: $($buildItem.FullName)"
    }
    Remove-Item -LiteralPath $buildItem.FullName -Recurse -Force -ErrorAction Stop
}

$env:IDF_TOOLS_PATH = $IdfToolsPath
$env:IDF_PYTHON_ENV_PATH = $IdfPythonEnvPath

. (Join-Path $IdfPath 'export.ps1')

# ESP-IDF 6.0.2 enables ccache during activation on this workstation. The
# sandbox can run the compiler directly, but ccache cannot reliably create its
# compiler child process there. Override both the environment and CLI setting.
$env:IDF_CCACHE_ENABLE = '0'

$sourceCompiler = (Get-Command riscv32-esp-elf-gcc -ErrorAction Stop).Source
$sourceCppCompiler = (Get-Command riscv32-esp-elf-g++ -ErrorAction Stop).Source
$sourceNinja = (Get-Command ninja -ErrorAction Stop).Source
$python = Join-Path $IdfPythonEnvPath 'Scripts\python.exe'
$idfPy = Join-Path $IdfPath 'tools\idf.py'

# The ESP 15.2 toolchain's gcc/as/objdump dispatchers determine their own path
# through a Windows process API that the sandbox denies for external binaries.
# Running the gcc driver from the writable build tree fixes that lookup. Point
# it back to the installed libraries and replace only the affected as/objdump
# dispatchers with their concrete ESP32-P4 (xespv2p1) implementations.
$sourceBin = Split-Path -Parent $sourceCompiler
$toolchainRoot = Split-Path -Parent $sourceBin
$shimPath = Join-Path $buildPath 'sandbox-toolchain'
New-Item -ItemType Directory -Path $shimPath -Force | Out-Null

$compiler = Join-Path $shimPath 'riscv32-esp-elf-gcc.exe'
$cppCompiler = Join-Path $shimPath 'riscv32-esp-elf-g++.exe'
$ninja = Join-Path $shimPath 'ninja.exe'
$assembler = Join-Path $shimPath 'riscv32-esp-elf-as.exe'
$shortAssembler = Join-Path $shimPath 'as.exe'
$objdump = Join-Path $shimPath 'riscv32-esp-elf-objdump.exe'

Copy-Item -LiteralPath $sourceCompiler -Destination $compiler -Force
Copy-Item -LiteralPath $sourceCppCompiler -Destination $cppCompiler -Force
Copy-Item -LiteralPath $sourceNinja -Destination $ninja -Force
Copy-Item -LiteralPath (Join-Path $sourceBin 'riscv32-esp-elf-as-xespv2p1.exe') `
    -Destination $assembler -Force
Copy-Item -LiteralPath $assembler -Destination $shortAssembler -Force
Copy-Item -LiteralPath (Join-Path $sourceBin 'riscv32-esp-elf-objdump-xespv2p1.exe') `
    -Destination $objdump -Force

foreach ($binutil in @(
        'riscv32-esp-elf-addr2line.exe',
        'riscv32-esp-elf-ar.exe',
        'riscv32-esp-elf-gcc-ar.exe',
        'riscv32-esp-elf-gcc-nm.exe',
        'riscv32-esp-elf-gcc-ranlib.exe',
        'riscv32-esp-elf-ld.exe',
        'riscv32-esp-elf-nm.exe',
        'riscv32-esp-elf-objcopy.exe',
        'riscv32-esp-elf-ranlib.exe',
        'riscv32-esp-elf-readelf.exe',
        'riscv32-esp-elf-size.exe',
        'riscv32-esp-elf-strip.exe'
    )) {
    Copy-Item -LiteralPath (Join-Path $sourceBin $binutil) `
        -Destination (Join-Path $shimPath $binutil) -Force
}

$env:GCC_EXEC_PREFIX = (Join-Path $toolchainRoot 'lib\gcc\')
$env:COMPILER_PATH = $shimPath
$env:PATH = "$shimPath;$env:PATH"
$sysroot = (Join-Path $toolchainRoot 'riscv32-esp-elf').Replace('\', '/')

# Avoid global git configuration changes for the sandbox identity while still
# allowing ESP-IDF and its nested OpenThread checkout to report versions.
$env:GIT_CONFIG_COUNT = '3'
$env:GIT_CONFIG_KEY_0 = 'safe.directory'
$env:GIT_CONFIG_VALUE_0 = $projectRoot.Replace('\', '/')
$env:GIT_CONFIG_KEY_1 = 'safe.directory'
$env:GIT_CONFIG_VALUE_1 = $IdfPath.Replace('\', '/')
$env:GIT_CONFIG_KEY_2 = 'safe.directory'
$env:GIT_CONFIG_VALUE_2 = (Join-Path $IdfPath 'components\openthread\openthread').Replace('\', '/')

$idfArguments = @(
    '--no-ccache',
    '-B', $buildPath,
    '-D', "CMAKE_PROGRAM_PATH=$shimPath",
    '-D', "CMAKE_MAKE_PROGRAM=$ninja",
    '-D', "CMAKE_C_COMPILER=$compiler",
    '-D', "CMAKE_CXX_COMPILER=$cppCompiler",
    '-D', "CMAKE_ASM_COMPILER=$compiler",
    '-D', "CMAKE_OBJDUMP=$objdump",
    '-D', "CMAKE_C_FLAGS=--sysroot=$sysroot",
    '-D', "CMAKE_CXX_FLAGS=--sysroot=$sysroot",
    '-D', "CMAKE_ASM_FLAGS=--sysroot=$sysroot",
    '-D', "CMAKE_EXE_LINKER_FLAGS=--sysroot=$sysroot",
    'build'
)

Write-Host "Building Project TARS from $projectRoot"
Write-Host 'ccache: disabled (sandbox-compatible)'
Write-Host "toolchain shim: $shimPath"
& $python $idfPy @idfArguments
if ($LASTEXITCODE -ne 0) {
    throw "ESP-IDF build failed with exit code $LASTEXITCODE"
}
