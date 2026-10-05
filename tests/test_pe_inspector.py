from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "inspect_pe_sections.py"


class PEInspectorTests(unittest.TestCase):
    def test_current_python_is_parsed_read_only(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), sys.executable, "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        self.assertIn(result["format"], {"PE32", "PE32+"})
        self.assertGreater(len(result["sections"]), 0)
        self.assertTrue(any(section["contains_entry_point"] for section in result["sections"]))

    def test_non_pe_input_is_rejected(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), str(ROOT / "README.md")],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("error:", completed.stderr)


if __name__ == "__main__":
    unittest.main()
