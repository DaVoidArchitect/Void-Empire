#!/usr/bin/env python3
"""Phase-1 VoidOS executable conformance checks.

Validates deterministic HAL/kernel/services skeleton behavior and writes:
- validation/phase1_conformance_report.json
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

from software.voidos.apis.contracts import ApiResponse, validate_response
from software.voidos.hal.counter import MonotonicCounterAdapter
from software.voidos.hal.mailbox import MailboxDriver
from software.voidos.hal.telemetry import TelemetryAdapter
from software.voidos.kernel.capabilities import Capability, CapabilityGuard
from software.voidos.kernel.event_journal import DeterministicEventJournal
from software.voidos.kernel.scheduler import DeterministicDomainScheduler, ScheduledIntent
from software.voidos.services.legacy_service import LegacyGraphService
from software.voidos.services.quest_service import QuestService
from software.voidos.services.treasury_service import TreasurySettlementService

REPORT_PATH = Path(__file__).resolve().parent / "phase1_conformance_report.json"


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


def run_deterministic_scenario() -> dict[str, Any]:
    mailbox = MailboxDriver()
    counter = MonotonicCounterAdapter()
    scheduler = DeterministicDomainScheduler()
    journal = DeterministicEventJournal()
    treasury = TreasurySettlementService()
    quest = QuestService()
    legacy = LegacyGraphService()

    quest.create(
        quest_id="Q-001",
        issuer_id="issuer-alpha",
        subnet_scope="SOV-A",
        payout_value=10_000,
        proof_required=True,
    )

    intents = [
        ScheduledIntent(
            domain_id="quest",
            subnet_scope="SOV-A",
            monotonic_counter=counter.next(domain_id="quest", subnet_scope="SOV-A"),
            pulse_id="pulse-quest-001",
            payload={"quest_id": "Q-001", "subject_id": "executor-7"},
        ),
        ScheduledIntent(
            domain_id="treasury",
            subnet_scope="SOV-A",
            monotonic_counter=counter.next(domain_id="treasury", subnet_scope="SOV-A"),
            pulse_id="pulse-treasury-001",
            payload={
                "src_subnet_id": 3,
                "dst_subnet_id": 9,
                "tx_value": 10_000,
                "collapse_guard": False,
            },
        ),
    ]

    ordered = scheduler.order(intents)
    ordered_domains: list[str] = []
    treasury_credit_total = 0
    quest_settled = False

    for item in ordered:
        ordered_domains.append(item.domain_id)

        mbox = mailbox.submit_intent(
            {
                "pulse_id": item.pulse_id,
                "domain_id": item.domain_id,
                "subnet_scope": item.subnet_scope,
                "counter": item.monotonic_counter,
                "payload": item.payload,
            }
        )
        if not mbox.ok:
            return {
                "ok": False,
                "reason": "mailbox rejected deterministic scenario envelope",
                "code": mbox.code,
                "ordered_domains": ordered_domains,
            }

        if item.domain_id == "treasury":
            t = treasury.settle(
                src_subnet_id=item.payload["src_subnet_id"],
                dst_subnet_id=item.payload["dst_subnet_id"],
                tx_value=item.payload["tx_value"],
                collapse_guard=item.payload["collapse_guard"],
            )
            treasury_credit_total += t.treasury_credit
            payload = {
                "domain": "treasury",
                "result": asdict(t),
            }
        else:
            ok_claim, code_claim = quest.claim(
                quest_id=item.payload["quest_id"],
                subject_id=item.payload["subject_id"],
            )
            ok_proof, code_proof = quest.submit_proof(
                quest_id=item.payload["quest_id"],
                proof_payload={"artifact": "proof-hash-001"},
            )
            ok_settle, code_settle = quest.mark_settled(quest_id=item.payload["quest_id"])
            quest_settled = bool(ok_settle)

            if ok_settle:
                legacy.append_event(
                    event_id="legacy-001",
                    subject_id=item.payload["subject_id"],
                    subnet_id=item.subnet_scope,
                    quest_id=item.payload["quest_id"],
                    impact_metrics={"payout": 10_000, "quality": 1.0},
                    evidence_hashes=["proof-hash-001"],
                    signer_set=["verifier-A", "auditor-B"],
                )

            payload = {
                "domain": "quest",
                "claim": {"ok": ok_claim, "code": code_claim},
                "proof": {"ok": ok_proof, "code": code_proof},
                "settle": {"ok": ok_settle, "code": code_settle},
            }

        ok_append, code_append = journal.append(event_id=item.pulse_id, payload=payload)
        if not ok_append:
            return {
                "ok": False,
                "reason": "journal append failed in deterministic scenario",
                "code": code_append,
                "ordered_domains": ordered_domains,
            }

    return {
        "ok": True,
        "ordered_domains": ordered_domains,
        "journal_head": journal.head,
        "journal_record_count": len(journal.records),
        "legacy_event_count": len(legacy.events),
        "treasury_credit_total": treasury_credit_total,
        "quest_settled": quest_settled,
    }


def main() -> int:
    version = read_json(ROOT / "VERSION.json")
    checks: list[dict[str, Any]] = []

    # HAL: mailbox anti-replay
    mailbox = MailboxDriver()
    env = {"pulse_id": "p-1", "domain_id": "treasury", "counter": 1}
    first = mailbox.submit_intent(env)
    replay = mailbox.submit_intent(env)
    checks.append(
        check(
            "HAL mailbox anti-replay",
            first.ok and (not replay.ok) and replay.code == "E_COUNTER_REPLAY",
            "deterministic envelope replay is rejected",
            {
                "first": asdict(first),
                "replay": asdict(replay),
            },
        )
    )

    # HAL: monotonic counter
    counter = MonotonicCounterAdapter()
    a1 = counter.next(domain_id="treasury", subnet_scope="SOV-A")
    a2 = counter.next(domain_id="treasury", subnet_scope="SOV-A")
    b1 = counter.next(domain_id="quest", subnet_scope="SOV-A")
    checks.append(
        check(
            "HAL monotonic counter",
            (a1, a2, b1) == (1, 2, 1),
            "counter is monotonic per (domain, subnet)",
            {"treasury_seq": [a1, a2], "quest_seq": [b1]},
        )
    )

    # HAL: telemetry normalization
    telemetry = TelemetryAdapter().capture(
        thermal_input_milliK=3400,
        defect_density=300,
        collapse_guard=False,
    )
    checks.append(
        check(
            "HAL telemetry normalization",
            telemetry.thermal_input_milliK == 3400 and telemetry.defect_density == 255,
            "telemetry snapshot normalized to deterministic bounds",
            asdict(telemetry),
        )
    )

    # Kernel: scheduler priority + deterministic ordering
    scheduler = DeterministicDomainScheduler()
    ordered = scheduler.order(
        [
            ScheduledIntent("quest", "SOV-A", 1, "q1", {}),
            ScheduledIntent("treasury", "SOV-A", 1, "t1", {}),
            ScheduledIntent("general", "SOV-A", 1, "g1", {}),
        ]
    )
    order_domains = [x.domain_id for x in ordered]
    checks.append(
        check(
            "Kernel deterministic scheduler",
            order_domains == ["treasury", "quest", "general"],
            "priority class order is deterministic",
            {"ordered_domains": order_domains},
        )
    )

    # Kernel: capability checks
    cap_guard = CapabilityGuard()
    cap = Capability(
        cap_id="cap-1",
        subject_id="svc-treasury",
        rights_mask=frozenset({"TREASURY_TRANSFER", "QUEST_SETTLE"}),
        subnet_scope="SOV-A",
        policy_hash="policy-abc",
        expires_at=2_200_000_000,
    )
    cap_ok, cap_ok_code = cap_guard.validate(
        cap,
        required_right="TREASURY_TRANSFER",
        subnet_scope="SOV-A",
        now_epoch_s=1_900_000_000,
    )
    cap_bad_scope, cap_bad_scope_code = cap_guard.validate(
        cap,
        required_right="TREASURY_TRANSFER",
        subnet_scope="SOV-B",
        now_epoch_s=1_900_000_000,
    )
    checks.append(
        check(
            "Kernel capability guard",
            cap_ok and cap_ok_code == "OK" and (not cap_bad_scope) and cap_bad_scope_code == "E_SCOPE_VIOLATION",
            "capability validation enforces scope and rights",
            {
                "ok": {"pass": cap_ok, "code": cap_ok_code},
                "scope_violation": {"pass": cap_bad_scope, "code": cap_bad_scope_code},
            },
        )
    )

    # Kernel: journal append/rollback/replay behavior
    journal = DeterministicEventJournal()
    j1_ok, j1_code = journal.append(event_id="evt-1", payload={"k": 1})
    head_after_1 = journal.head
    j2_fail, j2_fail_code = journal.append(event_id="evt-2", payload={"k": 2}, force_fail=True)
    head_after_fail = journal.head
    j2_ok, j2_ok_code = journal.append(event_id="evt-2", payload={"k": 2})
    j2_replay, j2_replay_code = journal.append(event_id="evt-2", payload={"k": 2})
    checks.append(
        check(
            "Kernel journal rollback + replay protection",
            (
                j1_ok
                and j1_code == "OK"
                and (not j2_fail)
                and j2_fail_code == "E_AUDIT_COMMIT_FAILED"
                and head_after_fail == head_after_1
                and j2_ok
                and j2_ok_code == "OK"
                and (not j2_replay)
                and j2_replay_code == "E_COUNTER_REPLAY"
            ),
            "journal preserves atomic commit and replay safety",
            {
                "head_after_1": head_after_1,
                "head_after_fail": head_after_fail,
                "head_final": journal.head,
                "record_count": len(journal.records),
            },
        )
    )

    # Services: treasury hard-law mirror
    treasury = TreasurySettlementService()
    inter = treasury.settle(src_subnet_id=3, dst_subnet_id=9, tx_value=10_000, collapse_guard=False)
    intra = treasury.settle(src_subnet_id=3, dst_subnet_id=3, tx_value=10_000, collapse_guard=False)
    collapse = treasury.settle(src_subnet_id=3, dst_subnet_id=9, tx_value=10_000, collapse_guard=True)
    checks.append(
        check(
            "Services treasury semantics",
            (
                inter.tariff_value == 618
                and inter.lease_value == 0
                and inter.routed_value == 9382
                and inter.treasury_credit == 618
                and intra.tariff_value == 0
                and intra.lease_value == 16
                and intra.routed_value == 9984
                and intra.treasury_credit == 0
                and collapse.routed_value == 0
            ),
            "treasury service mirrors hard-law tariff/lease behavior",
            {
                "inter": asdict(inter),
                "intra": asdict(intra),
                "collapse": asdict(collapse),
            },
        )
    )

    # Services: quest lifecycle + proof-gated settlement
    quest = QuestService()
    quest.create(quest_id="QX-1", issuer_id="issuer-1", subnet_scope="SOV-A", payout_value=500)
    qc_ok, qc_code = quest.claim(quest_id="QX-1", subject_id="exec-1")
    qp_fail, qp_fail_code = quest.submit_proof(quest_id="QX-1", proof_payload={})
    qp_ok, qp_ok_code = quest.submit_proof(quest_id="QX-1", proof_payload={"proof": "hash"})
    qs_ok, qs_code = quest.mark_settled(quest_id="QX-1")
    checks.append(
        check(
            "Services quest lifecycle",
            (
                qc_ok
                and qc_code == "OK"
                and (not qp_fail)
                and qp_fail_code == "E_PROOF_INVALID"
                and qp_ok
                and qp_ok_code == "OK"
                and qs_ok
                and qs_code == "OK"
            ),
            "quest settlement requires valid proof",
            {
                "claim": {"ok": qc_ok, "code": qc_code},
                "proof_fail": {"ok": qp_fail, "code": qp_fail_code},
                "proof_ok": {"ok": qp_ok, "code": qp_ok_code},
                "settle": {"ok": qs_ok, "code": qs_code},
            },
        )
    )

    # Services: legacy append
    legacy = LegacyGraphService()
    legacy.append_event(
        event_id="L-1",
        subject_id="exec-1",
        subnet_id="SOV-A",
        quest_id="QX-1",
        impact_metrics={"payout": 500},
        evidence_hashes=["hash-1"],
        signer_set=["sig-A"],
    )
    checks.append(
        check(
            "Services legacy append",
            len(legacy.events) == 1 and legacy.events[0].quest_id == "QX-1",
            "legacy graph records provenance-linked contribution event",
            {"event_count": len(legacy.events)},
        )
    )

    # API contracts
    api_ok, api_ok_reason = validate_response(ApiResponse(ok=True, code="OK", message="ok"))
    api_bad, api_bad_reason = validate_response(ApiResponse(ok=True, code="E_CAP_INVALID", message="bad"))
    checks.append(
        check(
            "API contract validation",
            api_ok and (not api_bad) and api_ok_reason == "OK",
            "API response code semantics are enforced",
            {
                "ok_reason": api_ok_reason,
                "bad_reason": api_bad_reason,
            },
        )
    )

    # Deterministic replay scenario
    s1 = run_deterministic_scenario()
    s2 = run_deterministic_scenario()
    replay_ok = s1.get("ok") and s2.get("ok") and s1 == s2
    checks.append(
        check(
            "Deterministic replay scenario",
            bool(replay_ok),
            "identical scenario replay yields identical terminal state",
            {"run_a": s1, "run_b": s2},
        )
    )

    overall_pass = all(item["pass"] for item in checks)
    payload = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "design_version": str(version.get("design_version", "UNKNOWN")),
        "release_id": str(version.get("release_id", "UNKNOWN")),
        "program_id": str(version.get("program_id", "UNKNOWN")),
        "check_count": len(checks),
        "pass_count": sum(1 for c in checks if c["pass"]),
        "checks": checks,
        "overall_pass": overall_pass,
    }
    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("[phase1_conformance] checks:", payload["check_count"])
    print("[phase1_conformance] pass_count:", payload["pass_count"])
    print("[phase1_conformance] overall_pass:", payload["overall_pass"])
    print("[phase1_conformance] report:", REPORT_PATH)
    return 0 if overall_pass else 14


if __name__ == "__main__":
    raise SystemExit(main())
