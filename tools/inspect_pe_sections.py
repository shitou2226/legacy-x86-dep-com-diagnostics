#!/usr/bin/env python3
"""Read-only PE section inspector using only the Python standard library."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path


MACHINE_NAMES = {
    0x014C: "x86",
    0x0200: "IA-64",
    0x8664: "x64",
    0x01C4: "ARM Thumb-2",
    0xAA64: "ARM64",
}

IMAGE_SCN_MEM_EXECUTE = 0x20000000
IMAGE_SCN_MEM_READ = 0x40000000
IMAGE_SCN_MEM_WRITE = 0x80000000


class PEFormatError(ValueError):
    """Raised when the input is not a structurally valid PE image."""


def _unpack_from(fmt: str, data: bytes, offset: int) -> tuple[int, ...]:
    size = struct.calcsize(fmt)
    if offset < 0 or offset + size > len(data):
        raise PEFormatError(f"Unexpected end of file at offset 0x{offset:X}")
    return struct.unpack_from(fmt, data, offset)


def inspect_pe(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise PEFormatError("Missing DOS MZ header")

    (pe_offset,) = _unpack_from("<I", data, 0x3C)
    if pe_offset + 24 > len(data) or data[pe_offset : pe_offset + 4] != b"PE\0\0":
        raise PEFormatError("Missing PE signature")

    coff_offset = pe_offset + 4
    machine, section_count, _, _, _, optional_size, characteristics = _unpack_from(
        "<HHIIIHH", data, coff_offset
    )
    optional_offset = coff_offset + 20
    if optional_size < 20:
        raise PEFormatError("Optional header is too small")

    (magic,) = _unpack_from("<H", data, optional_offset)
    format_name = {0x10B: "PE32", 0x20B: "PE32+"}.get(magic)
    if format_name is None:
        raise PEFormatError(f"Unsupported optional-header magic 0x{magic:04X}")
    (entry_rva,) = _unpack_from("<I", data, optional_offset + 16)

    section_table = optional_offset + optional_size
    sections: list[dict[str, object]] = []
    for index in range(section_count):
        offset = section_table + index * 40
        if offset + 40 > len(data):
            raise PEFormatError("Section table extends beyond end of file")
        name_raw = data[offset : offset + 8]
        name = name_raw.split(b"\0", 1)[0].decode("ascii", errors="replace")
        (
            virtual_size,
            virtual_address,
            raw_size,
            raw_pointer,
            _,
            _,
            _,
            _,
            section_characteristics,
        ) = _unpack_from("<IIIIIIHHI", data, offset + 8)
        permissions = "".join(
            (
                "R" if section_characteristics & IMAGE_SCN_MEM_READ else "-",
                "W" if section_characteristics & IMAGE_SCN_MEM_WRITE else "-",
                "X" if section_characteristics & IMAGE_SCN_MEM_EXECUTE else "-",
            )
        )
        sections.append(
            {
                "name": name,
                "virtual_address": virtual_address,
                "virtual_size": virtual_size,
                "raw_pointer": raw_pointer,
                "raw_size": raw_size,
                "characteristics": section_characteristics,
                "permissions": permissions,
                "contains_entry_point": (
                    virtual_address <= entry_rva < virtual_address + max(virtual_size, raw_size)
                ),
            }
        )

    return {
        "file": path.name,
        "size": len(data),
        "format": format_name,
        "machine": MACHINE_NAMES.get(machine, f"unknown-0x{machine:04X}"),
        "coff_characteristics": characteristics,
        "entry_point_rva": entry_rva,
        "sections": sections,
    }


def print_table(result: dict[str, object]) -> None:
    print(
        f"File: {result['file']}  Format: {result['format']}  "
        f"Machine: {result['machine']}  Entry RVA: 0x{result['entry_point_rva']:08X}"
    )
    print("Name     RVA        VSize      RawPtr     RawSize    Flags      R/W/X  Entry")
    for section in result["sections"]:
        marker = "yes" if section["contains_entry_point"] else ""
        print(
            f"{section['name'][:8]:8} "
            f"0x{section['virtual_address']:08X} "
            f"0x{section['virtual_size']:08X} "
            f"0x{section['raw_pointer']:08X} "
            f"0x{section['raw_size']:08X} "
            f"0x{section['characteristics']:08X} "
            f"{section['permissions']:5}  {marker}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Read PE headers and section permissions without modifying the file.")
    parser.add_argument("path", type=Path, help="PE file to inspect")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    try:
        result = inspect_pe(args.path)
    except (OSError, PEFormatError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_table(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
