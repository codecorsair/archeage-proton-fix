"""Focused safety and capability tests for setup.sh.

These tests use temporary checkouts and command stubs. They never contact the
network, invoke a package manager, touch Steam, or install Python packages.
"""
import hashlib
import os
import shutil
import stat
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SETUP = ROOT / "setup.sh"


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.env = os.environ.copy()
        self.env["HOME"] = str(self.root / "home")
        (self.root / "home").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def run_setup(self, *args, cwd=None, env=None, input_text=""):
        merged = self.env.copy()
        if env:
            merged.update(env)
        return subprocess.run(
            ["/bin/sh", str(SETUP), *args],
            cwd=cwd or ROOT,
            env=merged,
            input=input_text,
            text=True,
            capture_output=True,
            timeout=30,
        )

    def test_help_and_check_have_separate_groups(self):
        help_result = self.run_setup("--help")
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("--check", help_result.stdout)
        check = self.run_setup("--check")
        self.assertIn("Installation requirements", check.stdout)
        self.assertIn("Source build requirements", check.stdout)
        self.assertIn("Installation result:", check.stdout)
        self.assertIn("Source build result:", check.stdout)

    def test_standalone_build_check_runs_without_build_sh(self):
        runner = self.root / "runner"
        runner.mkdir()
        shutil.copy2(SETUP, runner / "setup.sh")
        result = subprocess.run(
            ["/bin/sh", str(runner / "setup.sh"), "--check", "--build"],
            cwd=runner,
            env=self.env,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Windows compile + import-library + link smoke test", result.stdout)

    def test_check_selection_does_not_run_other_group(self):
        install = self.run_setup("--check", "--install")
        self.assertIn("Installation requirements", install.stdout)
        reversed_order = self.run_setup("--install", "--check")
        self.assertEqual(reversed_order.returncode, install.returncode)
        self.assertIn("Installation requirements", reversed_order.stdout)
        self.assertNotIn("Source build requirements", install.stdout)
        build = self.run_setup("--check", "--build")
        self.assertIn("Source build requirements", build.stdout)
        self.assertNotIn("Installation requirements", build.stdout)

    def test_check_does_not_download(self):
        stub = self.root / "stub"
        stub.mkdir()
        log = self.root / "curl.log"
        self._write_executable(
            stub / "curl",
            "#!/bin/sh\nprintf '%s\\n' \"$*\" >>\"$CURL_LOG\"\nprintf '%s\\n' --proto\n",
        )
        result = self.run_setup("--check", env={"PATH": f"{stub}:{os.environ['PATH']}", "CURL_LOG": str(log)})
        self.assertNotIn("https://codeload.github.com", log.read_text() if log.exists() else "")
        self.assertNotIn("--output", log.read_text() if log.exists() else "")
        self.assertIn("Installation requirements", result.stdout)

    def test_check_rejects_cp_without_reflink_capability(self):
        stub = self.root / "stub"
        stub.mkdir()
        self._write_executable(
            stub / "cp",
            "#!/bin/sh\ncase \"$1\" in --version) echo 'cp (GNU coreutils)';; *) exit 1;; esac\n",
        )
        result = self.run_setup(
            "--check", "--install", env={"PATH": f"{stub}:{os.environ['PATH']}"}
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("GNU cp with working --reflink=auto capability", result.stdout)
        self.assertRegex(result.stderr, r"sudo (apt-get|dnf|pacman)|manually")

    def test_declined_distro_command_is_shown_and_not_run(self):
        checkout = self._make_local_checkout()
        self._set_distro(checkout / 'setup.sh', 'ID=debian\n')
        stub = self.root / "stub"
        stub.mkdir()
        apt_log = self.root / "apt.log"
        self._write_executable(stub / "cp", "#!/bin/sh\ncase \"$1\" in --version) echo fake;; *) exit 1;; esac\n")
        self._write_executable(stub / "apt-get", "#!/bin/sh\nprintf called >>\"$APT_LOG\"\nexit 99\n")
        result = subprocess.run(
            ["/bin/sh", str(checkout / "setup.sh")],
            cwd=checkout,
            env={**self.env, "PATH": f"{stub}:{os.environ['PATH']}", "APT_LOG": str(apt_log)},
            input="n\n",
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("sudo apt-get install", combined)
        self.assertIn("[y/N]", combined)
        self.assertFalse(apt_log.exists())

    def test_approved_package_command_uses_stub_sudo_and_install_tools_only(self):
        checkout = self._make_local_checkout()
        self._set_distro(checkout / 'setup.sh', 'ID=debian\n')
        stub = self.root / 'stub'
        stub.mkdir()
        log = self.root / 'sudo.log'
        self._write_executable(stub / 'cp', '#!/bin/sh\nexit 1\n')
        self._write_executable(stub / 'apt-get', '#!/bin/sh\nexit 99\n')
        self._write_executable(stub / 'sudo', '#!/bin/sh\nprintf "%s\\n" "$*" >> "$SUDO_LOG"\n')
        result = subprocess.run(['/bin/sh', str(checkout / 'setup.sh')], env={**self.env, 'PATH': f'{stub}:{os.environ["PATH"]}', 'SUDO_LOG': str(log)}, input='y\n', text=True, capture_output=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)  # Stub installation cannot repair the missing cp.
        command = log.read_text().strip()
        self.assertEqual(command, 'apt-get install python3 python3-venv python3-pip coreutils curl tar gzip')
        self.assertNotIn('clang', command)
        self.assertIn('[y/N]', result.stderr)

    def test_manual_install_hints_do_not_require_compilers(self):
        stub = self.root / 'stub'
        stub.mkdir()
        for manager in ('zypper', 'apk'):
            self._write_executable(stub / manager, '#!/bin/sh\nexit 99\n')
        for distro in ('opensuse-tumbleweed', 'alpine'):
            with self.subTest(distro=distro):
                harness = self.root / 'manual.sh'
                harness.write_text(SETUP.read_text().rsplit('main "$@"', 1)[0] + 'show_package_command install\n')
                self._set_distro(harness, f'ID={distro}\n')
                result = subprocess.run(['/bin/sh', str(harness)], env={**self.env, 'PATH': f'{stub}:{os.environ["PATH"]}'}, text=True, capture_output=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('manually', result.stderr)
                self.assertNotIn('clang', result.stderr)
                self.assertNotIn('sudo', result.stderr)

    def test_local_checkout_is_verified_before_handoff(self):
        checkout = self._make_local_checkout()
        marker = self.root / "handoff"
        install = checkout / "install.py"
        install.write_text("from pathlib import Path\nPath(__import__('os').environ['MARKER']).write_text('ok')\n")
        (checkout / "bin/tzcompat.dll").write_bytes(b"tampered")
        result = subprocess.run(
            ["/bin/sh", str(checkout / "setup.sh")],
            cwd=checkout,
            env={**self.env, "MARKER": str(marker)},
            text=True,
            capture_output=True,
            timeout=30,
        )
        # A checked-in artifact is intentionally changed after the manifest was
        # written, so the checksum gate must reject it and not hand off.
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(marker.exists())
        self.assertIn("Checksum verification failed", result.stderr)

    def test_local_checkout_handoff_after_checksum(self):
        checkout = self._make_local_checkout()
        marker = self.root / "handoff"
        self._write_manifest(checkout)
        result = subprocess.run(
            ["/bin/sh", str(checkout / "setup.sh")],
            cwd=checkout,
            env={**self.env, "MARKER": str(marker)},
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(marker.read_text(), "ok")

    def test_native_distro_wins_over_foreign_package_managers(self):
        stub = self.root / 'stub'
        stub.mkdir()
        for manager in ('apt-get', 'dnf', 'pacman', 'zypper', 'apk'):
            self._write_executable(stub / manager, '#!/bin/sh\nexit 99\n')
        function_source = SETUP.read_text().rsplit('main "$@"', 1)[0]
        cases = [
            ('ID=ubuntu\nID_LIKE=debian\n', 'apt-get'),
            ('ID=fedora\n', 'dnf'),
            ('ID=cachyos\nID_LIKE=arch\n', 'pacman'),
            ('ID=derivative\nID_LIKE=arch\n', 'pacman'),
            ('ID=opensuse-tumbleweed\n', 'zypper'),
            ('ID=alpine\n', 'apk'),
        ]
        for metadata, expected in cases:
            with self.subTest(distro=metadata):
                harness = self.root / 'manager.sh'
                harness.write_text(function_source + 'package_manager\n')
                self._set_distro(harness, metadata)
                result = subprocess.run(['/bin/sh', str(harness)], env={**self.env, 'PATH': f'{stub}:{os.environ["PATH"]}'}, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected)
        harness.write_text(function_source + 'package_manager\n')
        self._set_distro(harness, 'ID=unknown\n')
        result = subprocess.run(['/bin/sh', str(harness)], env={**self.env, 'PATH': f'{stub}:{os.environ["PATH"]}'}, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')

    def test_relative_tmpdir_from_another_cwd_does_not_write_checkout(self):
        checkout = self.root / 'source'
        checkout.mkdir()
        for name in ('setup.sh', 'build.sh', 'tzcompat.c', 'timezone.h', 'probe.c'):
            shutil.copy2(ROOT / name, checkout / name)
        caller = self.root / 'caller'
        caller.mkdir()
        scratch = caller / 'relative-tmp'
        scratch.mkdir()
        sentinel = scratch / 'keep'
        sentinel.write_text('caller-owned')
        result = subprocess.run(['/bin/sh', str(checkout / 'setup.sh'), '--check', '--build'], cwd=caller,
                                env={**self.env, 'TMPDIR': 'relative-tmp'}, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((checkout / 'relative-tmp').exists())
        self.assertEqual(sentinel.read_text(), 'caller-owned')
        self.assertEqual(list(scratch.iterdir()), [sentinel])

    def test_probe_cleanup_preserves_other_paths_with_newline_tmpdir(self):
        keep = self.root / 'keep'
        keep.mkdir()
        sentinel = keep / 'settings'
        sentinel.write_text('keep this')
        temporary = self.root / 'keep\nprobe'
        temporary.mkdir()
        result = self.run_setup('--check', '--build', env={'TMPDIR': str(temporary)})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sentinel.read_text(), 'keep this')
        self.assertEqual(list(temporary.iterdir()), [])

    def test_download_collision_refuses_before_curl(self):
        runner = self.root / "runner"
        runner.mkdir()
        shutil.copy2(SETUP, runner / "setup.sh")
        destination = self.root / "target"
        destination.mkdir()
        stub = self.root / "stub"
        stub.mkdir()
        log = self.root / "curl.log"
        self._write_executable(
            stub / "curl",
            "#!/bin/sh\ncase \"$*\" in *'--help all'*) echo --proto;; *) printf called >>\"$CURL_LOG\"; exit 99;; esac\n",
        )
        result = subprocess.run(
            ["/bin/sh", str(runner / "setup.sh"), "--directory", str(destination)],
            cwd=runner,
            env={**self.env, "PATH": f"{stub}:{os.environ['PATH']}", "CURL_LOG": str(log)},
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destination already exists", result.stderr)
        self.assertNotIn('Installation requirements', result.stdout)
        self.assertNotIn('[y/N]', result.stderr)
        self.assertFalse(log.exists())

    def test_download_handoff_uses_new_destination(self):
        archive = self._make_archive(valid_checksum=True)
        runner = self.root / "runner"
        runner.mkdir()
        shutil.copy2(SETUP, runner / "setup.sh")
        stub = self.root / "stub"
        stub.mkdir()
        self._write_executable(stub / "curl", self._curl_stub())
        destination = self.root / "target"
        marker = self.root / "handoff"
        result = subprocess.run(
            ["/bin/sh", str(runner / "setup.sh"), "--directory", str(destination)],
            cwd=runner,
            env={
                **self.env,
                "PATH": f"{stub}:{os.environ['PATH']}",
                "ARCHIVE": str(archive),
                "MARKER": str(marker),
            },
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(marker.read_text(), "ok")
        self.assertTrue((destination / "SHA256SUMS").is_file())
        self.assertEqual(list(self.root.glob(".archeage-setup.*")), [])

    def test_download_publish_detects_noop_move(self):
        archive = self._make_archive(valid_checksum=True)
        runner = self.root / "runner"
        runner.mkdir()
        shutil.copy2(SETUP, runner / "setup.sh")
        stub = self.root / "stub"
        stub.mkdir()
        self._write_executable(stub / "curl", self._curl_stub())
        self._write_executable(stub / "mv", "#!/bin/sh\nexit 0\n")
        destination = self.root / "target"
        result = subprocess.run(
            ["/bin/sh", str(runner / "setup.sh"), "--directory", str(destination)],
            cwd=runner,
            env={**self.env, "PATH": f"{stub}:{os.environ['PATH']}", "ARCHIVE": str(archive)},
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(destination.exists())
        self.assertIn("publish did not complete", result.stderr)

    def test_download_rejects_archive_symlinks(self):
        source = self.root / "unsafe/archeage-proton-fix-main"
        source.mkdir(parents=True)
        (source / "link").symlink_to("/etc/passwd")
        archive = self.root / "unsafe.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(source, arcname="archeage-proton-fix-main")
        runner = self.root / "runner"
        runner.mkdir()
        shutil.copy2(SETUP, runner / "setup.sh")
        stub = self.root / "stub"
        stub.mkdir()
        self._write_executable(stub / "curl", self._curl_stub())
        destination = self.root / "target"
        result = subprocess.run(
            ["/bin/sh", str(runner / "setup.sh"), "--directory", str(destination)],
            cwd=runner,
            env={**self.env, "PATH": f"{stub}:{os.environ['PATH']}", "ARCHIVE": str(archive)},
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(destination.exists())
        self.assertEqual(list(self.root.glob(".archeage-setup.*")), [])
        self.assertIn("unsafe paths or unsupported links", result.stderr)

    def test_download_checksum_failure_cleans_staging(self):
        archive = self._make_archive(valid_checksum=False)
        runner = self.root / "runner"
        runner.mkdir()
        shutil.copy2(SETUP, runner / "setup.sh")
        stub = self.root / "stub"
        stub.mkdir()
        self._write_executable(stub / "curl", self._curl_stub())
        destination = self.root / "target"
        result = subprocess.run(
            ["/bin/sh", str(runner / "setup.sh"), "--directory", str(destination)],
            cwd=runner,
            env={
                **self.env,
                "PATH": f"{stub}:{os.environ['PATH']}",
                "ARCHIVE": str(archive),
            },
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(destination.exists())
        self.assertEqual(list(self.root.glob(".archeage-setup.*")), [])
        self.assertIn("Checksum verification failed", result.stderr)

    def _make_local_checkout(self):
        checkout = self.root / "checkout"
        checkout.mkdir()
        shutil.copy2(SETUP, checkout / "setup.sh")
        (checkout / "bin").mkdir()
        (checkout / "bin/tzcompat.dll").write_bytes(b"dll")
        (checkout / "bin/probe.exe").write_bytes(b"probe")
        (checkout / "install.py").write_text(
            "from pathlib import Path\nPath(__import__('os').environ['MARKER']).write_text('ok')\n"
        )
        self._write_manifest(checkout)
        return checkout

    def _write_manifest(self, checkout):
        entries = []
        for name in ("bin/tzcompat.dll", "bin/probe.exe"):
            entries.append(f"{hashlib.sha256((checkout / name).read_bytes()).hexdigest()}  {name}")
        (checkout / "SHA256SUMS").write_text("\n".join(entries) + "\n")

    def _make_archive(self, valid_checksum):
        source = self.root / "archive-source/archeage-proton-fix-main"
        (source / "bin").mkdir(parents=True)
        (source / "bin/tzcompat.dll").write_bytes(b"dll")
        (source / "bin/probe.exe").write_bytes(b"probe")
        (source / "install.py").write_text(
            "from pathlib import Path\nPath(__import__('os').environ['MARKER']).write_text('ok')\n"
        )
        self._write_manifest(source)
        if not valid_checksum:
            (source / "SHA256SUMS").write_text("0" * 64 + "  bin/tzcompat.dll\n" + (source / "SHA256SUMS").read_text().split("\n", 1)[1])
        archive = self.root / "repo.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(source, arcname="archeage-proton-fix-main")
        return archive

    def _curl_stub(self):
        return """#!/bin/sh
case "$*" in
  *"--help all"*) printf '%s\\n' --proto; exit 0;;
esac
out=
while [ "$#" -gt 0 ]; do
  if [ "$1" = "--output" ]; then out=$2; shift; fi
  shift
done
cp "$ARCHIVE" "$out"
"""

    def _set_distro(self, script, metadata):
        release = self.root / 'fixture-os-release'
        release.write_text(metadata)
        script.write_text(script.read_text().replace('/etc/os-release', str(release)))

    def _write_executable(self, path, text):
        path.write_text(text)
        path.chmod(path.stat().st_mode | stat.S_IXUSR)


if __name__ == "__main__":
    unittest.main()
