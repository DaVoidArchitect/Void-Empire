#!/usr/bin/env python3
"""Long-horizon ecosystem economics conformance.

Runs deterministic multi-eon citizen economy simulations on governed services and writes:
- validation/ecosystem_eons_report.json
- validation/citizen_livability_report.json
"""

from __future__ import annotations

import json
import math
import random
import statistics
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from software.voidos.apis.gateway import VoidApiGateway
from software.voidos.kernel.capabilities import Capability

REPORT_PATH = Path(__file__).resolve().parent / "ecosystem_eons_report.json"
LIVABILITY_PATH = Path(__file__).resolve().parent / "citizen_livability_report.json"


@dataclass(frozen=True)
class ScenarioConfig:
    name: str
    seed: int
    eon_count: int
    cycles_per_eon: int
    payout_scale: float
    living_cost_scale: float
    participation_rate: float
    shock_cycles: tuple[int, ...]
    fraud_probe_interval: int


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def check(name: str, ok: bool, detail: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "pass": bool(ok),
        "detail": detail,
        "evidence": evidence or {},
    }


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(v) for v in values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (float(p) / 100.0)
    lo = int(math.floor(rank))
    hi = int(math.ceil(rank))
    if lo == hi:
        return ordered[lo]
    w_hi = rank - lo
    w_lo = 1.0 - w_hi
    return (ordered[lo] * w_lo) + (ordered[hi] * w_hi)


def gini(values: list[float]) -> float:
    if not values:
        return 0.0
    v = [float(x) for x in values]
    min_v = min(v)
    if min_v <= 0:
        shift = abs(min_v) + 1e-9
        v = [x + shift for x in v]
    ordered = sorted(v)
    n = len(ordered)
    total = sum(ordered)
    if total <= 0:
        return 0.0
    weighted_sum = sum((idx + 1) * val for idx, val in enumerate(ordered))
    return float((2 * weighted_sum) / (n * total) - (n + 1) / n)


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


def build_capability() -> Capability:
    return Capability(
        cap_id="cap-ecosystem-eons",
        subject_id="svc-ecosystem-eons",
        rights_mask=frozenset(
            {
                "TREASURY_TRANSFER",
                "QUEST_CLAIM",
                "QUEST_SUBMIT_PROOF",
                "QUEST_SETTLE",
                "LEGACY_APPEND",
                "KNOWLEDGE_REGISTER",
                "KNOWLEDGE_GRANT",
                "GOVERNANCE_VOTE",
                "GOVERNANCE_FINALIZE",
            }
        ),
        subnet_scope="SOV-A",
        policy_hash="policy-ecosystem-eons-v1",
        expires_at=2_200_000_000,
    )


