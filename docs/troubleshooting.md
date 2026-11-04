# Troubleshooting

[Back to installation](../README.md#install)

## Download without curl

[Save setup.sh using your browser](https://raw.githubusercontent.com/codecorsair/archeage-proton-fix/main/setup.sh), open a terminal in its folder, and run `sh setup.sh`.

Or use **Code → Download ZIP**, extract it, open a terminal in that folder, and run `sh setup.sh`. Advanced users can still run `python3 install.py` directly.

You are trusting code from this repository, so review the saved file first if you prefer. Checksums detect artifact changes relative to the checkout; they are not a signature or an independent guarantee of trust.

## Python, venv, ensurepip, or pip is missing

Rerun `sh setup.sh` from the downloaded repo so it can check prerequisites and offer installation. If you prefer to install Python tools manually:

```bash
# Ubuntu / Debian
sudo apt install python3 python3-venv python3-pip

# Arch / CachyOS
sudo pacman -S --needed python python-pip
```

Use only the command for your distribution. Run `setup.sh` and `install.py` **without sudo**; only a separately confirmed package-manager command may use it.

Automatic package offers cover apt, dnf, and pacman. openSUSE/zypper and Alpine/apk receive [manual guidance](advanced.md#distribution-caveats) because Python and LLVM package names vary by release.

## Steam still appears to be running

Use Steam's tray icon to choose Exit. The installer will not terminate Steam or the game for you.

## Game prefix not found

Launch the game once through Steam, dismiss the error, then exit Steam and rerun the installer. If needed, specify paths using the [advanced options](advanced.md#installer-options).

## “Already exists”

If setup's download folder exists, open it and run `sh setup.sh` there rather than downloading over it. For a different download location, use `sh archeage-setup.sh --directory "$HOME/Downloads/archeage-proton-fix-new"`.

The guided installer may also find a prior private runtime, backup, or `tzcompat.dll` and stop without overwriting it. If the workaround is already installed, select it in Steam instead of reinstalling. If this is from an interrupted attempt, keep the backup and open an issue with the error text before deleting anything.

## Lock file after an interruption

Do not run two installers at once. If no installer is running, open an issue with the message and paths before removing the lock or retrying.

## Checksum error or unsupported DLL/layout

Stop. Download a fresh ZIP for a checksum error. For unsupported runtimes, use the tested base if available or report your Proton version. Do not bypass the safety checks or replace shared Windows DLLs.

## A new error or failed launch

Switch back to your original Proton and [open an issue](https://github.com/codecorsair/archeage-proton-fix/issues). Include your distro, Steam installation type, selected base Proton, installer error text, and the new game error. Never share passwords, Steam tokens, or your entire prefix.

“Installed” means the files were prepared, not that online compatibility has been verified on your machine. See [tested scope and risks](advanced.md#tested-scope-and-risks).
