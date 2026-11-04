#!/usr/bin/env bash
# Build only. Does not modify Proton or the game's prefix.
set -euo pipefail
cd -- "$(dirname -- "$0")"
out=${1:?Usage: bash build.sh NEW_OUTPUT_DIRECTORY}
test ! -e "$out"
mkdir -p "$out"
out=$(realpath "$out")
printf 'LIBRARY kernel32.dll\nEXPORTS\nGetModuleHandleA\nGetProcAddress\nGetSystemTime\nExitProcess\nGetDynamicTimeZoneInformation\nGetTimeZoneInformationForYear\nSystemTimeToTzSpecificLocalTime\nSetLastError\n' > "$out/kernel32.def"
llvm-dlltool -m i386:x86-64 -d "$out/kernel32.def" -l "$out/kernel32.lib"
for name in tzcompat probe; do
    clang --target=x86_64-pc-windows-msvc -c -O2 -ffreestanding -funwind-tables -fno-stack-protector "$name.c" -o "$out/$name.obj"
done
lld-link /timestamp:0 /dll /noentry /nodefaultlib /out:"$out/tzcompat.dll" "$out/tzcompat.obj" "$out/kernel32.lib"
lld-link /timestamp:0 /entry:mainCRTStartup /subsystem:console /nodefaultlib /out:"$out/probe.exe" "$out/probe.obj" "$out/kernel32.lib"
