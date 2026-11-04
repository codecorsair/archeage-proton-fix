# ArcheAge Chronicles: Proton launch fix

For Linux players getting this Steam launch error:

> The procedure entry point SystemTimeToTzSpecificLocalTimeEx could not be located in the dynamic link library KERNEL32.dll.

Uses a **private copy of Proton** without replacing shared Proton or patching the game or anti-cheat. Setup uses the included DLL; no compiler is needed.

**Experimental:** Linux x86-64 with native Steam only. Flatpak is unsupported. Tested on CachyOS; other setups are unverified. There is no guarantee of anti-cheat acceptance or account safety.

## Install

1. Exit the game and use **Steam → Exit**, not just close the window.
2. Open a terminal and run:

```sh
curl -fL --proto '=https' --proto-redir '=https' -o archeage-setup.sh \
  https://raw.githubusercontent.com/codecorsair/archeage-proton-fix/main/setup.sh &&
sh archeage-setup.sh
```

Run **without sudo**. Setup downloads the repo and DLL, checks requirements, and asks before installing system packages. The installer backs up the game's Windows settings/saves and never overwrites existing installations or backups.

3. Follow the prompts. If available, choose `proton-cachyos-slr`, the tested base Proton.
4. Start Steam and right-click **ArcheAge Chronicles**:
   - Open **Properties → Compatibility**.
   - Enable **Force the use of a specific Steam Play compatibility tool**.
   - Choose **Proton ArcheAge TZ Fix (experimental)** and launch the game.

If the option is missing, fully restart Steam. First-time shader compilation may take a while. Allow a few GB of free space for the Proton copy and backup.

Missing curl? See [other download options](docs/troubleshooting.md#download-without-curl).

## Check dependencies

Without downloading the repo or installing packages:

```sh
sh archeage-setup.sh --check
```

Use `--check --install` or `--check --build` to check one group. Missing build tools do not prevent using the prebuilt DLL.

If your script is named `setup.sh`, use `sh setup.sh --check`.

## Undo

Exit the game and select your **original Proton version** under **Properties → Compatibility**. The added DLL is unused by the original Proton.

Keep the backup until you are happy with the result. See [cleanup and restoration](docs/advanced.md#roll-back) before restoring an older prefix over newer saves/settings.

## More help

- [Troubleshooting](docs/troubleshooting.md)
- [Build tools and source builds](docs/advanced.md#build-from-source)
- [Manual installation and technical details](docs/advanced.md)
- [Report a problem](https://github.com/codecorsair/archeage-proton-fix/issues)

Original code and bundled shim/test binaries are [MIT licensed](LICENSE).
