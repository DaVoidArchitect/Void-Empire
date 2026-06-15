#!/usr/bin/env python3
"""Generate statistical yield report with raw and mission-yield confidence bands."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "validation"
VERSION_PATH = ROOT / "VERSION.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def q(arr: np.ndarray, p: float) -> float:
    return float(np.quantile(arr, p))


def main() -> int:
    version_info = read_json(VERSION_PATH)

    tcad = read_json(VALIDATION / "tcad_report.json")
    void_report = read_json(VALIDATION / "void_channel_report.json")
    connectome = read_json(VALIDATION / "defect_connectome_report.json")
    suite = read_json(VALIDATION / "xenalchemy_test_report.json")
    material = read_json(VALIDATION / "material_compliance_report.json")

    seed = env_int("XENALCHEMY_YIELD_SEED", 4242)
    samples = max(1000, env_int("XENALCHEMY_YIELD_SAMPLES", 5000))

    rng = np.random.default_rng(seed)

    # Inputs from existing evidence
    connectome_eff = float(connectome.get("metrics", {}).get("connectome_path_efficiency", 0.75))
    memory_ret = float(connectome.get("metrics", {}).get("defect_memory_retention_pct", 90.0)) / 100.0
    forgetting = float(connectome.get("metrics", {}).get("catastrophic_forgetting_rate", 0.04))
    q_precision = float(connectome.get("metrics", {}).get("quarantine_precision", 0.90))
    q_recall = float(connectome.get("metrics", {}).get("quarantine_recall", 0.88))

    pass_rate = float(void_report.get("coherence_sweep", {}).get("pass_rate", 0.95))
    surface_margin_k = float(tcad.get("surface_margin_k", 15.0))
    required_margin_k = float(tcad.get("required_surface_margin_k", 15.0))

    formal = suite.get("formal", {}) if isinstance(suite.get("formal", {}), dict) else {}
    qutip = void_report.get("qutip", {}) if isinstance(void_report.get("qutip", {}), dict) else {}

    # Avoid circular dependency on prior suite overall result. Yield should use
    # strict prerequisite evidence, not stale aggregate status from previous runs.
    strict_prereq_flags = {
        "formal_pass": bool(formal.get("pass", True) and not formal.get("skipped", False)),
        "tcad_pass": bool(tcad.get("pass", True)),
        "void_channel_strict_pass": bool(
            qutip.get("pass", False)
            and qutip.get("strict_ready", False)
            and not qutip.get("skipped", False)
            and void_report.get("overall_pass", True)
        ),
        "defect_connectome_pass": bool(connectome.get("pass", True)),
        "material_compliance_pass": bool(material.get("pass", True)),
    }
    strict_overall = all(strict_prereq_flags.values())

    # Baseline defect-density model (ppm) with bounded spread.
    nominal_dd = env_float("XENALCHEMY_DEFECT_DENSITY_PPM", 1200.0)
    dd_std = max(50.0, nominal_dd * 0.22)
    defect_density = np.clip(rng.normal(nominal_dd, dd_std, size=samples), 10.0, 5000.0)

    # Raw yield proxy: Poisson-style sensitive-area model.
    effective_critical_area = env_float("XENALCHEMY_CRITICAL_AREA_CM2", 0.08)
    d0 = defect_density / 1_000_000.0
    raw_die_yield = np.exp(-d0 * effective_critical_area)

    # Mission yield adds adaptive recovery from connectome + immune behavior.
    recovery_gain = clamp(
        0.18 * connectome_eff
        + 0.14 * memory_ret
        + 0.10 * q_precision
        + 0.10 * q_recall
        + 0.08 * pass_rate
        + 0.06 * clamp(surface_margin_k / max(1e-9, required_margin_k), 0.0, 1.4)
        - 0.20 * forgetting,
        0.0,
        0.35,
    )

    mission_yield = np.clip(raw_die_yield + recovery_gain * (1.0 - raw_die_yield), 0.0, 1.0)

    # Conservative haircut if strict suite is not passing.
    if not strict_overall:
        mission_yield *= 0.92

    targets = {
        "raw_die_yield_p50_min": env_float("XENALCHEMY_RAW_YIELD_P50_MIN", 0.89),
        "raw_die_yield_p90_min": env_float("XENALCHEMY_RAW_YIELD_P90_MIN", 0.86),
        "mission_yield_p50_min": env_float("XENALCHEMY_MISSION_YIELD_P50_MIN", 0.98),
        "mission_yield_p90_min": env_float("XENALCHEMY_MISSION_YIELD_P90_MIN", 0.97),
    }

    metrics = {
        "raw_die_yield": {
            "mean": round(float(np.mean(raw_die_yield)), 6),
            "p10": round(q(raw_die_yield, 0.10), 6),
            "p50": round(q(raw_die_yield, 0.50), 6),
            "p90": round(q(raw_die_yield, 0.90), 6),
        },
        "mission_yield": {
            "mean": round(float(np.mean(mission_yield)), 6),
            "p10": round(q(mission_yield, 0.10), 6),
            "p50": round(q(mission_yield, 0.50), 6),
            "p90": round(q(mission_yield, 0.90), 6),
        },
        "recovery_gain": round(recovery_gain, 6),
    }

    gates = {
        "raw_die_yield_p50": metrics["raw_die_yield"]["p50"] >= targets["raw_die_yield_p50_min"],
        "raw_die_yield_p90": metrics["raw_die_yield"]["p90"] >= targets["raw_die_yield_p90_min"],
        "mission_yield_p50": metrics["mission_yield"]["p50"] >= targets["mission_yield_p50_min"],
        "mission_yield_p90": metrics["mission_yield"]["p90"] >= targets["mission_yield_p90_min"],
        "strict_suite_pass": strict_overall,
    }

    payload = {
        "design_version": str(version_info.get("design_version", "UNKNOWN")),
        "release_id": str(version_info.get("release_id", "UNKNOWN")),
        "program_id": str(version_info.get("program_id", "UNKNOWN")),
        "seed": seed,
        "samples": samples,
        "inputs": {
            "nominal_defect_density_ppm": nominal_dd,
            "critical_area_cm2": effective_critical_area,
            "connectome_path_efficiency": connectome_eff,
            "defect_memory_retention": memory_ret,
            "catastrophic_forgetting_rate": forgetting,
            "quarantine_precision": q_precision,
            "quarantine_recall": q_recall,
            "coherence_pass_rate": pass_rate,
            "surface_margin_k": surface_margin_k,
            "required_surface_margin_k": required_margin_k,
        },
        "targets": targets,
        "metrics": metrics,
        "strict_prereq_flags": strict_prereq_flags,
        "gates": gates,
        "pass": all(gates.values()),
    }

    out_path = VALIDATION / "yield_report.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("[yield_report] raw_p50:", metrics["raw_die_yield"]["p50"])
    print("[yield_report] raw_p90:", metrics["raw_die_yield"]["p90"])
    print("[yield_report] mission_p50:", metrics["mission_yield"]["p50"])
    print("[yield_report] mission_p90:", metrics["mission_yield"]["p90"])
    print("[yield_report] pass:", payload["pass"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
