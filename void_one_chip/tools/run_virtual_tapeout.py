#!/usr/bin/env python3
"""Run an open-source virtual tape-out flow for Void One.

This orchestration script executes an evidence-first pre-fab flow:

1) GDS generation
2) Validation suite (formal + TCAD + channel + materials + yield + synthetic PDK)
3) Frontier readiness scoring
4) Release manifest generation

Outputs:
- validation/virtual_tapeout_report.json
- validation/virtual_tapeout_summary.md
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATION_DIR = ROOT / "validation"
REPORT_JSON = VALIDATION_DIR / "virtual_tapeout_report.json"
SUMMARY_MD = VALIDATION_DIR / "virtual_tapeout_summary.md"
VERSION_PATH = ROOT / "VERSION.json"


@dataclass
class StepResult:
    name: str
    command: list[str]
    rc: int
    output_tail: str


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    return data if isinstance(data, dict) else {}


def run_cmd(name: str, command: list[str], env: dict[str, str]) -> StepResult:
    proc = subprocess.run(
        command,
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    out = proc.stdout or ""
    return StepResult(name=name, command=command, rc=proc.returncode, output_tail=out[-6000:])


def detect_tooling() -> dict[str, str | None]:
    checks = [
        "python",
        "yosys",
        "sby",
        "yowasp-sby",
        "z3",
        "iverilog",
        "verilator",
        "openroad",
        "opensta",
        "magic",
        "netgen",
        "klayout",
    ]
    return {name: shutil.which(name) for name in checks}


def build_env(strict: bool) -> dict[str, str]:
    env = os.environ.copy()

    if strict:
        env.setdefault("XENALCHEMY_REQUIRE_SBY", "1")
        env.setdefault("XENALCHEMY_REQUIRE_QUTIP", "1")
        env.setdefault("XENALCHEMY_ENABLE_SPDK", "1")
        env.setdefault("XENALCHEMY_SPDK_AUTOGEN", "1")

    return env


def summarize(
    steps: list[StepResult],
    strict: bool,
    version: dict[str, Any],
    tool_paths: dict[str, str | None],
) -> tuple[dict[str, Any], str, int]:
    suite = read_json(VALIDATION_DIR / "xenalchemy_test_report.json")
    readiness = read_json(VALIDATION_DIR / "frontier_readiness_report.json")
    manifest = read_json(VALIDATION_DIR / "xenalchemy_release_manifest.json")

    all_steps_pass = all(step.rc == 0 for step in steps)
    suite_pass = bool(suite.get("overall_pass", False))
    ready_idx = readiness.get("frontier_readiness_index", "UNKNOWN")
    readiness_v2 = readiness.get("readiness_v2", {})
    cert = (
        readiness_v2.get("certification", "UNKNOWN")
        if isinstance(readiness_v2, dict)
        else "UNKNOWN"
    )
    release_id = str(version.get("release_id", "UNKNOWN"))
    design_version = str(version.get("design_version", "UNKNOWN"))

    overall_ready = bool(all_steps_pass and suite_pass)
    final_rc = 0 if overall_ready else 5

    payload = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "flow": "virtual_tapeout_open_source",
        "strict_mode": strict,
        "design_name": str(version.get("design_name", "Void One")),
        "design_version": design_version,
        "release_id": release_id,
        "program_id": str(version.get("program_id", "UNKNOWN")),
        "step_results": [
            {
                "name": s.name,
                "command": s.command,
                "rc": s.rc,
                "pass": s.rc == 0,
                "output_tail": s.output_tail,
            }
            for s in steps
        ],
        "all_steps_pass": all_steps_pass,
        "validation_overall_pass": suite_pass,
        "frontier_readiness_index": ready_idx,
        "frontier_certification": cert,
        "release_manifest": {
            "file_count": manifest.get("file_count", "UNKNOWN"),
            "tree_sha256": manifest.get("tree_sha256", "UNKNOWN"),
        },
        "tooling_detection": tool_paths,
        "overall_virtual_tapeout_ready": overall_ready,
    }

    rows = []
    for s in steps:
        status = "PASS" if s.rc == 0 else "FAIL"
        rows.append(f"| {s.name} | `{status}` | `{s.rc}` |")

    missing_tools = [k for k, v in tool_paths.items() if not v]
    missing_line = ", ".join(missing_tools) if missing_tools else "none"
    md = "\n".join(
        [
            "# Void One Virtual Tape-Out Summary",
            "",
            f"- **Generated (UTC):** {payload['generated_utc']}",
            f"- **Design Version:** `{design_version}`",
            f"- **Release ID:** `{release_id}`",
            f"- **Strict Mode:** `{strict}`",
            "",
            "## Step Results",
            "",
            "| Step | Status | Return Code |",
            "|---|---:|---:|",
            *rows,
            "",
            "## Readiness Signals",
            "",
            f"- **Validation Overall Pass:** `{suite_pass}`",
            f"- **Frontier Readiness Index:** `{ready_idx}`",
            f"- **Certification:** `{cert}`",
            f"- **Release Manifest File Count:** `{manifest.get('file_count', 'UNKNOWN')}`",
            f"- **Release Manifest Tree SHA-256:** `{manifest.get('tree_sha256', 'UNKNOWN')}`",
            "",
            "## Tooling Detection (Open Source)",
            "",
            f"- **Missing Tools in PATH:** {missing_line}",
            "",
            "## Physical Fabrication Note",
            "",
            "This virtual tape-out validates design and evidence readiness using open tools. Physical",
            "fabrication still requires a cleanroom-capable foundry or packaging partner.",
            "",
            f"## Final Verdict: `{'TAPE-OUT READY (VIRTUAL)' if overall_ready else 'NOT READY'}`",
            "",
        ]
    )

    return payload, md, final_rc


def main() -> int:
    strict = os.environ.get("VOID_VTO_STRICT", "1").strip().lower() not in {"0", "false", "no", "off"}
    env = build_env(strict)
    version = read_json(VERSION_PATH)
    tool_paths = detect_tooling()

    steps = [
        run_cmd(
            "build_gds",
            [sys.executable, str(ROOT / "AlchemyGDSII" / "build_alchemy_gdsii.py")],
            env,
        ),
        run_cmd(
            "run_validation_suite",
            [sys.executable, str(ROOT / "validation" / "run_xenalchemy_tests.py")],
            env,
        ),
        run_cmd(
            "generate_frontier_readiness",
            [sys.executable, str(ROOT / "tools" / "generate_frontier_readiness_report.py")],
            env,
        ),
        run_cmd(
            "generate_release_manifest",
            [sys.executable, str(ROOT / "tools" / "generate_xenalchemy_release_manifest.py")],
            env,
        ),
    ]

    payload, summary_md, rc = summarize(steps, strict, version, tool_paths)

    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    SUMMARY_MD.write_text(summary_md, encoding="utf-8")

    print("[virtual_tapeout] strict_mode:", strict)
    print("[virtual_tapeout] report:", REPORT_JSON)
    print("[virtual_tapeout] summary:", SUMMARY_MD)
    print("[virtual_tapeout] overall_virtual_tapeout_ready:", payload["overall_virtual_tapeout_ready"])
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
