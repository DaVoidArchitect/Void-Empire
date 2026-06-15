#!/usr/bin/env python3
"""Run strict, end-to-end release gates for Void production posture.

Pipeline:
1) Toolchain preflight
2) Phase-1 conformance
3) Core validation suite (strict flags)
4) Frontier readiness report generation
5) Release manifest generation
6) Stage-2/3/4 conformance
7) Platform motherboard-equivalence conformance
8) Full-chip digital twin conformance
9) Long-horizon ecosystem eons conformance

Writes:
- validation/strict_release_gates_report.json
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATION_DIR = ROOT / "validation"
REPORT_PATH = VALIDATION_DIR / "strict_release_gates_report.json"
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
    return StepResult(
        name=name,
        command=command,
        rc=proc.returncode,
        output_tail=(proc.stdout or "")[-6000:],
    )


def build_strict_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("XENALCHEMY_REQUIRE_SBY", "1")
    env.setdefault("XENALCHEMY_REQUIRE_QUTIP", "1")
    env.setdefault("XENALCHEMY_ENABLE_SPDK", "1")
    env.setdefault("XENALCHEMY_SPDK_AUTOGEN", "1")
    env.setdefault("XENALCHEMY_REQUIRE_LIVING_POLICY", "1")
    return env


def summarize(steps: list[StepResult]) -> tuple[dict[str, Any], int]:
    version = read_json(VERSION_PATH)
    suite = read_json(VALIDATION_DIR / "xenalchemy_test_report.json")
    readiness = read_json(VALIDATION_DIR / "frontier_readiness_report.json")
    manifest = read_json(VALIDATION_DIR / "xenalchemy_release_manifest.json")
    preflight = read_json(VALIDATION_DIR / "preflight_toolchain_report.json")
    phase1 = read_json(VALIDATION_DIR / "phase1_conformance_report.json")
    stage24 = read_json(VALIDATION_DIR / "stage24_conformance_report.json")
    stage4_ops = read_json(VALIDATION_DIR / "stage4_operational_hardening_report.json")
    platform_board = read_json(VALIDATION_DIR / "platform_board_conformance_report.json")
    digital_twin = read_json(VALIDATION_DIR / "digital_twin_report.json")
    motherboard_equivalence = read_json(VALIDATION_DIR / "motherboard_equivalence_report.json")
    ecosystem_eons = read_json(VALIDATION_DIR / "ecosystem_eons_report.json")

    all_steps_pass = all(step.rc == 0 for step in steps)
    suite_pass = bool(suite.get("overall_pass", False))
    phase1_pass = bool(phase1.get("overall_pass", False))
    stage24_pass = bool(stage24.get("overall_pass", False))
    stage4_ops_pass = bool(stage4_ops.get("pass", False))
    platform_board_pass = bool(platform_board.get("overall_pass", False))
    digital_twin_pass = bool(digital_twin.get("overall_pass", False))
    motherboard_equivalence_pass = bool(motherboard_equivalence.get("overall_pass", False))
    ecosystem_eons_pass = bool(ecosystem_eons.get("overall_pass", False))

    readiness_v2 = readiness.get("readiness_v2", {}) if isinstance(readiness.get("readiness_v2", {}), dict) else {}
    cert = str(readiness_v2.get("certification", "UNKNOWN"))

    payload = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "design_version": str(version.get("design_version", "UNKNOWN")),
        "release_id": str(version.get("release_id", "UNKNOWN")),
        "program_id": str(version.get("program_id", "UNKNOWN")),
        "strict_env": {
            "XENALCHEMY_REQUIRE_SBY": "1",
            "XENALCHEMY_REQUIRE_QUTIP": "1",
            "XENALCHEMY_ENABLE_SPDK": "1",
            "XENALCHEMY_SPDK_AUTOGEN": "1",
            "XENALCHEMY_REQUIRE_LIVING_POLICY": "1",
        },
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
        "phase1_conformance_pass": phase1_pass,
        "stage24_conformance_pass": stage24_pass,
        "stage4_operational_hardening_pass": stage4_ops_pass,
        "platform_board_conformance_pass": platform_board_pass,
        "digital_twin_conformance_pass": digital_twin_pass,
        "motherboard_equivalence_conformance_pass": motherboard_equivalence_pass,
        "ecosystem_eons_conformance_pass": ecosystem_eons_pass,
        "readiness_v2_index": readiness.get("frontier_readiness_index", "UNKNOWN"),
        "readiness_v2_certification": cert,
        "preflight_pass": preflight.get("pass", False),
        "release_manifest_tree_sha256": manifest.get("tree_sha256", "UNKNOWN"),
        "release_manifest_file_count": manifest.get("file_count", "UNKNOWN"),
    }

    payload["overall_strict_release_ready"] = bool(
        all_steps_pass
        and suite_pass
        and phase1_pass
        and stage24_pass
        and stage4_ops_pass
        and platform_board_pass
        and digital_twin_pass
        and motherboard_equivalence_pass
        and ecosystem_eons_pass
        and payload["preflight_pass"]
        and cert == "FRONTIER_V2_CERTIFIED"
    )

    return payload, (0 if payload["overall_strict_release_ready"] else 13)


def main() -> int:
    env = build_strict_env()

    steps = [
        run_cmd(
            "preflight_toolchain",
            [sys.executable, str(ROOT / "validation" / "preflight_toolchain.py"), "--strict"],
            env,
        ),
        run_cmd(
            "phase1_conformance",
            [sys.executable, str(ROOT / "validation" / "phase1_conformance.py")],
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
        run_cmd(
            "stage24_conformance",
            [sys.executable, str(ROOT / "validation" / "stage24_conformance.py")],
            env,
        ),
        run_cmd(
            "platform_board_conformance",
            [sys.executable, str(ROOT / "validation" / "platform_board_conformance.py")],
            env,
        ),
        run_cmd(
            "digital_twin_conformance",
            [sys.executable, str(ROOT / "validation" / "digital_twin_conformance.py")],
            env,
        ),
        run_cmd(
            "motherboard_equivalence_conformance",
            [sys.executable, str(ROOT / "validation" / "motherboard_equivalence_conformance.py")],
            env,
        ),
        run_cmd(
            "ecosystem_eons_conformance",
            [sys.executable, str(ROOT / "validation" / "ecosystem_eons_conformance.py")],
            env,
        ),
    ]

    payload, rc = summarize(steps)
    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("[strict_release] report:", REPORT_PATH)
    print("[strict_release] overall_strict_release_ready:", payload.get("overall_strict_release_ready", False))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