def simulate_scenario(config: ScenarioConfig) -> dict[str, Any]:
    rng = random.Random(int(config.seed))
    gateway = VoidApiGateway()
    cap = build_capability()
    now_epoch = 1_900_000_000
    nonce_counter = 0

    citizen_count = 36
    citizens: list[dict[str, Any]] = []
    for idx in range(citizen_count):
        citizens.append(
            {
                "id": f"citizen-{idx:03d}",
                "wallet": float(rng.uniform(920.0, 1080.0)),
                "skill": float(rng.uniform(0.85, 1.25)),
                "trust": 1.0,
            }
        )

    def dispatch(domain: str, action: str, payload: dict[str, Any]) -> Any:
        nonlocal nonce_counter
        nonce_counter += 1
        intent = gateway.build_intent(
            domain_id=str(domain),
            subnet_scope="SOV-A",
            action=str(action),
            payload=dict(payload),
            signer_id="ecosim-operator",
            nonce=f"{config.name}-n-{nonce_counter}",
        )
        return gateway.dispatch(intent=intent, cap=cap, now_epoch_s=now_epoch)

    treasury_reserve = 400_000.0
    living_cost_base = 8.0 * float(config.living_cost_scale)
    quest_base_value = 30.0 * float(config.payout_scale)
    living_cost_multiplier = 1.0

    livability_series: list[float] = []
    insolvency_series: list[float] = []
    gini_series: list[float] = []
    reserve_series: list[float] = []

    total_governed_ops = 0
    failed_governed_ops = 0
    governance_rounds = 0
    governance_success = 0
    fraud_probe_attempts = 0
    fraud_probe_blocked = 0

    total_cycles = int(config.eon_count) * int(config.cycles_per_eon)
    for cycle in range(1, total_cycles + 1):
        if cycle in set(config.shock_cycles):
            living_cost_multiplier *= 1.07
            quest_base_value *= 0.97
            treasury_reserve *= 0.992

        living_cost_multiplier = clamp(living_cost_multiplier, 0.75, 1.45)
        quest_base_value = clamp(quest_base_value, 18.0, 60.0)

        cycle_cost = living_cost_base * living_cost_multiplier
        for c in citizens:
            c["wallet"] = float(c["wallet"]) - cycle_cost

        # Quest economy flow: assign quests to lower-wallet active citizens first.
        active = [c for c in citizens if float(c["wallet"]) > -260.0 and rng.random() < float(config.participation_rate)]
        active_sorted = sorted(active, key=lambda x: (float(x["wallet"]), str(x["id"])))
        quest_slots = max(1, int(len(citizens) * float(config.participation_rate) * 0.35))
        selected = active_sorted[:quest_slots]

        for q_idx, citizen in enumerate(selected, start=1):
            citizen_id = str(citizen["id"])
            quest_id = f"{config.name}-Q-{cycle:04d}-{q_idx:03d}"

            gateway.quest.create(
                quest_id=quest_id,
                issuer_id="ecosystem-civic-pool",
                subnet_scope="SOV-A",
                payout_value=int(quest_base_value),
                proof_required=True,
            )

            claim = dispatch("quest", "claim", {"quest_id": quest_id, "subject_id": citizen_id})
            total_governed_ops += 1
            if not claim.ok:
                failed_governed_ops += 1

            proof = dispatch(
                "quest",
                "submit_proof",
                {
                    "quest_id": quest_id,
                    "proof_payload": {"artifact": f"proof-{quest_id}"},
                },
            )
            total_governed_ops += 1
            if not proof.ok:
                failed_governed_ops += 1

            settle = dispatch("quest", "mark_settled", {"quest_id": quest_id})
            total_governed_ops += 1
            if not settle.ok:
                failed_governed_ops += 1

            if claim.ok and proof.ok and settle.ok:
                tx_value = int(quest_base_value * float(citizen["skill"]) * rng.uniform(0.92, 1.08))
                inter = (cycle % 9) == 0
                src_subnet = 1
                dst_subnet = 2 if inter else 1

                tr = dispatch(
                    "treasury",
                    "settle",
                    {
                        "src_subnet_id": src_subnet,
                        "dst_subnet_id": dst_subnet,
                        "tx_value": tx_value,
                        "collapse_guard": False,
                    },
                )
                total_governed_ops += 1
                if not tr.ok:
                    failed_governed_ops += 1

                settlement = gateway.treasury.settle(
                    src_subnet_id=src_subnet,
                    dst_subnet_id=dst_subnet,
                    tx_value=tx_value,
                    collapse_guard=False,
                )
                payout = float(settlement.routed_value)
                treasury_reserve -= payout
                treasury_reserve += float(settlement.treasury_credit + settlement.lease_value)
                treasury_reserve += float(int(tx_value * 0.30))
                citizen["wallet"] = float(citizen["wallet"]) + payout

                lg = dispatch(
                    "legacy",
                    "append",
                    {
                        "subject_id": citizen_id,
                        "subnet_id": "SOV-A",
                        "quest_id": quest_id,
                        "impact_metrics": {
                            "payout": int(payout),
                            "quality": round(rng.uniform(0.94, 1.0), 4),
                        },
                        "evidence_hashes": [f"proof-{quest_id}"],
                        "signer_set": ["verifier-civic", "auditor-civic"],
                    },
                )
                total_governed_ops += 1
                if not lg.ok:
                    failed_governed_ops += 1

        # Knowledge economy micro-cycle.
        if cycle % 12 == 0:
            owner = max(citizens, key=lambda x: float(x["skill"]))
            owner_id = str(owner["id"])
            artifact_id = f"{config.name}-K-{cycle:04d}"
            reg = dispatch(
                "knowledge",
                "register",
                {
                    "artifact_id": artifact_id,
                    "owner_id": owner_id,
                    "license_tier": "tier-1",
                    "payload_hash": f"kh-{artifact_id}",
                    "metadata": {"class": "civic-knowledge"},
                },
            )
            total_governed_ops += 1
            if not reg.ok:
                failed_governed_ops += 1

            grantee_ids = [
                str(c["id"])
                for c in sorted(citizens, key=lambda x: (float(x["wallet"]), str(x["id"])))[:3]
            ]
            for gid in grantee_ids:
                grant = dispatch(
                    "knowledge",
                    "grant",
                    {
                        "artifact_id": artifact_id,
                        "subject_id": gid,
                        "requested_tier": "tier-1",
                    },
                )
                total_governed_ops += 1
                if not grant.ok:
                    failed_governed_ops += 1
                else:
                    royalty = 6.0
                    owner["wallet"] = float(owner["wallet"]) + royalty
                    treasury_reserve -= royalty

        # Governance adaptation at eon boundaries.
        if cycle % int(config.cycles_per_eon) == 0:
            governance_rounds += 1
            recent = livability_series[-8:] if livability_series else [1.0]
            recent_livable = float(statistics.fmean(recent))

            proposal_id = f"{config.name}-G-{cycle:04d}"
            gateway.governance.create_proposal(
                proposal_id=proposal_id,
                subnet_scope="SOV-A",
                title=f"Eon policy adjustment {cycle}",
                body_hash=f"body-{proposal_id}",
                created_by="council-eon",
            )

            vote = dispatch("governance", "vote", {"proposal_id": proposal_id, "vote": "yes"})
            total_governed_ops += 1
            if not vote.ok:
                failed_governed_ops += 1

            fin = dispatch(
                "governance",
                "finalize",
                {"proposal_id": proposal_id, "minimum_yes_votes": 1},
            )
            total_governed_ops += 1
            if not fin.ok:
                failed_governed_ops += 1

            if vote.ok and fin.ok:
                governance_success += 1
                if recent_livable < 0.93:
                    living_cost_multiplier *= 0.97
                    quest_base_value *= 1.02
                elif recent_livable > 0.985:
                    living_cost_multiplier *= 1.004
                    quest_base_value *= 0.995

        # Fraud replay probes.
        if int(config.fraud_probe_interval) > 0 and cycle % int(config.fraud_probe_interval) == 0:
            fraud_probe_attempts += 1
            intent = gateway.build_intent(
                domain_id="treasury",
                subnet_scope="SOV-A",
                action="settle",
                payload={
                    "src_subnet_id": 1,
                    "dst_subnet_id": 1,
                    "tx_value": 0,
                    "collapse_guard": True,
                },
                signer_id="fraud-probe",
                nonce=f"{config.name}-fraud-{cycle}",
            )
            first = gateway.dispatch(intent=intent, cap=cap, now_epoch_s=now_epoch)
            second = gateway.dispatch(intent=intent, cap=cap, now_epoch_s=now_epoch)

            total_governed_ops += 2
            if not first.ok:
                failed_governed_ops += 1
            if second.ok:
                failed_governed_ops += 1
            if (not second.ok) and second.code == "E_COUNTER_REPLAY":
                fraud_probe_blocked += 1

        # Cycle-level metrics.
        wallets = [float(c["wallet"]) for c in citizens]
        livable_ratio = sum(1 for w in wallets if w >= 0.0) / len(wallets)
        insolvency_ratio = sum(1 for w in wallets if w < 0.0) / len(wallets)

        livability_series.append(float(livable_ratio))
        insolvency_series.append(float(insolvency_ratio))
        gini_series.append(gini(wallets))
        reserve_series.append(float(treasury_reserve))

    avg_livable = float(statistics.fmean(livability_series)) if livability_series else 0.0
    min_livable = float(min(livability_series)) if livability_series else 0.0
    max_insolvency = float(max(insolvency_series)) if insolvency_series else 1.0
    gini_p95 = float(percentile(gini_series, 95.0)) if gini_series else 1.0

    reserve_final = float(reserve_series[-1]) if reserve_series else 0.0
    reserve_floor = float(min(reserve_series)) if reserve_series else 0.0
    reserve_adequacy_ratio = reserve_final / (len(citizens) * living_cost_base * 30.0)

    op_success_rate = 1.0
    if total_governed_ops > 0:
        op_success_rate = (total_governed_ops - failed_governed_ops) / total_governed_ops
    gov_success_rate = 1.0 if governance_rounds == 0 else governance_success / governance_rounds
    fraud_block_rate = 1.0 if fraud_probe_attempts == 0 else fraud_probe_blocked / fraud_probe_attempts

    stability_index = clamp(
        0.30 * avg_livable
        + 0.20 * (1.0 - max_insolvency)
        + 0.15 * (1.0 - clamp(gini_p95, 0.0, 1.0))
        + 0.15 * clamp(reserve_adequacy_ratio, 0.0, 1.0)
        + 0.10 * op_success_rate
        + 0.10 * gov_success_rate,
        0.0,
        1.0,
    )

    scenario_pass = bool(
        avg_livable >= 0.90
        and min_livable >= 0.78
        and max_insolvency <= 0.22
        and gini_p95 <= 0.55
        and reserve_adequacy_ratio >= 0.25
        and op_success_rate >= 0.995
        and gov_success_rate >= 0.99
        and fraud_block_rate >= 0.99
        and stability_index >= 0.82
    )

    return {
        "scenario": config.name,
        "seed": int(config.seed),
        "eon_count": int(config.eon_count),
        "cycles_per_eon": int(config.cycles_per_eon),
        "total_cycles": int(total_cycles),
        "citizen_count": len(citizens),
        "metrics": {
            "avg_livable_ratio": round(avg_livable, 6),
            "min_livable_ratio": round(min_livable, 6),
            "max_insolvency_ratio": round(max_insolvency, 6),
            "gini_p95": round(gini_p95, 6),
            "reserve_final": round(reserve_final, 3),
            "reserve_floor": round(reserve_floor, 3),
            "reserve_adequacy_ratio": round(reserve_adequacy_ratio, 6),
            "governed_op_success_rate": round(op_success_rate, 6),
            "governance_success_rate": round(gov_success_rate, 6),
            "fraud_probe_block_rate": round(fraud_block_rate, 6),
            "stability_index": round(stability_index, 6),
        },
        "ops": {
            "total_governed_ops": int(total_governed_ops),
            "failed_governed_ops": int(failed_governed_ops),
            "governance_rounds": int(governance_rounds),
            "governance_success": int(governance_success),
            "fraud_probe_attempts": int(fraud_probe_attempts),
            "fraud_probe_blocked": int(fraud_probe_blocked),
        },
        "series_samples": {
            "livability_first5": [round(x, 6) for x in livability_series[:5]],
            "livability_last5": [round(x, 6) for x in livability_series[-5:]],
            "insolvency_last5": [round(x, 6) for x in insolvency_series[-5:]],
        },
        "scenario_pass": scenario_pass,
    }


