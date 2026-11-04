# ArcheAge Chronicles: Proton launch fix

For Linux players getting this error when starting ArcheAge Chronicles through Steam:

> The procedure entry point SystemTimeToTzSpecificLocalTimeEx could not be located in the dynamic link library KERNEL32.dll.

This adds the missing Windows timezone function to a **separate copy of Proton**. It does not replace your normal Proton installation or patch the game or anti-cheat.

**Experimental:** tested with native Steam on CachyOS and `proton-cachyos-11.0-20261015`. The original workaround got the player into the game. Other setups and future game/anti-cheat updates are not guaranteed. Only Linux x86-64 is supported; **Flatpak Steam is not supported by the installer**.

## Easy installation

You do not need an AI assistant, compiler, Git, or Windows tools. Setup downloads the repository and its prebuilt DLL/test program for you.

### 1. Close Steam

Exit the game, then use **Steam → Exit**. Closing just the Steam window may leave it running in the tray.

### 2. Download and run setup

Open a terminal, paste these lines, and press Enter:

```sh
curl -fL --proto '=https' --proto-redir '=https' -o archeage-setup.sh \
  https://raw.githubusercontent.com/codecorsair/archeage-proton-fix/main/setup.sh &&
sh archeage-setup.sh
```

This saves the script before running it; it is not a `curl | sh` pipeline. You are trusting code from this repository, so review the saved file first if you prefer.

If `curl` is missing, [save setup.sh using your browser](https://raw.githubusercontent.com/codecorsair/archeage-proton-fix/main/setup.sh), open a terminal in its folder, and run `sh setup.sh` instead.

### 3. Follow the prompts

Setup checks installation requirements. If system tools are missing, it shows the exact package-manager command and asks before using `sudo`. Press **Enter** to decline. It never silently installs packages or runs the game installer as root.

It downloads the source and prebuilt assets to a new `~/.local/share/archeage-proton-fix-setup` folder, verifies their checksums, and opens the guided installer. If run from an already-downloaded repository, it uses that checkout instead.

The guided installer finds Steam and the game's library, lets you choose a base Proton, shows its planned paths, and asks permission again. If available, `proton-cachyos-slr` is the tested base; other versions are unverified.

After approval, it may download the Python helper `pefile` into a local `.venv`. It then copies Proton, backs up the game's Windows settings/saves folder (its **prefix**), patches only the copy, and adds `tzcompat.dll` to this game's prefix.

Copying/backups can take several minutes and may need a few GB of free space. Existing setup destinations, installations, and backups are **never overwritten**. Keep the prefix backup until you are happy with the result.

**ZIP alternative:** use **Code → Download ZIP**, extract it, open a terminal in that folder, and run `sh setup.sh`. Advanced users can still run `python3 install.py` directly.

### 4. Select it in Steam

Start Steam, then:

1. Right-click **ArcheAge Chronicles** in your Library.
2. Open **Properties → Compatibility**.
3. Enable **Force the use of a specific Steam Play compatibility tool**.
4. Choose **Proton ArcheAge TZ Fix (experimental)**.
5. Close Properties and launch the game.

If that option is missing, fully exit and restart Steam. First-time shader compilation may take a while. “Installed” means the files were prepared, not that online compatibility has been verified on your machine.

## Check requirements or build your own DLL

The same script can check your machine without downloading the repo or installing packages:

```sh
sh archeage-setup.sh --check           # Separate installation and build results
sh archeage-setup.sh --check --install # Prebuilt-DLL installation only
sh archeage-setup.sh --check --build   # Source-build tools only
```

Inside a downloaded repository, use `sh setup.sh` instead of `sh archeage-setup.sh`.

- **Prebuilt installation:** Python 3.9+, GNU coreutils, and either an existing `pefile` helper or working Python `venv`/pip. Downloading also needs curl or wget, tar, and gzip.
- **Building:** Bash, GNU coreutils, Clang with the Windows x86-64 target, `llvm-dlltool`, and `lld-link`. No Windows SDK, MSVC, GCC, or CMake is needed.

The build check performs a temporary Windows compile/link test, not just a command-name check. Installation/build results are separate: missing compiler tools do **not** prevent using the prebuilt DLL. Temporary checks are cleaned up.

Automatic package offers cover apt, dnf, and pacman. openSUSE/zypper and Alpine/apk receive manual guidance because Python and LLVM package names vary by release. Checks still report the actual missing tools. This is not a claim that the game or setup has been tested on every distro. See the [tool table and build instructions](docs/advanced.md#build-from-source) for details.

## Undo the change

Exit the game and select your **original Proton version** under **Properties → Compatibility**. That is enough to stop using this workaround.

The extra DLL is unused by the original Proton. You can leave the backup and private runtime alone. For optional cleanup or prefix restoration, see [advanced instructions](docs/advanced.md#roll-back). Do not restore an older prefix over newer saves/settings without preserving them first.

## Troubleshooting

**`python3: command not found`, or errors mentioning `venv`, `ensurepip`, or `pip`**

Rerun `sh setup.sh` from the downloaded repo so it can check prerequisites and offer installation. If you prefer to install Python tools manually:

```bash
# Ubuntu / Debian
sudo apt install python3 python3-venv python3-pip

# Arch / CachyOS
sudo pacman -S --needed python python-pip
```

Use only the command for your distribution. Run `setup.sh` and `install.py` **without sudo**; only a separately confirmed package-manager command may use it.

**It asks me to close Steam, but the window is closed**

Use Steam's tray icon to choose Exit. The installer will not terminate Steam or the game for you.

**It cannot find the game prefix**

Launch the game once through Steam, dismiss the error, then exit Steam and rerun the installer. If needed, specify paths using the [advanced options](docs/advanced.md#installer-options).

**It says “Already exists”**

If setup's download folder exists, open it and run `sh setup.sh` there rather than downloading over it. For a different download location, use `sh archeage-setup.sh --directory "$HOME/Downloads/archeage-proton-fix-new"`.

The guided installer may also find a prior private runtime, backup, or `tzcompat.dll` and stop without overwriting it. If the workaround is already installed, select it in Steam instead of reinstalling. If this is from an interrupted attempt, keep the backup and open an issue with the error text before deleting anything.

**A lock file exists after an interruption**

Do not run two installers at once. If no installer is running, open an issue with the message and paths before removing the lock or retrying.

**It reports a checksum error or unsupported DLL/layout**

Stop. Download a fresh ZIP for a checksum error. For unsupported runtimes, use the tested base if available or report your Proton version. Do not bypass the safety checks or replace shared Windows DLLs.

**A new error appears, or the game still will not start**

Switch back to your original Proton and [open an issue](https://github.com/codecorsair/archeage-proton-fix/issues). Include your distro, Steam installation type, selected base Proton, installer error text, and the new game error. Never share passwords, Steam tokens, or your entire prefix.

## What is included?

`tzcompat.dll` is custom-built from the C source in this repository. It supplies the missing function using timezone APIs Wine already supports. It is not an official Microsoft, Valve, or game-publisher DLL.

No Proton/Wine DLLs, game files, or anti-cheat files are distributed here. Checksums detect artifact changes relative to the checkout; they are not a signature or an independent guarantee of trust. The installer does not bypass anti-cheat, and there is **no guarantee of anti-cheat acceptance or account safety**.

For manual installation, building from source, tests, exact file changes, or AI-assisted automation, see [advanced instructions](docs/advanced.md).

Original code and the included shim/test binaries are [MIT licensed](LICENSE).
