# Project TARS — Firmware Build Guide

**Status:** Reproducible Windows build procedure

**Validated:** 2026-08-20 with ESP-IDF 6.0.2 and ESP32-P4

---

# Recommended Command

From the repository root, run:

```powershell
.\tools\build-firmware.ps1
```

For a completely fresh configuration and rebuild:

```powershell
.\tools\build-firmware.ps1 -Clean
```

The script validates the build directory before `-Clean` removes it. It refuses
to remove a file, link, reparse point, path outside the repository, or directory
whose name is not exactly `build`.

# Why the Wrapper Is Required

The ESP-IDF 6.0.2 activation installed on this workstation sets
`IDF_CCACHE_ENABLE=1`. In the Codex filesystem/process sandbox, `ccache` cannot
reliably start the compiler as a child process. The ESP 15.2 RISC-V toolchain
also uses Rust dispatch programs for `gcc`, `as`, and `objdump`; their Windows
path lookup receives access-denied when the dispatcher runs outside the
writable workspace. Typical symptoms are:

```text
CreateProcess failed: The system cannot find the file specified.
The C compiler identification is unknown.
Failed to get path name. Error code: 5
```

This is not a Project TARS source-code or compiler installation failure. The
repository wrapper makes the build independent of that inherited setting by:

- activating the pinned ESP-IDF 6.0.2 environment;
- explicitly disabling `ccache` in both the environment and `idf.py` command;
- resolving and supplying full paths for Ninja and the RISC-V C, C++, and
  assembler compilers;
- creating a generated `build/sandbox-toolchain/` compatibility directory that
  runs the GCC drivers inside the workspace and directly selects the ESP32-P4
  `xespv2p1` assembler/objdump implementations;
- pointing the copied driver back to the installed compiler libraries, so the
  complete 3+ GiB toolchain is not duplicated;
- forwarding the same Ninja, compiler, binutils and sysroot settings into
  ESP-IDF's nested bootloader configuration;
- supplying process-local Git safe-directory entries for the repository,
  ESP-IDF, and its nested OpenThread checkout;
- using the repository's normal ignored `build/` directory.

Do not troubleshoot this symptom by repeatedly reinstalling the compiler or by
weakening the sandbox. Use the wrapper first.

The compatibility directory is generated, ignored by Git, and recreated on
every build. No files in the global ESP-IDF installation are changed.

# Installation Paths

The current workstation defaults are:

| Component | Default path |
|---|---|
| ESP-IDF | `C:\esp\v6.0.2\esp-idf` |
| ESP-IDF tool registry | `C:\Users\zs1gf\.espressif` |
| ESP-IDF Python environment | `C:\Espressif\tools\python\v6.0.2\venv` |

These can be overridden without editing the script:

```powershell
.\tools\build-firmware.ps1 `
    -IdfPath 'D:\esp\esp-idf' `
    -IdfToolsPath 'D:\esp\tools' `
    -IdfPythonEnvPath 'D:\esp\python-env'
```

# Expected Success Evidence

A successful build ends with `Project build complete` and creates:

```text
build/project_tars.bin
build/project_tars.elf
build/bootloader/bootloader.bin
build/partition_table/partition-table.bin
```

The build proves configuration, compilation, linking and image generation. It
does not prove physical microphone, LCD, Wi-Fi or PSRAM behavior; those require
flashing the P4 and collecting runtime logs.