def main() -> int:
    version = read_json(ROOT / "VERSION.json")
    checks: list[dict[str, Any]] = []

    scenarios = [
        ScenarioConfig(
            name="baseline",
            seed=101,
            eon_count=12,
            cycles_per_eon=15,
            payout_scale=1.0,
            living_cost_scale=1.0,
            participation_rate=0.92,
            shock_cycles=(),
            fraud_probe_interval=30,
        ),
        ScenarioConfig(
            name="resource_shock",
            seed=202,
            eon_count=12,
            cycles_per_eon=15,
            payout_scale=0.98,
            living_cost_scale=1.07,
            participation_rate=0.88,
            shock_cycles=(45, 90, 135),
            fraud_probe_interval=25,
        ),
        ScenarioConfig(
            name="participation_shock",
            seed=303,
            eon_count=12,
            cycles_per_eon=15,
            payout_scale=1.02,
            living_cost_scale=1.03,
            participation_rate=0.82,
            shock_cycles=(60, 120),
            fraud_probe_interval=20,
        ),
    ]

    results = [simulate_scenario(cfg) for cfg in scenarios]

    scenario_passes = [bool(r.get("scenario_pass", False)) for r in results]
    min_livable_global = min(float(r["metrics"]["min_livable_ratio"]) for r in results)
    avg_livable_global = float(statistics.fmean(float(r["metrics"]["avg_livable_ratio"]) for r in results))
    max_insolvency_global = max(float(r["metrics"]["max_insolvency_ratio"]) for r in results)
    min_stability_global = min(float(r["metrics"]["stability_index"]) for r in results)
    min_op_success = min(float(r["metrics"]["governed_op_success_rate"]) for r in results)
    min_fraud_block = min(float(r["metrics"]["fraud_probe_block_rate"]) for r in results)

    checks.append(
        check(
            "Ecosystem multi-scenario execution",
            all(scenario_passes),
            "all deterministic eon scenarios satisfy livability and stability thresholds",
            {
                "scenario_passes": {
                    str(r["scenario"]): bool(r["scenario_pass"])
                    for r in results
                }
            },
        )
    )

    checks.append(
        check(
            "Citizen livability floor",
            avg_livable_global >= 0.90 and min_livable_global >= 0.78 and max_insolvency_global <= 0.22,
            "citizen living outcomes remain viable across eon horizons",
            {
                "avg_livable_global": round(avg_livable_global, 6),
                "min_livable_global": round(min_livable_global, 6),
                "max_insolvency_global": round(max_insolvency_global, 6),
            },
        )
    )

    checks.append(
        check(
            "Economic stability index",
            min_stability_global >= 0.82,
            "worst-case scenario remains above minimum stability index",
            {
                "min_stability_index": round(min_stability_global, 6),
            },
        )
    )

    checks.append(
        check(
            "Anti-abuse and governance resilience",
            min_op_success >= 0.995 and min_fraud_block >= 0.99,
            "governed operations remain reliable and replay abuse is blocked",
            {
                "min_governed_op_success_rate": round(min_op_success, 6),
                "min_fraud_block_rate": round(min_fraud_block, 6),
            },
        )
    )

    livability_payload = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "design_version": str(version.get("design_version", "UNKNOWN")),
        "release_id": str(version.get("release_id", "UNKNOWN")),
        "program_id": str(version.get("program_id", "UNKNOWN")),
        "thresholds": {
            "avg_livable_ratio_min": 0.90,
            "min_livable_ratio_min": 0.78,
            "max_insolvency_ratio_max": 0.22,
            "stability_index_min": 0.82,
        },
        "scenario_metrics": [
            {
                "scenario": r["scenario"],
                "metrics": dict(r["metrics"]),
                "scenario_pass": bool(r["scenario_pass"]),
            }
            for r in results
        ],
        "overall_livability_pass": bool(avg_livable_global >= 0.90 and min_livable_global >= 0.78),
    }
    LIVABILITY_PATH.write_text(json.dumps(livability_payload, indent=2), encoding="utf-8")

    overall_pass = all(item["pass"] for item in checks)
    payload = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "design_version": str(version.get("design_version", "UNKNOWN")),
        "release_id": str(version.get("release_id", "UNKNOWN")),
        "program_id": str(version.get("program_id", "UNKNOWN")),
        "scenario_count": len(results),
        "check_count": len(checks),
        "pass_count": sum(1 for c in checks if c["pass"]),
        "checks": checks,
        "scenario_results": results,
        "livability_report": str(LIVABILITY_PATH),
        "overall_pass": overall_pass,
    }
    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("[ecosystem_eons_conformance] scenario_count:", payload["scenario_count"])
    print("[ecosystem_eons_conformance] check_count:", payload["check_count"])
    print("[ecosystem_eons_conformance] pass_count:", payload["pass_count"])
    print("[ecosystem_eons_conformance] overall_pass:", payload["overall_pass"])
    print("[ecosystem_eons_conformance] report:", REPORT_PATH)
    print("[ecosystem_eons_conformance] livability_report:", LIVABILITY_PATH)
    return 0 if overall_pass else 35


if __name__ == "__main__":
    raise SystemExit(main())
