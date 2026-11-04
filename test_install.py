"""Exercise installation against small realistic prefixes, never the real Steam tree."""
import contextlib
import fcntl
import io
import os
import pty
import struct
import subprocess
import sys
import tempfile
import termios
import unittest
from pathlib import Path
from unittest.mock import patch

import install
from add_forwarder import patched_bytes


class InstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.environ.get('KERNEL32_DLL'):
            raise RuntimeError('Set KERNEL32_DLL to an unmodified x64 Wine kernel32.dll')
        cls.original_dll = Path(os.environ['KERNEL32_DLL']).read_bytes()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.steam = self.root / 'Steam'
        self.library = self.root / 'Steam Library'
        self.proton = self.steam / 'steamapps/common/Proton - Experimental'
        (self.steam / 'steamapps').mkdir(parents=True)
        (self.steam / 'steamapps/libraryfolders.vdf').write_text(
            f'"libraryfolders"\n{{\n"1"\n{{\n"path" "{self.library}"\n}}\n}}\n')
        dll = self.proton / install.DLL_PATH
        dll.parent.mkdir(parents=True)
        dll.write_bytes(self.original_dll)
        dll.chmod(0o555)
        (self.proton / 'proton').write_text('#!/usr/bin/env python3\n')
        (self.proton / 'compatibilitytool.vdf').write_text('original config\n')
        self.app = self.library / 'steamapps/compatdata/3218230'
        self.system32 = self.app / 'pfx/drive_c/windows/system32'
        self.system32.mkdir(parents=True)
        (self.app / 'pfx/user.reg').write_text('WINE REGISTRY Version 2\n[Software\\\\Wine]\n')
        (self.system32 / 'kernel32.dll').symlink_to(dll)
        self.custom = self.steam / 'compatibilitytools.d' / install.TOOL_NAME
        self.backup = self.app.with_name('3218230.before-tz-fix')

    def test_install_preserves_originals_and_creates_backup(self):
        with patch('install.require_idle'), contextlib.redirect_stderr(io.StringIO()):
            custom, backup = install.install(self.steam, self.library, self.proton)
        self.assertEqual(custom, self.custom)
        self.assertEqual(backup, self.backup)
        self.assertEqual((self.proton / install.DLL_PATH).read_bytes(), self.original_dll)
        self.assertEqual((self.custom / install.DLL_PATH).read_bytes(), patched_bytes(self.original_dll))
        self.assertEqual((self.system32 / 'tzcompat.dll').read_bytes(), (install.ROOT / 'bin/tzcompat.dll').read_bytes())
        self.assertEqual((self.backup / 'pfx/user.reg').read_bytes(), (self.app / 'pfx/user.reg').read_bytes())
        self.assertTrue((self.backup / 'pfx/drive_c/windows/system32/kernel32.dll').is_symlink())
        self.assertFalse((self.backup / 'pfx/drive_c/windows/system32/tzcompat.dll').exists())
        self.assertEqual((self.custom / 'compatibilitytool.vdf').read_bytes(), (install.ROOT / 'compatibilitytool.vdf').read_bytes())
        self.assertFalse((self.custom.parent / '.archeage-tz-install.lock').exists())
        with self.assertRaisesRegex(ValueError, 'Already exists'):
            install.validate_paths(self.steam, self.library, self.proton)

    def test_backup_failure_leaves_prefix_and_runtime_unchanged(self):
        actual_run = subprocess.run

        def fail_backup(command, **kwargs):
            if str(self.app) + '/.' in command:
                raise subprocess.CalledProcessError(1, command)
            return actual_run(command, **kwargs)

        with patch('install.require_idle'), patch('install.subprocess.run', side_effect=fail_backup), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(subprocess.CalledProcessError):
                install.install(self.steam, self.library, self.proton)
        self.assertFalse(self.custom.exists())
        self.assertFalse(self.backup.exists())
        self.assertFalse((self.system32 / 'tzcompat.dll').exists())
        self.assertEqual((self.proton / install.DLL_PATH).read_bytes(), self.original_dll)
        self.assertEqual(list(self.custom.parent.iterdir()), [])
        self.assertEqual(list(self.app.parent.iterdir()), [self.app])

    def test_failure_after_shim_write_retains_backup_and_removes_shim(self):
        actual_rename = Path.rename

        def fail_final_rename(path, destination):
            if destination == self.custom:
                raise OSError('simulated final rename failure')
            return actual_rename(path, destination)

        with patch('install.require_idle'), patch.object(Path, 'rename', fail_final_rename), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(OSError, 'simulated final rename'):
                install.install(self.steam, self.library, self.proton)
        self.assertFalse(self.custom.exists())
        self.assertTrue((self.backup / 'pfx/user.reg').is_file())
        self.assertFalse((self.system32 / 'tzcompat.dll').exists())
        self.assertEqual(list(self.custom.parent.iterdir()), [])

    def test_symlinked_private_dll_is_never_followed(self):
        external = self.root / 'external-kernel32.dll'
        external.write_bytes(self.original_dll)
        target = self.proton / install.DLL_PATH
        target.unlink()
        target.symlink_to(external)
        with patch('install.require_idle'), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(ValueError, 'outside the copied runtime'):
                install.install(self.steam, self.library, self.proton)
        self.assertEqual(external.read_bytes(), self.original_dll)
        self.assertFalse(self.custom.exists())
        self.assertFalse(self.backup.exists())

    def test_library_discovery_and_read_only_dry_run(self):
        self.assertEqual(install.libraries(self.steam), [self.steam, self.library])
        before = sorted(str(p) for p in self.root.rglob('*'))
        args = ['install.py', '--dry-run', '--steam-root', str(self.steam),
                '--library', str(self.library), '--proton', str(self.proton)]
        output = io.StringIO()
        with patch.object(sys, 'argv', args), patch('install.require_idle') as idle, \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(install.main(), 0)
            idle.assert_not_called()
        self.assertIn('Dry run: no files changed', output.getvalue())
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob('*')))

    def test_terminal_confirmation_cancels_without_writes(self):
        # Only process detection is replaced: this fixture is not the running user's Steam.
        code = 'import install; install.require_idle = lambda: None; raise SystemExit(install.main())'
        for width in (80, 60):
            with self.subTest(columns=width):
                master, slave = pty.openpty()
                fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 24, width, 0, 0))
                command = [sys.executable, '-c', code, '--steam-root', str(self.steam),
                           '--library', str(self.library), '--proton', str(self.proton)]
                process = subprocess.Popen(command, cwd=install.ROOT, stdin=slave, stdout=slave, stderr=slave)
                os.close(slave)
                try:
                    os.write(master, b'n\n')
                    self.assertEqual(process.wait(timeout=5), 0)
                    chunks = []
                    while True:
                        try:
                            data = os.read(master, 8192)
                        except OSError:
                            break  # Linux PTY reports EIO once the slave closes.
                        if not data:
                            break
                        chunks.append(data)
                    output = b''.join(chunks)
                    self.assertIn(b'[y/N]', output)
                    self.assertIn(b'Cancelled. No files changed.', output)
                    self.assertNotIn(b'\x1b', output)
                    self.assertFalse(self.custom.exists())
                    self.assertFalse(self.backup.exists())
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait()
                    os.close(master)

    def test_running_steam_or_game_refused(self):
        proc = self.root / 'proc'
        (proc / '123').mkdir(parents=True)
        cases = [
            ('steam', b'steam\0'),
            ('ArcheAgeChronic', b'./ArcheAgeChronicles.exe\0'),
            ('GameThread', b'Z:\\games\\ArcheAge Chronicles\\X5\\Binaries\\Win64\\ArcheAgeChronicles.exe\0X5\0'),
        ]
        for name, command in cases:
            with self.subTest(process=name):
                (proc / '123/comm').write_text(name + '\n')
                (proc / '123/cmdline').write_bytes(command)
                with patch('install.Path', return_value=proc):
                    with self.assertRaisesRegex(ValueError, 'Fully exit'):
                        install.require_idle()

    def test_existing_venv_missing_helper_can_bootstrap(self):
        environment = self.root / '.venv'
        (environment / 'bin').mkdir(parents=True)
        (environment / 'bin/python').symlink_to(sys.executable)
        with patch('install.ROOT', self.root), patch('install.importlib.util.find_spec', return_value=None), \
                patch('install.subprocess.run') as run, patch('install.os.execv', side_effect=RuntimeError('reexec requested')) as execute, \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, 'reexec requested'):
                install.ensure_dependency(self.steam, self.library, self.proton)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(execute.call_args.args[0], str(environment / 'bin/python'))
        self.assertIn('--yes', execute.call_args.args[1])


if __name__ == '__main__':
    unittest.main()
