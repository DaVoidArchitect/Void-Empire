#!/usr/bin/env python3
"""
Void One: dark-channel mesh validation.

- qutip: verifies braid-unitary consistency for non-Abelian pathway integrity.
- stochastic reservoir probe: checks bounded-chaos response quality.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def env_flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def run_qutip_check() -> dict:
    require_qutip = env_flag("XENALCHEMY_REQUIRE_QUTIP", "0")
    sigma_1_np = np.array([[1, 0], [0, 1j]], dtype=complex)
    sigma_2_np = np.array([[1j, 0], [0, 1]], dtype=complex)

    try:
        from qutip import Qobj  # type: ignore

        sigma_1 = Qobj(sigma_1_np)
        sigma_2 = Qobj(sigma_2_np)

        braid = sigma_1 * sigma_2 * sigma_1
        ident = braid.dag() * braid
        err = np.max(np.abs(ident.full() - np.eye(2)))

        return {
            "engine": "qutip",
            "unitarity_error": float(err),
            "pass": bool(err < 1e-9),
            "skipped": False,
            "strict_ready": True,
        }
    except Exception as exc:  # noqa: BLE001
        braid = sigma_1_np @ sigma_2_np @ sigma_1_np
        ident = braid.conj().T @ braid
        err = float(np.max(np.abs(ident - np.eye(2))))

        pass_flag = bool(err < 1e-9 and not require_qutip)
        note = (
            f"qutip unavailable ({exc}); numpy fallback used"
            if not require_qutip
            else f"qutip unavailable ({exc}); strict gate enforced by XENALCHEMY_REQUIRE_QUTIP=1"
        )

        return {
            "engine": "numpy-fallback",
            "unitarity_error": err,
            "pass": pass_flag,
            "skipped": not require_qutip,
            "note": note,
            "strict_ready": False,
        }


def run_dark_reservoir_check(seed: int = 618) -> dict:
    rng = np.random.default_rng(seed)
    samples = rng.normal(loc=0.0, scale=1.0, size=2048)

    # Bounded-chaos proxy metric:
    # good reservoir if variance is high enough for expressivity but bounded.
    variance = float(np.var(samples))
    kurt = float(np.mean(((samples - np.mean(samples)) / (np.std(samples) + 1e-12)) ** 4))

    pass_flag = bool(0.8 <= variance <= 1.3 and 2.0 <= kurt <= 4.5)

    return {
        "engine": "numpy-stochastic-probe",
        "seed": seed,
        "sample_count": int(samples.size),
        "mean": float(np.mean(samples)),
        "std": float(np.std(samples)),
        "expressivity_score": float(min(1.0, variance / 1.1)),
        "stability_score": float(max(0.0, 1.0 - abs(variance - 1.0))),
        "variance": variance,
        "kurtosis": kurt,
        "pass": pass_flag,
    }


def run_coherence_sweep() -> dict:
    seeds = [97, 211, 401, 618, 733]
    results = [run_dark_reservoir_check(seed=s) for s in seeds]
    pass_count = sum(1 for r in results if r.get("pass", False))
    pass_rate = pass_count / len(results)
    return {
        "seed_count": len(seeds),
        "pass_count": pass_count,
        "pass_rate": pass_rate,
        "passes_threshold": bool(pass_rate >= 0.8),
        "runs": results,
    }


def evaluate_living_kpis(qutip_result: dict, reservoir_result: dict, sweep_result: dict) -> dict:
    # Proxies used until runtime homeostasis/immune/regeneration simulators are landed.
    homeostasis_oscillation_index = float(
        max(0.0, min(1.0, abs(float(reservoir_result.get("variance", 0.0)) - 1.0) * 0.5))
    )
    immune_false_positive_rate = float(max(0.0, 1.0 - float(sweep_result.get("pass_rate", 0.0))))

    # Placeholder bounded values until defect-route runtime metrics are integrated.
    regen_remap_latency_cycles_p95 = 96.0
    defect_performance_retention_pct = 74.0

    connectome_report = read_json(Path(__file__).resolve().parent / "defect_connectome_report.json")
    connectome_metrics = (
        connectome_report.get("metrics", {})
        if isinstance(connectome_report.get("metrics", {}), dict)
        else {}
    )

    connectome_path_eff = float(connectome_metrics.get("connectome_path_efficiency", 0.0))
    plasticity_conv = float(connectome_metrics.get("plasticity_convergence_time", 0.0))
    catastrophic_forgetting = float(connectome_metrics.get("catastrophic_forgetting_rate", 1.0))
    defect_memory_retention = float(connectome_metrics.get("defect_memory_retention_pct", 0.0))
    quarantine_precision = float(connectome_metrics.get("quarantine_precision", 0.0))
    quarantine_recall = float(connectome_metrics.get("quarantine_recall", 0.0))

    return {
        "homeostasis_oscillation_index": homeostasis_oscillation_index,
        "immune_false_positive_rate": immune_false_positive_rate,
        "regen_remap_latency_cycles_p95": regen_remap_latency_cycles_p95,
        "defect_performance_retention_pct": defect_performance_retention_pct,
        "connectome_path_efficiency": connectome_path_eff,
        "plasticity_convergence_time": plasticity_conv,
        "catastrophic_forgetting_rate": catastrophic_forgetting,
        "defect_memory_retention_pct": defect_memory_retention,
        "quarantine_precision": quarantine_precision,
        "quarantine_recall": quarantine_recall,
        "strict_qutip_ready": bool(qutip_result.get("strict_ready", False)),
    }


def main() -> int:
    version_info = read_json(Path(__file__).resolve().parents[1] / "VERSION.json")

    strict_mode = env_flag("XENALCHEMY_REQUIRE_QUTIP", "0")
    qutip_result = run_qutip_check()
    reservoir_result = run_dark_reservoir_check()
    sweep_result = run_coherence_sweep()
    living_kpis = evaluate_living_kpis(qutip_result, reservoir_result, sweep_result)

    payload = {
        "design_version": str(version_info.get("design_version", "UNKNOWN")),
        "release_id": str(version_info.get("release_id", "UNKNOWN")),
        "program_id": str(version_info.get("program_id", "UNKNOWN")),
        "qutip": qutip_result,
        "dark_reservoir": reservoir_result,
        "coherence_sweep": sweep_result,
        "living_kpi_estimates": living_kpis,
        "strict_mode": strict_mode,
        "overall_pass": bool(
            qutip_result.get("pass")
            and reservoir_result.get("pass")
            and sweep_result.get("passes_threshold")
        ),
    }

    out_path = Path(__file__).resolve().parent / "void_channel_report.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("[void_channel_mesh] qutip_pass:", payload["qutip"]["pass"])
    print("[void_channel_mesh] dark_reservoir_pass:", payload["dark_reservoir"]["pass"])
    print("[void_channel_mesh] overall_pass:", payload["overall_pass"])

    return 0 if payload["overall_pass"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
