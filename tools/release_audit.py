#!/usr/bin/env python3
"""Fail closed when a release tree contains binary, private, or product-specific material."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path


FORBIDDEN_EXTENSIONS = {
    ".7z",
    ".activate",
    ".bak",
    ".cat",
    ".chm",
    ".dll",
    ".dmp",
    ".evtx",
    ".exe",
    ".inf",
    ".key",
    ".msi",
    ".orig",
    ".patched",
    ".pfx",
    ".sys",
    ".vxd",
    ".zip",
}

TEXT_RULES = {
    "absolute Windows path": re.compile(r"(?i)(?:[A-Z]:\\|C:\\Users\\)"),
    "machine name": re.compile(r"(?i)\b(?:DESKTOP|LAPTOP)-[A-Z0-9-]+\b"),
    "email address": re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    "phone number": re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)"),
    "OpenAI-style key": re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    "GitHub token": re.compile(r"(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
}

# Build sensitive product-specific terms from fragments so this audit file does not match itself.
BLOCKED_TERMS = (
    "VSPD" + "CTL",
    "ALT" + "USERNAME",
    "USER" + "KEY",
    "Virtual Serial Port " + "Driver 6.9",
    "Seek n' " + "Destroy",
)

SKIP_DIRECTORIES = {".git", ".mypy_cache", ".pytest_cache", "__pycache__"}

# Only these manually reviewed screenshots may bypass UTF-8 text inspection.
# Any replacement needs visual privacy review and an updated SHA-256 digest.
REVIEWED_SCREENSHOTS = {
    "docs/images/virtual-serial-port.jpg": (
        b"\xff\xd8\xff",
        "9085a8bc7b6d6d8f11e689afe951eb1d0e46c438390aa485c096d7d4ffb1f753",
    ),
    "docs/images/tool-results.png": (
        b"\x89PNG\r\n\x1a\n",
        "2fce1747bb77ce0fa05c79537414f7323ca8ad649b7fcbbc230074c0d6c55dbf",
    ),
}


def audit(root: Path) -> list[str]:
    findings: list[str] = []
    self_path = Path(__file__).resolve()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in SKIP_DIRECTORIES for part in path.parts):
            continue
        relative = path.relative_to(root)
        if path.suffix.casefold() in FORBIDDEN_EXTENSIONS:
            findings.append(f"{relative}: forbidden file extension")
            continue
        if path.resolve() == self_path:
            continue
        if path.stat().st_size > 2_000_000:
            findings.append(f"{relative}: file exceeds 2 MB review limit")
            continue
        if relative.as_posix() in REVIEWED_SCREENSHOTS:
            signature, digest = REVIEWED_SCREENSHOTS[relative.as_posix()]
            data = path.read_bytes()
            if not data.startswith(signature):
                findings.append(f"{relative}: expected a reviewed screenshot image")
            elif hashlib.sha256(data).hexdigest() != digest:
                findings.append(f"{relative}: screenshot changed; visual privacy review required")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            findings.append(f"{relative}: non-UTF-8 or unreadable file")
            continue
        for label, rule in TEXT_RULES.items():
            if rule.search(text):
                findings.append(f"{relative}: {label}")
        lowered = text.casefold()
        for term in BLOCKED_TERMS:
            if term.casefold() in lowered:
                findings.append(f"{relative}: product-specific or credential-related term")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a repository before publication.")
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args()
    findings = audit(args.root.resolve())
    if findings:
        print("AUDIT FAILED")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("AUDIT PASSED: no blocked binary, private, secret-like, or product-specific material found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
