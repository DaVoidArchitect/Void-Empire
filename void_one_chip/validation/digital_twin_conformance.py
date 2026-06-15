#!/usr/bin/env python3
"""Full-chip digital twin conformance checks.

Writes:
- validation/digital_twin_report.json
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from software.voidos.kernel.capabilities import Capability
from software.voidos.twin.digital_twin import FullChipDigitalTwin

REPORT_PATH = Path(__file__).resolve().parent / "digital_twin_report.json"


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


def run_twin_scenario() -> tuple[FullChipDigitalTwin, list[dict[str, Any]], list[Any]]:
    twin = FullChipDigitalTwin()
    cap = Capability(
        cap_id="cap-digital-twin",
        subject_id="svc-digital-twin",
        rights_mask=frozenset(
            {
                "DEVICE_REGISTER",
                "POWER_TRANSITION",
                "MEMORY_WRITE",
                "MEMORY_READ",
                "STORAGE_WRITE",
                "STORAGE_READ",
                "IO_EMIT",
                "IO_POLL",
                "NETWORK_TX",
                "NETWORK_RX",
                "PERIPHERAL_COMMAND",
                "PERIPHERAL_QUERY",
                "ROUTE_EVENT",
                "QUEST_CLAIM",
                "QUEST_SUBMIT_PROOF",
                "QUEST_SETTLE",
                "TREASURY_TRANSFER",
                "LEGACY_APPEND",
                "KNOWLEDGE_REGISTER",
                "KNOWLEDGE_GRANT",
                "GOVERNANCE_VOTE",
                "GOVERNANCE_FINALIZE",
            }
        ),
        subnet_scope="SOV-A",
        policy_hash="policy-digital-twin-v1",
        expires_at=2_200_000_000,
    )

    twin.gateway.quest.create(
        quest_id="DT-Q-1",
        issuer_id="issuer-dt",
        subnet_scope="SOV-A",
        payout_value=1000,
        proof_required=True,
    )
    twin.gateway.governance.create_proposal(
        proposal_id="DT-G-1",
        subnet_scope="SOV-A",
        title="Twin constitutional ratification",
        body_hash="dt-gov-body-1",
        created_by="council-dt",
    )
    twin.gateway.platform.peripheral_register(peripheral_id="sensor-dt", initial_state={"mode": "idle"})
    twin.gateway.platform.add_route(
        source_domain="io",
        action="sensor_tick",
        target_domain="memory",
        endpoint_id="mem-lane-dt",
    )

    scenario: list[dict[str, Any]] = [
        {
            "domain": "device",
            "subnet_scope": "SOV-A",
            "action": "register",
            "payload": {
                "device_id": "dt-mem-ctrl-0",
                "device_class": "memory_controller",
                "metadata": {"lane": "M0"},
            },
            "nonce": "dt-n-001",
        },
        {
            "domain": "power",
            "subnet_scope": "SOV-A",
            "action": "transition",
            "payload": {"target_state": "BOOTSTRAP"},
            "nonce": "dt-n-002",
        },
        {
            "domain": "power",
            "subnet_scope": "SOV-A",
            "action": "transition",
            "payload": {"target_state": "READY"},
            "nonce": "dt-n-003",
        },
        {
            "domain": "memory",
            "subnet_scope": "SOV-A",
            "action": "write",
            "payload": {"address": 42, "value": 12345},
            "nonce": "dt-n-004",
        },
        {
            "domain": "storage",
            "subnet_scope": "SOV-A",
            "action": "write",
            "payload": {"block_id": 3, "payload": "citizen-profile-blob"},
            "nonce": "dt-n-005",
        },
        {
            "domain": "io",
            "subnet_scope": "SOV-A",
            "action": "emit",
            "payload": {"endpoint_id": "uart-dt", "payload": {"byte": 65}},
            "nonce": "dt-n-006",
        },
        {
            "domain": "network",
            "subnet_scope": "SOV-A",
            "action": "tx",
            "payload": {"payload": {"dst": "mesh-a", "msg": "twin-ping"}},
            "nonce": "dt-n-007",
        },
        {
            "domain": "peripheral",
            "subnet_scope": "SOV-A",
            "action": "command",
            "payload": {
                "peripheral_id": "sensor-dt",
                "command": "calibrate",
                "params": {"level": 2},
            },
            "nonce": "dt-n-008",
        },
        {
            "domain": "platform",
            "subnet_scope": "SOV-A",
            "action": "route_event",
            "payload": {
                "source_domain": "io",
                "route_action": "sensor_tick",
                "payload": {"sample": 7},
            },
            "nonce": "dt-n-009",
        },
        {
            "domain": "quest",
            "subnet_scope": "SOV-A",
            "action": "claim",
            "payload": {"quest_id": "DT-Q-1", "subject_id": "citizen-1"},
            "nonce": "dt-n-010",
        },
        {
            "domain": "quest",
            "subnet_scope": "SOV-A",
            "action": "submit_proof",
            "payload": {
                "quest_id": "DT-Q-1",
                "proof_payload": {"artifact": "proof-dt-1"},
            },
            "nonce": "dt-n-011",
        },
        {
            "domain": "quest",
            "subnet_scope": "SOV-A",
            "action": "mark_settled",
            "payload": {"quest_id": "DT-Q-1"},
            "nonce": "dt-n-012",
        },
        {
            "domain": "treasury",
            "subnet_scope": "SOV-A",
            "action": "settle",
            "payload": {
                "src_subnet_id": 1,
                "dst_subnet_id": 2,
                "tx_value": 5000,
                "collapse_guard": False,
            },
            "nonce": "dt-n-013",
        },
        {
            "domain": "legacy",
            "subnet_scope": "SOV-A",
            "action": "append",
            "payload": {
                "subject_id": "citizen-1",
                "subnet_id": "SOV-A",
                "quest_id": "DT-Q-1",
                "impact_metrics": {"payout": 5000, "quality": 0.98},
                "evidence_hashes": ["proof-dt-1"],
                "signer_set": ["verifier-dt", "auditor-dt"],
            },
            "nonce": "dt-n-014",
        },
        {
            "domain": "knowledge",
            "subnet_scope": "SOV-A",
            "action": "register",
            "payload": {
                "artifact_id": "DT-K-1",
                "owner_id": "citizen-1",
                "license_tier": "tier-1",
                "payload_hash": "knowledge-hash-dt-1",
                "metadata": {"topic": "civic-upgrade"},
            },
            "nonce": "dt-n-015",
        },
        {
            "domain": "knowledge",
            "subnet_scope": "SOV-A",
            "action": "grant",
            "payload": {
                "artifact_id": "DT-K-1",
                "subject_id": "citizen-2",
                "requested_tier": "tier-1",
            },
            "nonce": "dt-n-016",
        },
        {
            "domain": "governance",
            "subnet_scope": "SOV-A",
            "action": "vote",
            "payload": {"proposal_id": "DT-G-1", "vote": "yes"},
            "nonce": "dt-n-017",
        },
        {
            "domain": "governance",
            "subnet_scope": "SOV-A",
            "action": "finalize",
            "payload": {"proposal_id": "DT-G-1", "minimum_yes_votes": 1},
            "nonce": "dt-n-018",
        },
    ]

    replay = twin.replay_signed_intents(scenario=scenario, cap=cap, now_epoch_s=1_900_000_000)
    return twin, scenario, replay


def main() -> int:
    version = read_json(ROOT / "VERSION.json")
    checks: list[dict[str, Any]] = []

    twin_a, scenario_a, replay_a = run_twin_scenario()
    twin_b, _, replay_b = run_twin_scenario()

    all_ok_a = all(step.ok for step in replay_a)
    all_ok_b = all(step.ok for step in replay_b)

    digest_a = twin_a.state_digest()
    digest_b = twin_b.state_digest()
    snap_a = twin_a.snapshot()
    snap_b = twin_b.snapshot()

    checks.append(
        check(
            "Digital twin replay execution",
            all_ok_a and all_ok_b,
            "all signed scenario actions commit under governed policy",
            {
                "run_a": [asdict(x) for x in replay_a],
                "run_b": [asdict(x) for x in replay_b],
            },
        )
    )

    checks.append(
        check(
            "Digital twin determinism",
            digest_a == digest_b and snap_a == snap_b,
            "re-running same scenario yields identical terminal twin state",
            {
                "digest_a": digest_a,
                "digest_b": digest_b,
            },
        )
    )

    platform = snap_a.get("platform", {}) if isinstance(snap_a.get("platform", {}), dict) else {}
    services = {
        "treasury": snap_a.get("treasury"),
        "quest": snap_a.get("quest"),
        "legacy": snap_a.get("legacy"),
        "knowledge": snap_a.get("knowledge"),
        "governance": snap_a.get("governance"),
    }
    service_presence = all(isinstance(v, dict) for v in services.values())

    checks.append(
        check(
            "Digital twin full-stack state coverage",
            isinstance(platform, dict)
            and service_presence
            and isinstance(platform.get("memory", {}), dict)
            and isinstance(platform.get("storage", {}), dict)
            and isinstance(platform.get("io", {}), dict)
            and isinstance(platform.get("network", {}), dict)
            and isinstance(platform.get("peripherals", {}), dict)
            and isinstance(platform.get("devices", {}), dict)
            and isinstance(platform.get("routing", {}), dict),
            "twin includes platform HAL/kernel + governed economy services",
            {
                "platform_keys": sorted(platform.keys()),
                "service_keys": sorted(services.keys()),
            },
        )
    )

    journal_records = (
        (((platform.get("coordinator") or {}).get("journal") or {}).get("record_count", 0))
        if isinstance(platform, dict)
        else 0
    )
    checks.append(
        check(
            "Digital twin audit-coupled projection",
            int(journal_records) > 0,
            "terminal twin state includes non-empty committed event journal chain",
            {
                "platform_journal_record_count": int(journal_records),
            },
        )
    )

    summary = {
        "scenario_step_count": len(scenario_a),
        "twin_state_digest": digest_a,
        "platform_power_state": ((platform.get("power") or {}).get("state", "UNKNOWN") if isinstance(platform, dict) else "UNKNOWN"),
        "quest_count": len((((services.get("quest") or {}).get("quests") or {}) if isinstance(services.get("quest"), dict) else {})),
    }

    overall_pass = all(item["pass"] for item in checks)
    payload = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "design_version": str(version.get("design_version", "UNKNOWN")),
        "release_id": str(version.get("release_id", "UNKNOWN")),
        "program_id": str(version.get("program_id", "UNKNOWN")),
        "check_count": len(checks),
        "pass_count": sum(1 for c in checks if c["pass"]),
        "checks": checks,
        "summary": summary,
        "overall_pass": overall_pass,
    }
    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("[digital_twin_conformance] check_count:", payload["check_count"])
    print("[digital_twin_conformance] pass_count:", payload["pass_count"])
    print("[digital_twin_conformance] overall_pass:", payload["overall_pass"])
    print("[digital_twin_conformance] report:", REPORT_PATH)
    return 0 if overall_pass else 33


if __name__ == "__main__":
    raise SystemExit(main())
