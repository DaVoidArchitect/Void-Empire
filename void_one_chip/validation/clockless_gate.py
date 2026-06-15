#!/usr/bin/env python3
"""
Clockless compliance gate for Void RTL sources.

Checks:
- no clock-like identifier usage (clk/clock naming patterns)
- all `always_ff` sensitivity lists are pulse/reset driven
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = Path(__file__).resolve().parent / "clockless_gate_report.json"

TARGET_DIRS = [
    REPO_ROOT / "src",
    REPO_ROOT / "validation" / "formal_core" / "src",
]

RESET_SIGNALS = {"state_reset_i"}
EXPLICIT_PULSE_SIGNALS = {
    "geometry_commit_i",
    "routing_pulse_i",
    "ledger_pulse_i",
    "update_pulse_i",
    "compute_pulse_i",
}


def blank_non_newline(text: str) -> str:
    return re.sub(r"[^\n]", " ", text)


def strip_comments_preserve_layout(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", lambda m: blank_non_newline(m.group(0)), text, flags=re.S)
    text = re.sub(r"//.*", lambda m: blank_non_newline(m.group(0)), text)
    return text


def iter_sv_files() -> Iterable[Path]:
    for base in TARGET_DIRS:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.sv")):
            if path.is_file():
                yield path


def is_clock_like_identifier(token: str) -> bool:
    t = token.lower()
    if t in {"clk", "clock"}:
        return True

    clock_like_patterns = (
        t.startswith("clk_"),
        t.endswith("_clk"),
        "_clk_" in t,
        t.startswith("clock_"),
        t.endswith("_clock"),
        "_clock_" in t,
    )
    return any(clock_like_patterns)


def is_allowed_pulse(signal: str) -> bool:
    return signal in EXPLICIT_PULSE_SIGNALS or signal.endswith("_pulse_i")


def analyze_file(path: Path) -> tuple[list[dict], list[dict]]:
    rel = path.relative_to(REPO_ROOT).as_posix()
    original = path.read_text(encoding="utf-8")
    code = strip_comments_preserve_layout(original)

    identifier_hits: list[dict] = []
    always_ff_violations: list[dict] = []

    token_pattern = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
    for line_no, line in enumerate(code.splitlines(), start=1):
        for match in token_pattern.finditer(line):
            token = match.group(0)
            if is_clock_like_identifier(token):
                identifier_hits.append(
                    {
                        "path": rel,
                        "line": line_no,
                        "identifier": token,
                    }
                )

    for match in re.finditer(r"always_ff\s*@\((?P<sens>[^)]*)\)", code, flags=re.M):
        sensitivity = match.group("sens")
        line_no = code.count("\n", 0, match.start()) + 1

        terms = [part.strip() for part in sensitivity.split("or") if part.strip()]
        if not terms:
            always_ff_violations.append(
                {
                    "path": rel,
                    "line": line_no,
                    "sensitivity": sensitivity.strip(),
                    "reason": "empty sensitivity list",
                }
            )
            continue

        non_reset_edges = 0
        for term in terms:
            edge_match = re.fullmatch(r"(posedge|negedge)\s+([A-Za-z_][A-Za-z0-9_]*)", term)
            if not edge_match:
                always_ff_violations.append(
                    {
                        "path": rel,
                        "line": line_no,
                        "sensitivity": sensitivity.strip(),
                        "reason": f"unsupported edge term '{term}'",
                    }
                )
                continue

            _edge, signal = edge_match.groups()
            if signal in RESET_SIGNALS:
                continue

            if is_allowed_pulse(signal):
                non_reset_edges += 1
            else:
                always_ff_violations.append(
                    {
                        "path": rel,
                        "line": line_no,
                        "sensitivity": sensitivity.strip(),
                        "reason": f"non-pulse sequential trigger '{signal}'",
                    }
                )

        if non_reset_edges != 1:
            always_ff_violations.append(
                {
                    "path": rel,
                    "line": line_no,
                    "sensitivity": sensitivity.strip(),
                    "reason": f"expected exactly one non-reset pulse edge, found {non_reset_edges}",
                }
            )

    return identifier_hits, always_ff_violations


def main() -> int:
    identifier_hits: list[dict] = []
    always_ff_violations: list[dict] = []
    files = list(iter_sv_files())

    for path in files:
        ids, sens = analyze_file(path)
        identifier_hits.extend(ids)
        always_ff_violations.extend(sens)

    # De-duplicate any repeated violation records from compound matching paths.
    dedup_ids = list({json.dumps(item, sort_keys=True): item for item in identifier_hits}.values())
    dedup_sens = list({json.dumps(item, sort_keys=True): item for item in always_ff_violations}.values())

    payload = {
        "scanned_sv_file_count": len(files),
        "target_dirs": [p.relative_to(REPO_ROOT).as_posix() for p in TARGET_DIRS if p.exists()],
        "forbidden_identifier_hits": sorted(
            dedup_ids, key=lambda x: (x["path"], int(x["line"]), x["identifier"])
        ),
        "always_ff_violations": sorted(
            dedup_sens, key=lambda x: (x["path"], int(x["line"]), x["reason"])
        ),
    }
    payload["pass"] = not payload["forbidden_identifier_hits"] and not payload["always_ff_violations"]

    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("[clockless_gate] scanned_sv_file_count:", payload["scanned_sv_file_count"])
    print("[clockless_gate] forbidden_identifier_hits:", len(payload["forbidden_identifier_hits"]))
    print("[clockless_gate] always_ff_violations:", len(payload["always_ff_violations"]))
    print("[clockless_gate] pass:", payload["pass"])
    print("[clockless_gate] report:", OUT_PATH)

    return 0 if payload["pass"] else 7


if __name__ == "__main__":
    raise SystemExit(main())
