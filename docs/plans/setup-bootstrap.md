# Portable setup workflow record

## Status
- Status: active
- Current phase: corrected product independently approved and final checks passed; ready to publish.
- Next safe action: integrate locally, push the authorized update, and verify the public script/archive.

## Request and scope
- Request: document build tools, check build and install dependencies across major Linux families, and provide a standalone shell script that downloads the repo/assets and starts guided installation.
- In scope: one POSIX setup.sh; check-only separate build/install results; real Windows cross-build smoke test; explicit-confirmation package-manager assistance; HTTPS archive including checked-in DLL/probe; existing guided installer handoff; docs/tests; updates to existing public repository.
- Out of scope: silent package installation, sudo for the whole installer, changing the active game, automatic game/Steam shutdown, new Python/UI dependencies, distro-wide runtime guarantees.

## Git identity
- Source branch: main, clean, fetched origin.
- Base commit: bda9637a2133d64afa18ec9cdc97606e3ae86d9f.
- Feature branch: feature/setup.
- Worktree: .worktrees/setup, rebased onto origin/main before product changes.
- Omitted source changes: none.

## Acceptance criteria
- [x] setup.sh --check reports build and installation groups separately without downloads/system installation.
- [x] --check --build and --check --install select one group; missing requirements give nonzero status and actionable package hints.
- [x] Build checks exercise clang Windows target, llvm-dlltool, and lld-link, including standalone use without build.sh.
- [x] Default setup offers missing-system-package installation only after showing the exact supported native-distro command and explicit default-no consent; zypper/apk use manual hints.
- [x] Standalone download/staging/collision/checksum/cleanup behavior passes isolated tests; real GitHub download verification is separately pending inspection.
- [x] Local-repo setup reuses its checkout; verifies artifact checksums before launching existing non-root guided installer.
- [x] Beginner README and advanced tools table explain prebuilt-vs-build requirements and tested-vs-supported scope.
- [x] Focused failure/safety tests, final suite/build checks, and fresh independent review passed.
- [ ] Authorized publication and public artifact verification complete.

## Approved implementation plan and gates
- Plan/specification source: user conversation and structured answers.
- Exact plan: script/test worker, read-only distro-package research, parallel parent docs; inspect outputs, review/remediate, final checks, integrate and push.
- Authority to proceed: user explicitly chose both requirement groups and confirmation-based system dependency installation. Existing public repository publication authorization remains scoped to this workaround.
- Pending decisions: none.
- UI classification and direction approval: small plain CLI, no full-screen or animation; default-no prompts and clear progress. Existing guided installer remains final Steam/game installation authority.
- Risk decisions and scope: no curl-to-shell documentation; download script to a file before running. HTTPS trust is not a cryptographic signature. Never execute package commands during harness tests; use controlled stubs. No root execution of the actual installer.

## Ownership
- Parent: README.md, docs/advanced.md, this record, optional minimal build.sh integration; Git commits/integration/publication only parent.
- setup-worker, worker profile: setup.sh and test_setup.py only; base bda9637, initial tracked changes only this parent-owned record; no commits/nested delegation. Original bounded assignment returned two files and 11 passing tests. Resumed under the same exclusive ownership to apply researched package caveats and then fix standalone-smoke, no-clobber publication, and interruption-cleanup contract issues found while integrating. Stable session identity not exposed; tool resume acknowledgements confirm preceding runs terminated. Final follow-up delivered and inspected: standalone smoke, no-clobber move, scratch cleanup and 13 tests reported. Worker is terminal; parent takes exclusive setup.sh/test_setup.py ownership for integration fixes and final review.
- setup-package-research, researcher profile: read-only evidence delivered; owns no files. Official metadata confirms Debian/Fedora/Arch mappings; RHEL repositories, openSUSE old/default Python and Alpine versioned LLVM require explicit caveats. No distro installations or runtime tests performed.

