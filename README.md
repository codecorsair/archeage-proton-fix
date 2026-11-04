# ArcheAge Chronicles: Proton launch fix

For Linux players getting this error when starting ArcheAge Chronicles through Steam:

> The procedure entry point SystemTimeToTzSpecificLocalTimeEx could not be located in the dynamic link library KERNEL32.dll.

This adds the missing Windows timezone function to a **separate copy of Proton**. It does not replace your normal Proton installation or patch the game or anti-cheat.

**Experimental:** tested with native Steam on CachyOS and `proton-cachyos-11.0-20261015`. The original workaround got the player into the game. Other setups and future game/anti-cheat updates are not guaranteed. Only Linux x86-64 is supported; **Flatpak Steam is not supported by the installer**.

## Easy installation

You do not need an AI assistant, compiler, Git, or Windows tools. The required DLL is included.

### 1. Download and unpack

On [this repository's page](https://github.com/codecorsair/archeage-proton-fix), click **Code → Download ZIP**, then extract it using your file manager.

Open the extracted folder. Right-click an empty area and choose **Open Terminal Here** (your file manager may call it something similar).

### 2. Close Steam

Exit the game, then use **Steam → Exit**. Closing just the Steam window may leave it running in the tray.

### 3. Run the installer

Copy this one line into that terminal and press Enter:

```bash
python3 install.py
```

The installer will:

1. Check the included DLL and test program against their checksums.
2. Find native Steam and the game's library, including libraries on other drives.
3. Let you pick a base Proton if several are installed. If available, `proton-cachyos-slr` is the tested base. Other versions are unverified.
4. Show where the separate runtime and prefix backup will go, then ask permission. Press **Enter** to cancel, or type **y** and Enter to continue.
5. If needed, download one Python helper (`pefile`) from PyPI into a local `.venv` folder. It never uses `sudo` or installs Python packages system-wide.
6. Copy Proton, back up the game's Windows settings/saves folder (its **prefix**), patch only the copy, and add `tzcompat.dll` to this game's prefix.

Copying/backups can take several minutes and may need a few GB of free space. Existing installations and backups are **never overwritten**. Keep the prefix backup until you are happy with the result.

### 4. Select it in Steam

Start Steam, then:

1. Right-click **ArcheAge Chronicles** in your Library.
2. Open **Properties → Compatibility**.
3. Enable **Force the use of a specific Steam Play compatibility tool**.
4. Choose **Proton ArcheAge TZ Fix (experimental)**.
5. Close Properties and launch the game.

If that option is missing, fully exit and restart Steam. First-time shader compilation may take a while. “Installed” means the files were prepared, not that online compatibility has been verified on your machine.

## Undo the change

Exit the game and select your **original Proton version** under **Properties → Compatibility**. That is enough to stop using this workaround.

The extra DLL is unused by the original Proton. You can leave the backup and private runtime alone. For optional cleanup or prefix restoration, see [advanced instructions](docs/advanced.md#roll-back). Do not restore an older prefix over newer saves/settings without preserving them first.

## Troubleshooting

**`python3: command not found`, or errors mentioning `venv`, `ensurepip`, or `pip`**

Install your distribution's Python tools, then rerun the installer:

```bash
# Ubuntu / Debian
sudo apt install python3 python3-venv python3-pip

# Arch / CachyOS
sudo pacman -S --needed python python-pip
```

Use only the command for your distribution. The installer itself should always run **without sudo**.

**It asks me to close Steam, but the window is closed**

Use Steam's tray icon to choose Exit. The installer will not terminate Steam or the game for you.

**It cannot find the game prefix**

Launch the game once through Steam, dismiss the error, then exit Steam and rerun the installer. If needed, specify paths using the [advanced options](docs/advanced.md#installer-options).

**It says “Already exists”**

It found a prior private runtime, backup, or `tzcompat.dll` and stopped without overwriting it. If the workaround is already installed, select it in Steam instead of reinstalling. If this is from an interrupted attempt, keep the backup and open an issue with the error text before deleting anything.

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
