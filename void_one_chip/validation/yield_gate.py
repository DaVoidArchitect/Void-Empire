#!/usr/bin/env python3
"""Yield-gate validator for statistical raw/mission-yield thresholds."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    path = root / "yield_report.json"

    if not path.exists():
        print("[yield_gate] fail: missing yield_report.json")
        return 9

    payload = json.loads(path.read_text(encoding="utf-8"))
    gates = payload.get("gates", {}) if isinstance(payload.get("gates", {}), dict) else {}
    failures = [name for name, ok in gates.items() if not bool(ok)]
    gate_pass = len(failures) == 0

    report = {
        "yield_report": str(path),
        "gates": gates,
        "failures": failures,
        "pass": gate_pass,
    }

    out_path = root / "yield_gate_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("[yield_gate] pass:", gate_pass)
    print("[yield_gate] failures:", len(failures))
    for item in failures:
        print("[yield_gate] fail:", item)

    return 0 if gate_pass else 10


if __name__ == "__main__":
    raise SystemExit(main())
