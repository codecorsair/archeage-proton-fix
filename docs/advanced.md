# Advanced instructions

For the guided setup, start with the [main README](../README.md). All commands below run from the repository root, not from this `docs/` folder.

## Standalone setup and dependency checks

`setup.sh` is a POSIX-shell bootstrap. A standalone copy downloads the fixed GitHub repository archive and its checked-in `bin/tzcompat.dll` and `bin/probe.exe`; it does not require Git or fetch a separate release. An in-repository copy reuses its checkout.

```sh
sh setup.sh --check           # Installation and source-build groups
sh setup.sh --check --install # Installation requirements only
sh setup.sh --check --build   # Build requirements only
```

Check mode never downloads the repository or installs packages. It may create temporary compiler/Python probes and removes its own scratch files. Exit 0 means the requested checks passed; a nonzero result names missing or unusable tools. A compiler failure is separate from installation readiness.

Default `sh setup.sh` checks prebuilt-install prerequisites, offers a displayed package-manager command with default-no consent when appropriate, and hands off to `install.py`. System package installation may use `sudo`; the Python installer never runs as root. Packages/repositories vary by distribution and release, so an unsuccessful package command stops rather than adding repositories or retrying unrelated managers.

For a standalone script, choose a different **new** download directory with:

```sh
sh setup.sh --directory "$HOME/Downloads/archeage-proton-fix-new"
```

The default is `~/.local/share/archeage-proton-fix-setup`. Downloaded artifacts are checked against their archive's `SHA256SUMS`, which detects mismatches, not a compromised source repository. HTTPS plus trusting this repository is the download trust model; the checksums are not signatures. The script does not rewrite shell profiles, stop Steam, or install compiler packages just to use the prebuilt DLL.

The original game/runtime validation was on CachyOS with native Steam. Distro-family dependency support and simulated package-manager tests are not equivalent to testing Steam or the game on those systems. Alpine/musl dependency detection in particular does not establish Steam runtime compatibility.

### Distribution caveats

Package hints are based on official metadata, not on installations performed on each distro:

