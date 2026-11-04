"""Add one missing kernel32 export to a private Wine DLL, preserving old exports."""
import argparse
import hashlib
import struct
from pathlib import Path

import pefile

API = b"SystemTimeToTzSpecificLocalTimeEx"
TARGET = b"tzcompat." + API


def align(value, alignment):
    return (value + alignment - 1) // alignment * alignment


def exports(pe):
    directory = pe.DIRECTORY_ENTRY_EXPORT
    return {
        (symbol.ordinal, symbol.name): (
            symbol.forwarder if symbol.forwarder else symbol.address
        )
        for symbol in directory.symbols
    }


def patched_bytes(original):
    if not original[64:96].startswith(b"Wine builtin DLL\0"):
        raise ValueError("Expected a Wine builtin DLL, not a native Windows DLL")
    pe = pefile.PE(data=original)
    if pe.FILE_HEADER.Machine != 0x8664:
        raise ValueError("Expected x86-64 DLL")
    if pe.OPTIONAL_HEADER.DATA_DIRECTORY[4].Size != 0:
        raise ValueError("Signed DLL: refuse")
    directory = pe.DIRECTORY_ENTRY_EXPORT
    old = directory.struct
    if pe.get_string_at_rva(old.Name).lower() != b"kernel32.dll":
        raise ValueError("Expected Wine kernel32.dll")
    if API in {symbol.name for symbol in directory.symbols}:
        raise ValueError("Already exported")
    section_header = pe.sections[-1].get_file_offset() + 40
    if section_header + 40 > pe.OPTIONAL_HEADER.SizeOfHeaders:
        raise ValueError("Section header exceeds header allocation")
    if any(original[section_header:section_header + 40]):
        raise ValueError("No free section header")
    # Append after the COFF debug-symbol overlay, leaving its file offsets intact.

    rva = align(max(s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData)
                    for s in pe.sections), pe.OPTIONAL_HEADER.SectionAlignment)
    raw_offset = align(len(original), pe.OPTIONAL_HEADER.FileAlignment)
    count = old.NumberOfFunctions
    eat_offset = 40
    names_offset = eat_offset + 4 * (count + 1)
    ordinals_offset = names_offset + 4 * (old.NumberOfNames + 1)
    payload = bytearray(ordinals_offset + 2 * (old.NumberOfNames + 1))

    def string_rva(value):
        position = rva + len(payload)
        payload.extend(value + b"\0")
        return position

    functions = list(struct.unpack(
        f"<{count}I", pe.get_data(old.AddressOfFunctions, 4 * count)))
    original_export = pe.OPTIONAL_HEADER.DATA_DIRECTORY[0]
    for index, address in enumerate(functions):
        if original_export.VirtualAddress <= address < original_export.VirtualAddress + original_export.Size:
            functions[index] = string_rva(pe.get_string_at_rva(address))
    functions.append(string_rva(TARGET))
    struct.pack_into(f"<{count + 1}I", payload, eat_offset, *functions)

    names = [(symbol.name, symbol.ordinal - old.Base)
             for symbol in directory.symbols if symbol.name is not None]
    names.append((API, count))
    names.sort()
    if len(names) != old.NumberOfNames + 1:
        raise ValueError("Unexpected named-export count")
    for index, (name, ordinal) in enumerate(names):
        struct.pack_into("<I", payload, names_offset + 4 * index, string_rva(name))
        struct.pack_into("<H", payload, ordinals_offset + 2 * index, ordinal)
    struct.pack_into("<IIHHIIIIIII", payload, 0,
                     old.Characteristics, old.TimeDateStamp, old.MajorVersion,
                     old.MinorVersion, string_rva(pe.get_string_at_rva(old.Name)),
                     old.Base, count + 1, len(names), rva + eat_offset,
                     rva + names_offset, rva + ordinals_offset)

    size = len(payload)
    raw_size = align(size, pe.OPTIONAL_HEADER.FileAlignment)
    output = bytearray(original)
    output.extend(bytes(raw_offset - len(output)))
    output.extend(payload)
    output.extend(bytes(raw_size - size))
    struct.pack_into("<8sIIIIIIHHI", output, section_header,
                     b".tzfix\0\0", size, rva, raw_size, raw_offset,
                     0, 0, 0, 0, 0x40000040)
    struct.pack_into("<H", output, pe.FILE_HEADER.get_field_absolute_offset("NumberOfSections"),
                     pe.FILE_HEADER.NumberOfSections + 1)
    for field, value in [
        ("SizeOfImage", align(rva + size, pe.OPTIONAL_HEADER.SectionAlignment)),
        ("SizeOfInitializedData", pe.OPTIONAL_HEADER.SizeOfInitializedData + raw_size),
        ("CheckSum", 0),
    ]:
        struct.pack_into("<I", output, pe.OPTIONAL_HEADER.get_field_absolute_offset(field), value)
    struct.pack_into("<II", output, original_export.get_file_offset(), rva, size)
    result = pefile.PE(data=bytes(output))
    expected = exports(pe)
    expected[(old.Base + count, API)] = TARGET
    if exports(result) != expected:
        raise ValueError("Existing export semantics changed")
    struct.pack_into("<I", output, pe.OPTIONAL_HEADER.get_field_absolute_offset("CheckSum"),
                     result.generate_checksum())
    return bytes(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Unmodified x64 Wine kernel32.dll")
    parser.add_argument("destination", type=Path, help="New output file; never the original")
    args = parser.parse_args()
    source, destination = args.source, args.destination
    if destination.exists():
        raise ValueError("Destination must be new")
    original = source.read_bytes()
    result = patched_bytes(original)
    with destination.open("xb") as stream:
        stream.write(result)
    print(f"Original SHA256: {hashlib.sha256(original).hexdigest()}")
    print(f"Patched SHA256:  {hashlib.sha256(result).hexdigest()}")
    print(f"Added {API.decode()} -> {TARGET.decode()}; all old exports preserved")
