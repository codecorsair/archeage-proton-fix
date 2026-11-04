"""Preservation and refusal tests against the installed, unmodified Wine DLL."""
import os
import struct
import unittest
from pathlib import Path

import pefile

from add_forwarder import API, TARGET, exports, patched_bytes

if not os.environ.get('KERNEL32_DLL'):
    raise RuntimeError('Set KERNEL32_DLL to an unmodified x64 Wine kernel32.dll')
SOURCE = Path(os.environ['KERNEL32_DLL'])


class PatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = SOURCE.read_bytes()
        cls.patched = patched_bytes(cls.original)

    def test_export_semantics_and_section_preservation(self):
        old = pefile.PE(data=self.original)
        new = pefile.PE(data=self.patched)
        expected = exports(old)
        ordinal = old.DIRECTORY_ENTRY_EXPORT.struct.Base + old.DIRECTORY_ENTRY_EXPORT.struct.NumberOfFunctions
        expected[(ordinal, API)] = TARGET
        self.assertEqual(exports(new), expected)
        for section in old.sections:
            start = section.PointerToRawData
            end = start + section.SizeOfRawData
            self.assertEqual(self.original[start:end], self.patched[start:end])
        self.assertEqual(old.FILE_HEADER.PointerToSymbolTable, new.FILE_HEADER.PointerToSymbolTable)
        self.assertEqual(new.OPTIONAL_HEADER.CheckSum, new.generate_checksum())
        self.assertEqual(SOURCE.read_bytes(), self.original)

    def test_native_or_signed_dll_refused(self):
        native = bytearray(self.original)
        native[64:80] = bytes(16)
        with self.assertRaisesRegex(ValueError, 'Wine builtin'):
            patched_bytes(bytes(native))
        signed = bytearray(self.original)
        pe = pefile.PE(data=self.original)
        certificate = pe.OPTIONAL_HEADER.DATA_DIRECTORY[4]
        struct.pack_into('<I', signed, certificate.get_field_absolute_offset('Size'), 8)
        with self.assertRaisesRegex(ValueError, 'Signed DLL'):
            patched_bytes(bytes(signed))

    def test_double_patch_refused_even_under_python_optimization(self):
        with self.assertRaisesRegex(ValueError, 'Already exported'):
            patched_bytes(self.patched)


if __name__ == '__main__':
    unittest.main()