| Family | Notes |
| --- | --- |
| Debian / Ubuntu | Python helpers normally use `python3-venv` and `python3-pip`; source tools are `clang`, `llvm`, and `lld`. See [LLVM's distro packages](https://apt.llvm.org/). |
| Fedora / RHEL | Fedora has the usual `clang`, `llvm`, and `lld` packages. RHEL availability depends on enabled repositories/subscriptions; setup does not add EPEL or other repositories. See [Fedora LLVM](https://packages.fedoraproject.org/pkgs/llvm/) and [EPEL prerequisites](https://docs.fedoraproject.org/en-US/epel/getting-started/). |
| Arch / CachyOS | Python packages use `python` and `python-pip`; LLVM tools use `clang`, `llvm`, and `lld`. See [Arch LLVM](https://archlinux.org/packages/extra/x86_64/llvm/). |
| openSUSE | Python defaults and package names vary significantly. Leap 15.6's Python 3.6 is too old; installing an arbitrary newer interpreter does not safely change `python3`. Tumbleweed currently packages a newer versioned Python. Do not replace the system Python to satisfy setup. |
| Alpine | LLVM packages are versioned by branch, such as `clang20`/`llvm20`/`lld20` on 3.22. Command providers and names vary; see [Alpine LLVM metadata](https://pkgs.alpinelinux.org/package/v3.22/main/x86_64/llvm20). GNU coreutils is required because BusyBox `cp` is not a substitute for `cp --reflink=auto`. |

The Python `pefile` dependency stays in the installer's local venv when needed; system `python3-pefile` packages are not required. The checker tests what is actually executable on `PATH`, rather than treating a package-manager name as proof that it works.

## Installer options

The guided installer uses plain terminal prompts and needs no extra UI libraries. It auto-detects native Steam, game libraries, and Proton runtimes with the tested directory layout.

Preview a setup without changing files or downloading helpers:

```bash
python3 install.py --dry-run
```

For automation, provide explicit paths and approve with `--yes`:

```bash
python3 install.py --yes \
  --steam-root "$HOME/.local/share/Steam" \
  --library "/mnt/games/SteamLibrary" \
  --proton "/usr/share/steam/compatibilitytools.d/proton-cachyos-slr"
```

Use `--dry-run` with those flags to preview that exact setup. `--yes` authorizes both installation and a local `.venv`/PyPI helper download if needed. The game and Steam must be fully closed for installation; dry runs can run while they are open. Missing/ambiguous paths fail rather than guessing in automation. Exit 0 means completed/cancelled/dry-run as printed, 1 means failure, and 130 means interruption.

The installer verifies the supplied artifacts, refuses existing outputs, preflights the Wine export patch, stages the private runtime, makes a complete prefix backup, then adds the shim and exposes the custom runtime. Ordinary failures remove its temporary copy and any shim it just added; completed backups are retained. A forced process termination or power loss can leave a temporary directory/lock: preserve those and investigate rather than deleting unknown state.

The private runtime contains `archeage-tz-install.json` with local provenance and backup paths. Do not upload that file or the prefix when publishing reports.

Experimental Linux/x86-64 workaround for this launch error in Steam app **3218230**:

> The procedure entry point SystemTimeToTzSpecificLocalTimeEx could not be located in the dynamic link library KERNEL32.dll.

This repository contains an original `tzcompat.dll`, its C source, a Wine export patcher, and tests. It does **not** contain a patched `kernel32.dll`, Proton distribution, game files, or anti-cheat files.

## What it does

The tested Proton runtime lacks this export in `kernel32.dll`. Its `kernelbase.dll` export is an unimplemented stub, so forwarding there does not fix the problem.

The workaround adds one export to a **private copy** of Proton's x64 `kernel32.dll`:

```text
SystemTimeToTzSpecificLocalTimeEx -> tzcompat.SystemTimeToTzSpecificLocalTimeEx
```

The shim uses existing Wine timezone APIs to obtain the applicable rules and convert UTC to local time. It handles a supplied timezone, the current timezone, historical DST rules, and input/output aliasing. This is a small compatibility implementation, not a complete Windows API conformance claim.

## Tested scope and risks

- Verified on CachyOS, native Steam, and `proton-cachyos-11.0-20261015 (steam linux runtime)`.
- The original workaround reached shader compilation; interactive testing confirmed entry into the game. The packaged build also passes the native API probe.
- This addresses **one launch error**, not every Proton or anti-cheat issue. There is no guarantee about future updates, continued online compatibility, or anti-cheat acceptance/account safety.
- It does not disable or bypass anti-cheat. No game or anti-cheat binary is patched.
- Only **x86-64** is supported. Flatpak Steam and other Proton layouts have not been validated.
- The patcher refuses native Windows DLLs, signed DLLs, already-exported functions, and DLLs without spare section-header space. If it refuses your runtime, stop rather than removing the checks.
- Use a separate Proton copy for this game. Never replace a shared/runtime-package DLL or download a Microsoft `kernel32.dll` to use with Wine.

## Install using the included DLL

Run the commands from the repository root, in the **same Bash terminal**. Fully exit the game and Steam first. Backups and the custom runtime may need several GB of disk space.

### 1. Verify artifacts and set up Python

```bash
set -euo pipefail
sha256sum -c SHA256SUMS
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

`bin/tzcompat.dll` and `bin/probe.exe` are built from the supplied source. Checksums detect changes relative to this checkout; they are not a signature or independent proof of trust. Build from source below if you prefer.

### 2. Set your paths

Edit these values for your installation. `STEAM_ROOT` is Steam's installation directory; `LIBRARY` is the library containing this game. They can be different.

```bash
STEAM_ROOT="$HOME/.local/share/Steam"
LIBRARY="$STEAM_ROOT"
BASE_PROTON="/usr/share/steam/compatibilitytools.d/proton-cachyos-slr"
CUSTOM="$STEAM_ROOT/compatibilitytools.d/Proton-ArcheAge-TZ-Fix"
APP_COMPAT="$LIBRARY/steamapps/compatdata/3218230"
PREFIX="$APP_COMPAT/pfx"
```

This procedure expects `BASE_PROTON/files/lib/wine/x86_64-windows/kernel32.dll`. If your runtime uses a different layout, these commands are not validated for it. Launch the game once normally and exit it if its prefix does not exist yet.

### 3. Back up the prefix and copy Proton

```bash
test -d "$PREFIX/drive_c/windows/system32"
test -f "$BASE_PROTON/proton"
test ! -e "$CUSTOM"
test ! -e "$APP_COMPAT.before-tz-fix"
cp -a --reflink=auto "$APP_COMPAT" "$APP_COMPAT.before-tz-fix"
mkdir -p "$STEAM_ROOT/compatibilitytools.d"
cp -a --reflink=auto "$BASE_PROTON" "$CUSTOM"
cp compatibilitytool.vdf "$CUSTOM/compatibilitytool.vdf"
```

These checks intentionally stop if a prior installation or backup exists. Do not overwrite either just to rerun the procedure.

### 4. Patch only the private DLL and add the shim

```bash
ORIGINAL_DLL="$BASE_PROTON/files/lib/wine/x86_64-windows/kernel32.dll"
PRIVATE_DLL="$CUSTOM/files/lib/wine/x86_64-windows/kernel32.dll"
test -f "$PRIVATE_DLL"
test ! -L "$PRIVATE_DLL"
mkdir -p build
python3 add_forwarder.py "$ORIGINAL_DLL" build/kernel32.patched.dll
cp -p "$PRIVATE_DLL" build/kernel32.original.dll
chmod u+w "$PRIVATE_DLL"
cp build/kernel32.patched.dll "$PRIVATE_DLL"
chmod u-w "$PRIVATE_DLL"

test ! -e "$PREFIX/drive_c/windows/system32/tzcompat.dll"
cp bin/tzcompat.dll "$PREFIX/drive_c/windows/system32/tzcompat.dll"
```

Keep `tzcompat.dll` in this **game's prefix**, not the game directory or shared Proton installation. A prefix reset/recreation will remove it; restore it from `bin/` afterward. Switching to a newer base Proton requires making a new private copy and reapplying the patch.

### 5. Verify and select the custom Proton

With the game still closed, run the API probe:

```bash
STEAM_COMPAT_CLIENT_INSTALL_PATH="$STEAM_ROOT" \
STEAM_COMPAT_DATA_PATH="$APP_COMPAT" \
WINEDEBUG=-all \
"$CUSTOM/proton" run "$PWD/bin/probe.exe"
printf 'Timezone API probe passed\n'
```

Exit **0** is success. The probe checks northern/southern DST, the 2007 US rule change, year rollover, aliasing, current timezone, and error cases. Exit **41** means the export is still missing. Other nonzero exits indicate failed cases or a Wine/runtime failure. A missing Linux-library/container error is a setup failure, not a passing probe; direct execution may need adaptation on other distributions.

Start Steam, then open **ArcheAge Chronicles → Properties → Compatibility**, enable the compatibility override, and select **Proton ArcheAge TZ Fix (experimental)**. If it is missing from the list, fully restart Steam.

Launch the game. Initial shader compilation can take time. Getting past the DLL dialog alone is not proof that online play works.

## Build from source

These are the actual source-build tools, separate from installation prerequisites:

| Tool | Purpose |
| --- | --- |
| Bash | Runs `build.sh` with its existing shell semantics. |
| GNU coreutils | Supplies `realpath`, `mkdir`, and `dirname`; setup/install also need `cp --reflink=auto` and `sha256sum`. |
| `clang` | Compiles C into Windows x86-64 COFF objects with `--target=x86_64-pc-windows-msvc`. |
| `llvm-dlltool` | Creates a Kernel32 import library from the project's `.def` declarations. |
| `lld-link` | Links Windows DLL/EXE output without an external C runtime. |

Run the checker, then build into a new directory:

```bash
sh setup.sh --check --build
bash build.sh build/from-source
```

The checker exercises a Windows-target compile/import-library/link sequence. Tool names must be available exactly as above because those are what `build.sh` invokes. If your distro installs versioned commands only, expose the matching LLVM toolchain's `bin` directory on `PATH` or follow the checker's package hints. Merely finding `clang` is insufficient if its Windows target or COFF linker support is missing.

Python **3.9+**, `venv`/pip (unless the helper already exists), and the pinned `pefile` dependency are needed separately for installing/patching/testing the Wine DLL, not for compiling these C files. Downloading setup needs curl or wget with HTTPS support, tar, and gzip. No Windows SDK, MSVC, GCC, CMake, MinGW SDK, or external C runtime is required.

The output directory must be new. This produces `tzcompat.dll`, `probe.exe`, and intermediate import/object files without modifying any installed runtime or prefix. To use your build, substitute `build/from-source/tzcompat.dll` and `build/from-source/probe.exe` for the `bin/` paths above.

The checked-in binaries use Clang/LLD **23.1.4** and a zero PE linker timestamp. Two fresh builds with that toolchain produced byte-identical DLL/probe files. Different compiler versions may produce different hashes without changing behavior.

## Test the export patcher

Use the **unmodified** DLL from your base runtime, not the private patched DLL:

```bash
source .venv/bin/activate
export KERNEL32_DLL="$BASE_PROTON/files/lib/wine/x86_64-windows/kernel32.dll"
python3 -m unittest -v
python3 -O -m unittest -v
```

Tests check existing named/ordinal exports, forwarders, section bytes, COFF symbol offsets, the PE checksum, and refusal of native/signed DLLs and duplicate patching. Installer tests use temporary Steam/Proton fixtures containing a real unmodified Wine DLL, validate backups and failure cleanup, and do not install into your real Steam directories. The native probe above is a separate behavior test; Python tests alone do not validate the C implementation.

## Roll back

1. Exit the game. In Steam's Compatibility settings, select your original Proton version. If you reset the override, Steam will choose its normal default.
2. The new `tzcompat.dll` is unused by the original Proton. You may leave it there or remove **only that file** from this game's prefix.
3. Keep the prefix backup until you are satisfied with the result. Do not restore an old prefix over newer saves/settings without preserving them first.
4. The private `Proton-ArcheAge-TZ-Fix` directory can be removed once no game is using it. Shared Proton and the game's original binaries were never replaced.

## Files and license

- `tzcompat.c`, `timezone.h`: original compatibility implementation and ABI declarations.
- `add_forwarder.py`: preserves old exports while adding a PE forwarding export.
- `probe.c`, `test_patch.py`: native behavior and PE-preservation tests.
- `setup.sh`: checks requirements or downloads/prepares the prebuilt-install route with explicit consent.
- `test_setup.py`: dependency/bootstrap failure and safety tests using isolated command stubs.
- `build.sh`: builds the shim/probe without changing an installation.
- `bin/`, `SHA256SUMS`: prebuilt x64 artifacts and integrity checks.
- `compatibilitytool.vdf`: distinct Steam compatibility-tool registration.

Original source and included shim/probe binaries are **MIT licensed**; see [LICENSE](../LICENSE). This does not relicense Wine/Proton, Python dependencies, the game, or anti-cheat software. Patched Wine DLLs are generated locally and are intentionally not distributed here.
