#!/usr/bin/env python3
"""Send one payload between two explicitly confirmed test serial ports."""

from __future__ import annotations

import argparse
import secrets
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a dedicated virtual serial-port pair.")
    parser.add_argument("--tx", required=True, help="transmit port, for example COM10")
    parser.add_argument("--rx", required=True, help="receive port, for example COM11")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--message", help="ASCII payload; a random test payload is used by default")
    parser.add_argument(
        "--confirm-test-ports",
        action="store_true",
        help="confirm both ports are isolated test ports and not production hardware",
    )
    args = parser.parse_args()

    if not args.confirm_test_ports:
        print("Refusing to transmit: add --confirm-test-ports after checking both endpoints.", file=sys.stderr)
        return 2
    if args.tx.casefold() == args.rx.casefold():
        print("TX and RX must be different ports.", file=sys.stderr)
        return 2
    if args.baud <= 0 or args.timeout <= 0:
        print("Baud rate and timeout must be positive.", file=sys.stderr)
        return 2

    try:
        import serial
    except ImportError:
        print("pyserial is required; install dependencies from requirements.txt.", file=sys.stderr)
        return 2

    payload_text = args.message or f"LOOPBACK-{secrets.token_hex(8)}"
    try:
        payload = payload_text.encode("ascii", errors="strict")
    except UnicodeEncodeError:
        print("The payload must contain ASCII characters only.", file=sys.stderr)
        return 2

    try:
        with serial.Serial(args.rx, args.baud, timeout=args.timeout) as receiver:
            receiver.reset_input_buffer()
            with serial.Serial(args.tx, args.baud, timeout=args.timeout) as sender:
                time.sleep(0.1)
                sender.write(payload)
                sender.flush()
                received = receiver.read(len(payload))
    except serial.SerialException as exc:
        print(f"Serial error: {exc}", file=sys.stderr)
        return 3

    if received != payload:
        print(f"FAIL: sent {len(payload)} bytes, received {len(received)} bytes.")
        return 1
    print(f"PASS: {len(payload)} bytes matched exactly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