## Verification matrix
| Surface | Command and cwd | Tested state/environment | Exit code | Outcome or reuse rationale |
| --- | --- | --- | --- | --- |
| Preflight | Git fetch/status/rebase | clean worktree at bda9637 | 0 | no omitted changes |
| Suite | KERNEL32_DLL=original-Wine-DLL python3 -m unittest -v; python3 -O -m unittest -q | 29 tests, repeated after fresh review | 0 | all pass; package execution uses fake sudo only |
| Final rebuild | bash build.sh build/final-setup; cmp DLL/probe with bin/ | reviewed source, Clang/LLD 23.1.4 | 0 | byte-identical to bundled artifacts; checksums pass |
| Final documentation/content checks | local-file link scan, private-marker scan, git diff --check | tracked files only | 0 | no broken local links or private-path/token markers |
| Relative TMPDIR regression | isolated copied source/checker run from another cwd with relative TMPDIR | all generated files contained in TemporaryDirectory fixtures | 1 then 0 | failed before fix, passed after canonicalizing probe parent paths; source checkout not written and caller sentinel preserved |
| Shell syntax/capabilities | sh -n setup.sh; sh setup.sh --check --install; sh setup.sh --check --build | CachyOS /bin/sh is Bash; installed LLVM 23.1.4 | 0 | groups pass; real source/standalone Windows smoke exercised |
| Artifact integrity | sha256sum -c SHA256SUMS | original packaged binaries unchanged | 0 | both pass |
| Safety regressions | native distro selection, newline TMPDIR cleanup, early collision, approved/declined commands | temporary fixtures only | 0 | foreign managers not chosen; unrelated files preserved; no actual package manager or sudo runs |
| Real download | setup-real-download and corrected setup-real-download-final background tasks | genuine GitHub archive; Python wrapper permits only install.py --help at handoff | 0 | both terminal results inspected: real artifacts verified and E2E_HANDOFF_HELP_ONLY confirmed; no installation or game changes |

## Review
- Base and product HEAD: bda9637a2133d64afa18ec9cdc97606e3ae86d9f to 52e3b862bdc29daa4a67271985b610c4baec9230.
- Clean status and tree hash: clean; 6e158a52931b205ad59fcc78e6578862050e920d.
- Commit list: 6ae77b3 bootstrap/checks/docs; 52e3b86 relative-TMPDIR correction.
- Exact diff command: git diff --binary --full-index --find-renames bda9637...52e3b862bdc29daa4a67271985b610c4baec9230 --
- SHA-256: b20b0e53d25002877af7e2b84a084be13d431693e0ec916e689c40d5691bbc39.
- Mutator identities: parent and setup-worker. Parent integration tightened native distro selection, single-active-scratch cleanup, fail-closed UID lookup, early destination refusal, and group-specific manual hints after worker termination. setup-review also generated untracked probe artifacts and is excluded from all subsequent review of this diff.
- Reviewer identity and digest confirmation: setup-review-fresh, reviewer profile, distinct newrun, confirmed final fingerprint and unchanged Git state; source-only review, no script/probe execution.
- Standards verdict: approved.
- Specification verdict: approved.
- Findings and targeted follow-up: reviewer executed an ad hoc relative-TMPDIR probe and created untracked relative-tmp build output. Parent inspected all files, proved DLL/probe match generated binaries, and preserved them, ultimately under the main Git directory's workflow-evidence/setup-relative-tmp-6ae77b3, outside public tracked files. Relative scratch paths changed meaning when the build script changed directory. Parent reproduced this only in an isolated copied-source fixture, then fixed all probe creation through an absolute-parent helper; regression is now green.
- Before/after reviewer Git evidence: initial clean6ae77b3; afterward only untracked generated directory. Parent preservation restored clean tracked/untracked Git state; no original work discarded. Fresh review began and ended clean at 52e3b86 with matching tree.

## Integration and rollback
- Synchronization and re-verification: fetched and rebased origin/main after fresh review; product identity unchanged; final suite/checks/rebuild passed.
- Fast-forward result: pending
- Product and evidence commits: pending
- Reachability and cleanup: remove only clean integrated workflow worktree; preserve active game and original workaround.
- Rollback strategy: code update is locally reversible; bootstrap never changes shared Proton and delegates prefix changes to the existing backed-up installer.

## Checkpoints and blockers
- Latest saved checkpoint and last committed checkpoint: initial plan, base bda9637.
- Blockers: none.
- Exact next safe action: integrate reviewed product and evidence-only record, push main, verify raw public script/hash and real archive handoff with installation restricted to --help.
