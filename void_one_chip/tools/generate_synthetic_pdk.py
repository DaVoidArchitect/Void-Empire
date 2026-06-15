#!/usr/bin/env python3
"""
Generate a candidate Synthetic PDK package from material/physics priors.

Inputs:
- pdk/synthetic_v1/material_library.yaml
- pdk/synthetic_v1/stack_manifest.yaml
- pdk/synthetic_v1/process_envelope.yaml
- pdk/synthetic_v1/rule_deck.yaml

Outputs:
- pdk/synthetic_v1/generated/XENALCHEMY_Synthetic_Candidate_BOM.csv
- pdk/synthetic_v1/generated/synthetic_candidate_manifest.json
- pdk/synthetic_v1/generated/synthetic_evidence_summary.json
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception as exc:  # noqa: BLE001
    raise SystemExit(
        "PyYAML is required for synthetic PDK generation. "
        "Install dependencies from VoidAlchmey/validation/requirements.txt"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
SPDK_ROOT = ROOT / "pdk" / "synthetic_v1"
GENERATED = SPDK_ROOT / "generated"


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        payload = yaml.safe_load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"invalid YAML payload: {path}")
    return payload


def element_set(material: dict[str, Any]) -> set[str]:
    elems = material.get("periodic_basis", [])
    return {str(e).strip().lower() for e in elems}


def has_forbidden_elements(material: dict[str, Any]) -> list[str]:
    elems = element_set(material)
    hits: list[str] = []
    if "si" in elems or "silicon" in elems:
        hits.append("silicon")
    if "cu" in elems or "copper" in elems:
        hits.append("copper")
    return hits


def thermal_stability(material: dict[str, Any]) -> float:
    k = float(material.get("thermal_conductivity_w_mk", 0.0))
    phase = material.get("phase_stability_k", {})
    pmin = float(phase.get("min", 0.0))
    pmax = float(phase.get("max", 0.0))
    span = max(0.0, pmax - pmin)

    k_norm = clamp01(k / 2200.0)
    span_norm = clamp01(span / 4500.0)
    return clamp01((0.55 * k_norm) + (0.45 * span_norm))


def resolve_material(
    layer_spec: dict[str, Any], material_by_id: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    preferred = [str(x) for x in layer_spec.get("preferred_material_ids", [])]
    for mat_id in preferred:
        if mat_id in material_by_id:
            return material_by_id[mat_id]

    intent = str(layer_spec.get("intent", "")).strip().lower()
    for material in material_by_id.values():
        if str(material.get("class", "")).strip().lower() == intent:
            return material

    raise KeyError(
        f"No material resolved for layer={layer_spec.get('layer')} "
        f"intent={layer_spec.get('intent')} preferred={preferred}"
    )


def main() -> int:
    material_library = read_yaml(SPDK_ROOT / "material_library.yaml")
    stack_manifest = read_yaml(SPDK_ROOT / "stack_manifest.yaml")
    process_envelope = read_yaml(SPDK_ROOT / "process_envelope.yaml")
    rule_deck = read_yaml(SPDK_ROOT / "rule_deck.yaml")

    GENERATED.mkdir(parents=True, exist_ok=True)

    materials = material_library.get("materials", [])
    if not isinstance(materials, list) or not materials:
        raise ValueError("material_library.yaml has no materials")

    material_by_id: dict[str, dict[str, Any]] = {}
    for mat in materials:
        mat_id = str(mat.get("id", "")).strip()
        if not mat_id:
            continue
        material_by_id[mat_id] = mat

    layers = stack_manifest.get("layer_order", [])
    if not isinstance(layers, list) or not layers:
        raise ValueError("stack_manifest.yaml has no layer_order")

    constraints = stack_manifest.get("constitutional_constraints", {})
    hard_fail = rule_deck.get("hard_fails", {})
    scoring = rule_deck.get("scoring", {})
    weights = scoring.get("weights", {})

    selected_rows: list[dict[str, Any]] = []
    csv_rows: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []

    thermal_scores: list[float] = []
    dark_scores: list[float] = []
    defect_scores: list[float] = []

    for idx, layer in enumerate(layers, start=1):
        material = resolve_material(layer, material_by_id)
        material_id = str(material.get("id", ""))
        layer_name = str(layer.get("layer", f"L{idx}"))
        intent = str(layer.get("intent", "unknown"))
        thickness_um = float(layer.get("thickness_um_target", 0.0))

        thermal = thermal_stability(material)
        dark = float(material.get("dark_channel_affinity", 0.0))
        defect = float(material.get("defect_tolerance", 0.0))

        thermal_scores.append(thermal)
        dark_scores.append(clamp01(dark))
        defect_scores.append(clamp01(defect))

        forbidden_hits = has_forbidden_elements(material)
        if forbidden_hits:
            violations.append(
                {
                    "layer": layer_name,
                    "material_id": material_id,
                    "violations": forbidden_hits,
                }
            )

        basis = ",".join(str(x) for x in material.get("periodic_basis", []))
        notes = "; ".join(str(x) for x in material.get("tags", []))
        if layer.get("immutable_hardlaw_zone", False):
            notes = (notes + "; " if notes else "") + "immutable_hardlaw_zone"

        selected_rows.append(
            {
                "layer": layer_name,
                "intent": intent,
                "material_id": material_id,
                "material": str(material.get("display_name", material_id)),
                "thickness_um": thickness_um,
                "periodic_basis": material.get("periodic_basis", []),
                "thermal_conductivity_w_mk": float(
                    material.get("thermal_conductivity_w_mk", 0.0)
                ),
                "dark_channel_affinity": clamp01(dark),
                "defect_tolerance": clamp01(defect),
                "thermal_stability": thermal,
                "tags": material.get("tags", []),
            }
        )

        csv_rows.append(
            {
                "item_id": f"SPDK-{idx:03d}",
                "layer_symbol": f"{layer_name}_{intent}".upper(),
                "material": str(material.get("display_name", material_id)),
                "composition": basis,
                "function": intent,
                "thickness_um": f"{thickness_um:.4f}",
                "notes": notes,
                "material_id": material_id,
                "thermal_conductivity_w_mk": f"{float(material.get('thermal_conductivity_w_mk', 0.0)):.4f}",
                "dark_channel_affinity": f"{clamp01(dark):.4f}",
                "defect_tolerance": f"{clamp01(defect):.4f}",
                "thermal_stability": f"{thermal:.4f}",
            }
        )

    thermal_avg = sum(thermal_scores) / max(1, len(thermal_scores))
    dark_avg = sum(dark_scores) / max(1, len(dark_scores))
    defect_avg = sum(defect_scores) / max(1, len(defect_scores))

    constitutional_ok = len(violations) == 0
    constitutional_ok = constitutional_ok and bool(
        constraints.get("silicon_allowed", True) == hard_fail.get("silicon_allowed", False)
    )
    constitutional_ok = constitutional_ok and bool(
        constraints.get("copper_allowed", True) == hard_fail.get("copper_allowed", False)
    )
    constitutional_ok = constitutional_ok and bool(
        constraints.get("l3_treasury_mutable", True)
        == hard_fail.get("l3_treasury_mutable", False)
    )
    constitutional_ok = constitutional_ok and bool(
        constraints.get("dark_channel_required", False)
        == hard_fail.get("dark_channel_required", True)
    )

    constitutional_alignment = 1.0 if constitutional_ok else 0.0

    viability_threshold = float(scoring.get("viability_threshold", 0.70))
    viability_headroom_target = float(scoring.get("viability_headroom_target", 0.08))
    w_thermal = float(weights.get("thermal_stability", 0.30))
    w_dark = float(weights.get("dark_channel_affinity", 0.20))
    w_defect = float(weights.get("defect_tolerance", 0.20))
    w_constitution = float(weights.get("constitutional_alignment", 0.30))

    viability_score = (
        (thermal_avg * w_thermal)
        + (dark_avg * w_dark)
        + (defect_avg * w_defect)
        + (constitutional_alignment * w_constitution)
    )

    viability_score = clamp01(viability_score)
    viability_headroom = viability_score - viability_threshold
    headroom_pass = viability_headroom >= viability_headroom_target
    spdk_pass = viability_score >= viability_threshold and constitutional_ok

    profile_id = str(stack_manifest.get("profile_id", "SV-SPDK-UNKNOWN"))
    timestamp = datetime.now(timezone.utc).isoformat()

    candidate_manifest = {
        "profile_id": profile_id,
        "version": str(stack_manifest.get("version", "synthetic_v1")),
        "generated_at_utc": timestamp,
        "layers": selected_rows,
        "constitutional_constraints": constraints,
        "process_envelope": process_envelope,
    }

    evidence_summary = {
        "profile_id": profile_id,
        "generated_at_utc": timestamp,
        "source_files": {
            "material_library": str(SPDK_ROOT / "material_library.yaml"),
            "stack_manifest": str(SPDK_ROOT / "stack_manifest.yaml"),
            "process_envelope": str(SPDK_ROOT / "process_envelope.yaml"),
            "rule_deck": str(SPDK_ROOT / "rule_deck.yaml"),
        },
        "constitutional": {
            "constraints": constraints,
            "violations": violations,
            "pass": constitutional_ok,
        },
        "metrics": {
            "thermal_stability": round(thermal_avg, 6),
            "dark_channel_affinity": round(dark_avg, 6),
            "defect_tolerance": round(defect_avg, 6),
            "constitutional_alignment": round(constitutional_alignment, 6),
            "viability_score": round(viability_score, 6),
            "viability_threshold": viability_threshold,
            "viability_headroom": round(viability_headroom, 6),
            "viability_headroom_target": viability_headroom_target,
            "viability_headroom_pass": headroom_pass,
            "weights": {
                "thermal_stability": w_thermal,
                "dark_channel_affinity": w_dark,
                "defect_tolerance": w_defect,
                "constitutional_alignment": w_constitution,
            },
        },
        "living_system_policy": process_envelope.get("living_system_policy", {}),
        "kpi_targets": rule_deck.get("kpi_targets", {}),
        "layer_count": len(selected_rows),
        "pass": spdk_pass,
        "recommendations": (
            []
            if spdk_pass
            else [
                "Increase viability score via higher thermal stability or defect tolerance.",
                "Remove constitutional violations before certification runs.",
            ]
        ),
    }

    csv_path = GENERATED / "XENALCHEMY_Synthetic_Candidate_BOM.csv"
    manifest_path = GENERATED / "synthetic_candidate_manifest.json"
    summary_path = GENERATED / "synthetic_evidence_summary.json"

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "item_id",
                "layer_symbol",
                "material",
                "composition",
                "function",
                "thickness_um",
                "notes",
                "material_id",
                "thermal_conductivity_w_mk",
                "dark_channel_affinity",
                "defect_tolerance",
                "thermal_stability",
            ],
        )
        writer.writeheader()
        writer.writerows(csv_rows)

    manifest_path.write_text(json.dumps(candidate_manifest, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(evidence_summary, indent=2), encoding="utf-8")

    print("[synthetic_pdk] profile_id:", profile_id)
    print("[synthetic_pdk] layer_count:", len(selected_rows))
    print("[synthetic_pdk] viability_score:", f"{viability_score:.4f}")
    print("[synthetic_pdk] viability_headroom:", f"{viability_headroom:.4f}")
    print("[synthetic_pdk] headroom_target:", f"{viability_headroom_target:.4f}")
    print("[synthetic_pdk] threshold:", f"{viability_threshold:.4f}")
    print("[synthetic_pdk] constitutional_pass:", constitutional_ok)
    print("[synthetic_pdk] pass:", spdk_pass)
    print("[synthetic_pdk] generated:", summary_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
