# Security Policy

## Scope

This repository contains read-only PE inspection and opt-in virtual serial-port test utilities. It must never contain proprietary binaries, drivers, credentials, activation data, crash dumps, machine identifiers, or personal paths.

## Safe use

- Inspect only files you own or are authorized to analyze.
- Run the serial test only against isolated virtual test ports.
- Do not connect the serial test to production PLCs, drives, instruments, or safety-related equipment.
- Do not disable system-wide DEP or other exploit protections for compatibility testing.

Before every publication, run:

```powershell
python tools/release_audit.py .
python -m unittest discover -s tests -v
```

Do not include sensitive values in an issue. Describe the category and affected file without posting the value itself.
