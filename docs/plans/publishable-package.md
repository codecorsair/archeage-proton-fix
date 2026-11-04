# Publishable package workflow record

## Status
- Status: complete
- Current phase: published and verified public GitHub repository.
- Next safe action: use the beginner README to share the guided installation; future changes require normal review.

## Request and scope
- Request: prepare a local Git repository containing code, DLL, and replication instructions for user-managed GitHub publication.
- In scope: original shim and patcher, prebuilt x64 shim/probe, checksums, portable build/tests, guided installer, install/verification/rollback documentation, MIT, authorized public GitHub publication to codecorsair/archeage-proton-fix.
- Out of scope: redistribution of Wine/game/anti-cheat binaries, changing the active game installation/session.

## Git identity
- Source branch: main; origin https://github.com/codecorsair/archeage-proton-fix.git.
- Base commit: f6bc328.
- Feature branch: feature/package was integrated and removed.
- Worktree: .worktrees/package was clean, reachable from main, and removed.
- Omitted source changes: none; import only six original code/build/test files, not local investigation history or records.

## Acceptance criteria
- [x] Package excludes game data, Wine DLLs, local logs, and investigation history.
- [x] Included shim/probe binaries build from supplied source with matching checksums and match across two fresh builds.
- [x] Build/test instructions accept user-provided paths; installer stages and patches only a private runtime.
- [x] Beginner README and advanced instructions cover guided/manual setup, source route, native verification, rollback, architecture limits, and anti-cheat risk.
- [x] Focused and post-review final checks pass; independent read-only review approves the final pinned package.

## Approved implementation plan and gates
- Plan/specification source: user request and structured answers.
- Exact plan: initialize clean repo, package original artifacts and portable commands, add plain inline guided installer with confirmation/backups/refusals, verify/review, integrate locally, create public GitHub repo and push using gh, present README.
- Authority to proceed: explicit request; chosen repository ~/code/archeage-proton-fix and MIT; user separately authorized gh publication, public visibility, and guided installation for nontechnical users.
- Pending decisions: none.
- UI classification and direction approval: plain inline prompts, no full-screen design/framework; user selected guided installer. Numbered choices, default-no confirmations, linear progress and errors, no animation/chrome, works at 60 columns and 80x24 by natural wrapping.
- Risk decisions and scope: installer only creates private runtime and backups and adds one prefix DLL. Reject running Steam, existing targets, Flatpak and unsupported layouts; no root/system runtime edits. Existing C timezone behavior retained.

## Ownership
- Parent owns all files. Review agent owns no files.
- Background source-cache task owns only OpenSrc cache, not this repository.

## Verification matrix
| Surface | Command and cwd | Tested state/environment | Exit code | Outcome or reuse rationale |
| --- | --- | --- | --- | --- |
| Existing behavior | prior isolated runtime probe and actual game launch | original locally reviewed shim | 0 | user confirmed in-game; packaged C behavior retained |
| C builds | bash build.sh build/repro-a; bash build.sh build/repro-b; cmp outputs | Clang/LLD 23.1.4, zero linker timestamp | 0 | byte-identical shim/probe; copied into bin/ |
| Artifact integrity | sha256sum -c SHA256SUMS | packaged bin/ | 0 | both match |
| Focused suite | KERNEL32_DLL=unmodified-Wine-kernel32 python3 -m unittest -v; repeated with -O | 11 tests, temporary fixtures with actual Wine DLL | 0 | backups, refusals, failure cleanup, dry-run, correct truncated/renamed game process detection, helper bootstrap, PE preservation pass |
| Terminal validation | PTY confirmation tests, 80x24 and 60x24 | plain prompts, real child process, cancelled before mutation | 0 | default-no prompt visible, no ANSI controls, cancellation makes no installation changes |
| Native package probe | background task publish-native-probe | separate copied test prefix, never active game prefix | 0 | terminal result inspected; packaged shim/probe passed |
| Full installer | background task publish-full-installer | full copied CachyOS runtime and test prefix; idle guard mocked only for isolated fixture | 0 | complete installer and resulting runtime API probe passed; active game untouched |
| Dependency source | OpenSrc pypi:pefile@2024.8.26 | shared OpenSrc cache | 0 | exact source cached and canonical path verified |

## Review
- Base and product HEAD: f6bc328 to 73589df8f6e345c0285d60e9c8ba958d48406703.
- Clean status and tree hash: clean; e9eb428003fe55cf7b0ae99c26817279e132e11c.
- Commit list: 5876b53 initial package; 73589df focused review fixes.
- Exact diff command: git diff --binary --full-index --find-renames f6bc328...73589df8f6e345c0285d60e9c8ba958d48406703 --
- SHA-256: 0cffe36b1f432ce66f0ea2fa8bf5b128aedfb41564180d75c58f59a6f74e368e.
- Mutator identities: parent only
- Reviewer identity and digest confirmation: publish-review, reviewer profile, confirmed final fingerprint and unchanged Git state.
- Standards verdict: approved after targeted follow-up.
- Specification verdict: approved after targeted follow-up.
- Findings and targeted follow-up: corrected truncated game process name and added command-line detection for Unreal's GameThread rename; replaced executable-realpath venv check with sys.prefix. New regression tests failed before fixes and pass afterward.
- Before/after reviewer Git evidence: final review clean, unchanged HEAD/tree. Post-review final suite repeated normal/-O, source build matched bin/, artifact/private-material/whitespace checks passed.

## Integration and rollback
- Synchronization and re-verification: new repository; final source checks passed before authorized publication.
- Fast-forward result: main fast-forwarded to dbe29d2 after reviewed product 73589df and evidence update.
- Product and evidence commits: 5876b53 package, 73589df fixes, dbe29d2 review/verification evidence; completion update is record-only.
- Reachability and cleanup: all package commits reachable from main; clean feature worktree and branch removed. Original local workaround and active game preserved.
- Publication: gh created and pushed public codecorsair/archeage-proton-fix. GitHub reports MIT and default branch main; remote main initially matched dbe29d24f65333405fd4f70f229d061993b60471.
- Remote artifacts: GitHub bin/tzcompat.dll blob f26cfe347bb08d2d7f8cae56305a6c13745b6239, 3072 bytes, matches local. README blob 7bdd15958c11e2e7ccf0fa6ea83522ab9fd43bf2 also matches local. Both SHA256SUMS entries pass after integration.
- Presentation: complete README opened successfully in native artifact viewer.
- Rollback strategy: original local workaround and running game untouched; public instructions select original Proton and remove only newly added shim if desired.

## Checkpoints and blockers
- Latest saved checkpoint and last committed checkpoint: published dbe29d2 with final reviewed code; this record-only completion checkpoint follows.
- Blockers: none.
- Exact next safe action: push this evidence-only completion record, confirm remote main equals local main, and report the public URL.
