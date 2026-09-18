#!/usr/bin/env python3
"""Оновлює ключі в .env зі stdin (KEY=value), не чіпає SECRET_KEY/DB."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOWED_PREFIXES = (
    "TELEGRAM_",
    "WAYFORPAY_",
    "RECAPTCHA_",
    "NP_",
    "ADMIN_URL",
)

KEY_RE = re.compile(r"^([A-Z][A-Z0-9_]*)=(.*)$")


def allowed(key: str) -> bool:
    return any(key == p or key.startswith(p) for p in ALLOWED_PREFIXES)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: merge-env-keys.py /path/to/.env < keys.env", file=sys.stderr)
        return 2
    dest = Path(sys.argv[1])
    incoming: dict[str, str] = {}
    for raw in sys.stdin:
        line = raw.rstrip("\n")
        match = KEY_RE.match(line)
        if not match:
            continue
        key, value = match.group(1), match.group(2)
        if allowed(key):
            incoming[key] = value
    if not incoming:
        print("WARN: no allowed keys on stdin")
        return 0
    lines = dest.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        match = KEY_RE.match(line)
        if match and match.group(1) in incoming:
            key = match.group(1)
            out.append(f"{key}={incoming[key]}")
            seen.add(key)
        else:
            out.append(line)
    for key, value in incoming.items():
        if key not in seen:
            out.append(f"{key}={value}")
    dest.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"merged {len(incoming)} keys")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
