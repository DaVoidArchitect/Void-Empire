#!/usr/bin/env python3
"""
Generate a frontier-readiness score from existing VOID evidence artifacts.

Reads:
- validation/xenalchemy_test_report.json
- validation/tcad_report.json
- validation/void_channel_report.json
- pdk/synthetic_v1/generated/synthetic_evidence_summary.json
- validation/living_system_kpi_template.json

Writes:
- validation/frontier_readiness_report.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "validation"
SPDK_SUMMARY = ROOT / "pdk" / "synthetic_v1" / "generated" / "synthetic_evidence_summary.json"
VERSION_PATH = ROOT / "VERSION.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def pass_score(flag: bool) -> float:
    return 1.0 if flag else 0.0


def kpi_conformance(kpis: dict[str, Any]) -> tuple[bool, list[str], int, int]:
    failures: list[str] = []
    checked = 0
    populated = 0

    for name, meta in kpis.items():
        if not isinstance(meta, dict):
            failures.append(f"{name}: malformed KPI metadata")
            continue

        checked += 1
        value = meta.get("value")
        if value is None:
            failures.append(f"{name}: missing value")
            continue

        populated += 1
        try:
            v = float(value)
        except Exception:  # noqa: BLE001
            failures.append(f"{name}: non-numeric value")
            continue

        if "target_max" in meta:
            try:
                tmax = float(meta["target_max"])
                if v > tmax:
                    failures.append(f"{name}: {v:.6f} exceeds target_max {tmax:.6f}")
            except Exception:  # noqa: BLE001
                failures.append(f"{name}: invalid target_max")

        if "target_min" in meta:
            try:
                tmin = float(meta["target_min"])
                if v < tmin:
                    failures.append(f"{name}: {v:.6f} below target_min {tmin:.6f}")
            except Exception:  # noqa: BLE001
                failures.append(f"{name}: invalid target_min")

    return len(failures) == 0, failures, populated, checked


def main() -> int:
    version_info = read_json(VERSION_PATH)

    suite = read_json(VALIDATION / "xenalchemy_test_report.json")
    tcad = read_json(VALIDATION / "tcad_report.json")
    void_report = read_json(VALIDATION / "void_channel_report.json")
    connectome_report = read_json(VALIDATION / "defect_connectome_report.json")
    yield_report = read_json(VALIDATION / "yield_report.json")
    spdk = read_json(SPDK_SUMMARY)
    kpi_template = read_json(VALIDATION / "living_system_kpi_template.json")

    formal = suite.get("formal", {}) if isinstance(suite.get("formal", {}), dict) else {}
    tcad_suite = suite.get("tcad", {}) if isinstance(suite.get("tcad", {}), dict) else {}
    void_suite = (
        suite.get("void_channel", {}) if isinstance(suite.get("void_channel", {}), dict) else {}
    )
    material_suite = (
        suite.get("material_compliance", {})
        if isinstance(suite.get("material_compliance", {}), dict)
        else {}
    )
    spdk_suite = (
        suite.get("synthetic_pdk", {}) if isinstance(suite.get("synthetic_pdk", {}), dict) else {}
    )
    connectome_suite = (
        suite.get("defect_connectome", {})
        if isinstance(suite.get("defect_connectome", {}), dict)
        else {}
    )
    yield_suite = (
        suite.get("yield_model", {}) if isinstance(suite.get("yield_model", {}), dict) else {}
    )
    yield_gate_suite = (
        suite.get("yield_gate", {}) if isinstance(suite.get("yield_gate", {}), dict) else {}
    )

    formal_score = pass_score(bool(formal.get("pass", False)))
    tcad_score = pass_score(bool(suite.get("tcad", {}).get("pass", False)))
    void_score = pass_score(bool(suite.get("void_channel", {}).get("pass", False)))
    material_score = pass_score(bool(suite.get("material_compliance", {}).get("pass", False)))
    spdk_score = pass_score(bool(suite.get("synthetic_pdk", {}).get("pass", False)))

    surface_temp = float(tcad.get("l0_surface_temp_k", 9999.0))
    surface_margin_k = 315.0 - surface_temp
    thermal_margin_score = clamp01(surface_margin_k / 20.0)

    viability_score = float(spdk.get("metrics", {}).get("viability_score", 0.0))
    viability_threshold = float(spdk.get("metrics", {}).get("viability_threshold", 0.72))
    viability_headroom = float(spdk.get("metrics", {}).get("viability_headroom", 0.0))
    viability_headroom_target = float(
        spdk.get("metrics", {}).get("viability_headroom_target", 0.08)
    )
    viability_margin = viability_score - viability_threshold
    viability_margin_score = clamp01((viability_margin + 0.10) / 0.20)
    viability_headroom_score = clamp01(viability_headroom / max(1e-9, viability_headroom_target))

    qutip = void_report.get("qutip", {}) if isinstance(void_report.get("qutip", {}), dict) else {}
    strict_qutip_ready = bool(
        qutip.get("pass", False)
        and qutip.get("strict_ready", False)
        and not qutip.get("skipped", False)
    )
    qutip_strict_score = pass_score(strict_qutip_ready)

    kpis = kpi_template.get("kpis", {}) if isinstance(kpi_template.get("kpis", {}), dict) else {}
    kpi_slots = len(kpis)
    kpi_targets_pass, kpi_failures, kpi_populated, _ = kpi_conformance(kpis)
    evidence_completeness = (kpi_populated / kpi_slots) if kpi_slots else 0.0

    max_heat_load = float(tcad.get("max_heat_load_k", 0.0))
    max_heat_target = 950.0
    max_heat_profile = (
        tcad.get("stress_profiles", {}).get("max_heat_load", {})
        if isinstance(tcad.get("stress_profiles", {}), dict)
        else {}
    )
    max_heat_profile_pass = bool(max_heat_profile.get("pass", False))
    max_heat_band = str(max_heat_profile.get("transmutation_band", ""))
    max_heat_profile_temp = float(max_heat_profile.get("core_temp_k", 0.0))
    required_surface_margin_k = float(tcad.get("required_surface_margin_k", 15.0))

    coherence_sweep = (
        void_report.get("coherence_sweep", {})
        if isinstance(void_report.get("coherence_sweep", {}), dict)
        else {}
    )

    connectome_metrics = (
        connectome_report.get("metrics", {})
        if isinstance(connectome_report.get("metrics", {}), dict)
        else {}
    )
    yield_metrics = (
        yield_report.get("metrics", {}) if isinstance(yield_report.get("metrics", {}), dict) else {}
    )
    yield_gates = (
        yield_report.get("gates", {}) if isinstance(yield_report.get("gates", {}), dict) else {}
    )

    connectome_path_efficiency = float(connectome_metrics.get("connectome_path_efficiency", 0.0))
    plasticity_convergence_time = float(connectome_metrics.get("plasticity_convergence_time", 9999.0))
    catastrophic_forgetting_rate = float(connectome_metrics.get("catastrophic_forgetting_rate", 1.0))
    defect_memory_retention_pct = float(connectome_metrics.get("defect_memory_retention_pct", 0.0))
    quarantine_precision = float(connectome_metrics.get("quarantine_precision", 0.0))
    quarantine_recall = float(connectome_metrics.get("quarantine_recall", 0.0))

    mission_yield = (
        yield_metrics.get("mission_yield", {})
        if isinstance(yield_metrics.get("mission_yield", {}), dict)
        else {}
    )
    raw_yield = (
        yield_metrics.get("raw_die_yield", {})
        if isinstance(yield_metrics.get("raw_die_yield", {}), dict)
        else {}
    )

    mission_yield_p90 = float(mission_yield.get("p90", 0.0))
    mission_yield_p50 = float(mission_yield.get("p50", 0.0))
    raw_yield_p90 = float(raw_yield.get("p90", 0.0))

    hard_gates = {
        "formal_strict_pass": bool(formal.get("pass", False) and not formal.get("skipped", False)),
        "tcad_nominal_pass": bool(tcad_suite.get("pass", False)),
        "tcad_surface_margin_enforced": bool(surface_margin_k >= required_surface_margin_k),
        "tcad_max_heat_950k_pass": bool(
            max_heat_profile_pass
            and abs(max_heat_profile_temp - max_heat_target) <= 1e-6
            and abs(max_heat_load - max_heat_target) <= 1e-6
            and max_heat_band == "SovereignExcursion"
        ),
        "void_channel_strict_pass": bool(void_suite.get("pass", False) and strict_qutip_ready),
        "coherence_sweep_threshold": bool(coherence_sweep.get("passes_threshold", False)),
        "defect_connectome_pass": bool(connectome_suite.get("pass", False)),
        "connectome_path_efficiency": bool(connectome_path_efficiency >= 0.78),
        "plasticity_convergence_time": bool(plasticity_convergence_time <= 12.0),
        "catastrophic_forgetting_rate": bool(catastrophic_forgetting_rate <= 0.05),
        "defect_memory_retention_pct": bool(defect_memory_retention_pct >= 90.0),
        "quarantine_precision": bool(quarantine_precision >= 0.90),
        "quarantine_recall": bool(quarantine_recall >= 0.88),
        "material_compliance_pass": bool(material_suite.get("pass", False)),
        "synthetic_pdk_pass": bool(spdk_suite.get("pass", False) and spdk.get("pass", False)),
        "synthetic_viability_headroom_pass": bool(
            viability_headroom >= viability_headroom_target
            and bool(spdk.get("metrics", {}).get("viability_headroom_pass", False))
        ),
        "yield_model_pass": bool(yield_suite.get("pass", False)),
        "yield_gate_pass": bool(yield_gate_suite.get("pass", False)),
        "mission_yield_p90": bool(mission_yield_p90 >= 0.97),
        "mission_yield_p50": bool(mission_yield_p50 >= 0.98),
        "raw_yield_p90": bool(raw_yield_p90 >= 0.86),
        "yield_report_gates": bool(yield_gates and all(bool(v) for v in yield_gates.values())),
        "evidence_completeness_full": bool(kpi_slots > 0 and kpi_populated == kpi_slots),
        "kpi_target_conformance": kpi_targets_pass,
    }

    hard_gate_total = len(hard_gates)
    hard_gate_pass_count = sum(1 for v in hard_gates.values() if v)
    hard_gate_fraction = hard_gate_pass_count / hard_gate_total if hard_gate_total else 0.0
    hard_gate_failures = [k for k, v in hard_gates.items() if not v]

    components = {
        "formal": formal_score,
        "tcad": tcad_score,
        "void_channel": void_score,
        "defect_connectome": pass_score(bool(connectome_suite.get("pass", False))),
        "material_compliance": material_score,
        "synthetic_pdk": spdk_score,
        "yield_model": pass_score(bool(yield_suite.get("pass", False) and yield_gate_suite.get("pass", False))),
        "thermal_margin": thermal_margin_score,
        "viability_margin": viability_margin_score,
        "viability_headroom": viability_headroom_score,
        "strict_qutip_readiness": qutip_strict_score,
        "evidence_completeness": evidence_completeness,
    }

    weights = {
        "formal": 0.15,
        "tcad": 0.08,
        "void_channel": 0.08,
        "defect_connectome": 0.08,
        "material_compliance": 0.08,
        "synthetic_pdk": 0.08,
        "yield_model": 0.08,
        "thermal_margin": 0.10,
        "viability_margin": 0.10,
        "viability_headroom": 0.07,
        "strict_qutip_readiness": 0.05,
        "evidence_completeness": 0.13,
    }

    legacy_weighted_index = 0.0
    for key, weight in weights.items():
        legacy_weighted_index += components.get(key, 0.0) * weight
    legacy_weighted_index = clamp01(legacy_weighted_index)

    readiness_v2_index = 1.0 if not hard_gate_failures else clamp01(min(legacy_weighted_index, hard_gate_fraction))

    recommendations: list[str] = []
    if thermal_margin_score < 0.20 or not hard_gates["tcad_surface_margin_enforced"]:
        recommendations.append(
            "Increase thermal margin: current L0 surface is too close to safety threshold."
        )
    if viability_margin_score < 0.30:
        recommendations.append(
            "Increase synthetic PDK viability headroom above threshold to reduce fragility."
        )
    if not hard_gates["synthetic_viability_headroom_pass"]:
        recommendations.append(
            "Raise synthetic viability headroom to meet readiness-v2 hard gate."
        )
    if not strict_qutip_ready:
        recommendations.append(
            "Enable strict QuTiP environment and pass with XENALCHEMY_REQUIRE_QUTIP=1."
        )
    if not hard_gates["defect_connectome_pass"]:
        recommendations.append(
            "Pass defect connectome mesh gate (path efficiency/plasticity/quarantine metrics)."
        )
    if not hard_gates["yield_gate_pass"]:
        recommendations.append(
            "Pass yield gate with statistical confidence targets (P50/P90)."
        )
    if not hard_gates["tcad_max_heat_950k_pass"]:
        recommendations.append(
            "Demonstrate explicit 950K stress-profile pass in SovereignExcursion band."
        )
    if evidence_completeness < 0.5:
        recommendations.append(
            "Populate living-system KPI values to improve funding-grade evidence completeness."
        )
    if not kpi_targets_pass:
        recommendations.append("Bring KPI values within declared target_min/target_max bounds.")

    if not recommendations and not hard_gate_failures:
        recommendations.append("All readiness-v2 hard gates satisfied. Maintain reproducibility discipline.")

    report = {
        "design_version": str(version_info.get("design_version", "UNKNOWN")),
        "release_id": str(version_info.get("release_id", "UNKNOWN")),
        "program_id": str(version_info.get("program_id", "UNKNOWN")),
        "frontier_readiness_index": round(readiness_v2_index, 6),
        "readiness_v2": {
            "index": round(readiness_v2_index, 6),
            "hard_gate_fraction": round(hard_gate_fraction, 6),
            "hard_gate_pass_count": hard_gate_pass_count,
            "hard_gate_total": hard_gate_total,
            "hard_gates": hard_gates,
            "failed_hard_gates": hard_gate_failures,
            "certification": "FRONTIER_V2_CERTIFIED" if not hard_gate_failures else "FRONTIER_V2_CONDITIONAL",
        },
        "legacy_weighted_index": round(legacy_weighted_index, 6),
        "component_scores": {k: round(v, 6) for k, v in components.items()},
        "weights": weights,
        "derived_metrics": {
            "surface_temp_k": surface_temp,
            "surface_margin_k": round(surface_margin_k, 6),
            "required_surface_margin_k": round(required_surface_margin_k, 6),
            "max_heat_load_k": round(max_heat_load, 6),
            "max_heat_profile_core_temp_k": round(max_heat_profile_temp, 6),
            "max_heat_profile_band": max_heat_band,
            "max_heat_profile_pass": max_heat_profile_pass,
            "connectome_path_efficiency": round(connectome_path_efficiency, 6),
            "plasticity_convergence_time": round(plasticity_convergence_time, 6),
            "catastrophic_forgetting_rate": round(catastrophic_forgetting_rate, 6),
            "defect_memory_retention_pct": round(defect_memory_retention_pct, 6),
            "quarantine_precision": round(quarantine_precision, 6),
            "quarantine_recall": round(quarantine_recall, 6),
            "mission_yield_p50": round(mission_yield_p50, 6),
            "mission_yield_p90": round(mission_yield_p90, 6),
            "raw_yield_p90": round(raw_yield_p90, 6),
            "synthetic_viability_score": round(viability_score, 6),
            "synthetic_viability_threshold": round(viability_threshold, 6),
            "synthetic_viability_margin": round(viability_margin, 6),
            "synthetic_viability_headroom": round(viability_headroom, 6),
            "synthetic_viability_headroom_target": round(viability_headroom_target, 6),
            "synthetic_viability_headroom_pass": bool(
                spdk.get("metrics", {}).get("viability_headroom_pass", False)
            ),
            "kpi_populated": kpi_populated,
            "kpi_slots": kpi_slots,
            "kpi_target_failures": kpi_failures,
        },
        "recommendations": recommendations,
        "source_artifacts": {
            "suite_report": str(VALIDATION / "xenalchemy_test_report.json"),
            "tcad_report": str(VALIDATION / "tcad_report.json"),
            "connectome_report": str(VALIDATION / "defect_connectome_report.json"),
            "yield_report": str(VALIDATION / "yield_report.json"),
            "void_channel_report": str(VALIDATION / "void_channel_report.json"),
            "synthetic_evidence_summary": str(SPDK_SUMMARY),
            "living_kpi_template": str(VALIDATION / "living_system_kpi_template.json"),
        },
    }

    out_path = VALIDATION / "frontier_readiness_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("[frontier_readiness] index:", f"{readiness_v2_index:.4f}")
    print("[frontier_readiness] legacy_weighted_index:", f"{legacy_weighted_index:.4f}")
    print("[frontier_readiness] hard_gate_fraction:", f"{hard_gate_fraction:.4f}")
    print("[frontier_readiness] recommendations:", len(recommendations))
    print("[frontier_readiness] report:", out_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
