# Standalone bootstrap with explicit package consent

Use a POSIX-shell bootstrap that can check installation and source-build requirements separately, download this repository with its prebuilt assets, and hand off to the existing guided installer. Default setup uses the prebuilt DLL so nontechnical users do not need compiler packages; check-only mode never installs or downloads, and any system-package command must be displayed and explicitly approved before `sudo`.

Keep archive/checksum validation and download cleanup in the bootstrap, while Steam detection, private Proton copies, prefix backups, and final game-installation consent remain owned by the Python installer. Document saving the script before running it rather than piping a remote response into a shell; HTTPS and repository trust are still required, and checksums do not provide an independent signature.
