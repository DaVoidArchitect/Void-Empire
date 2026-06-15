#!/usr/bin/env python3
"""Motherboard-equivalence coverage conformance checks.

Writes:
- validation/motherboard_equivalence_report.json
"""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from software.voidos.apis.gateway import VoidApiGateway
from software.voidos.kernel.capabilities import Capability

REPORT_PATH = Path(__file__).resolve().parent / "motherboard_equivalence_report.json"
MAP_PATH = ROOT / "docs" / "technical" / "VOID_MOTHERBOARD_EQUIVALENCE_MAP.md"


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


def parse_mapping_domains_and_rights(doc_text: str) -> tuple[set[str], set[str]]:
    domains: set[str] = set()
    rights: set[str] = set()

    for line in doc_text.splitlines():
        if "|" not in line:
            continue
        line_clean = line.strip()
        if not line_clean.startswith("|"):
            continue
        if line_clean.startswith("|---"):
            continue

        cols = [c.strip() for c in line_clean.strip("|").split("|")]
        if len(cols) < 4:
            continue

        dom_col = cols[-2]
        rights_col = cols[-1]

        for token in re.findall(r"[a-z][a-z_]*", dom_col.lower()):
            t = token.strip().lower()
            if t and t not in {"all", "and"}:
                domains.add(t)

        rights.update(set(re.findall(r"\b[A-Z_]{3,}\b", rights_col)))

    return domains, rights


def main() -> int:
    version = read_json(ROOT / "VERSION.json")
    checks: list[dict[str, Any]] = []

    doc_text = MAP_PATH.read_text(encoding="utf-8") if MAP_PATH.exists() else ""
    mapped_domains, mapped_rights = parse_mapping_domains_and_rights(doc_text)

    expected_domains = {
        "device",
        "power",
        "memory",
        "storage",
        "io",
        "network",
        "peripheral",
        "platform",
        "treasury",
        "quest",
        "knowledge",
        "governance",
        "legacy",
    }
    missing_domains = sorted(expected_domains - mapped_domains)

    expected_rights = {
        "DEVICE_REGISTER",
        "DEVICE_REMOVE",
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
        "TREASURY_TRANSFER",
        "QUEST_CLAIM",
        "QUEST_SUBMIT_PROOF",
        "QUEST_SETTLE",
        "KNOWLEDGE_REGISTER",
        "KNOWLEDGE_GRANT",
        "GOVERNANCE_VOTE",
        "GOVERNANCE_FINALIZE",
        "LEGACY_APPEND",
    }
    missing_rights = sorted(expected_rights - mapped_rights)

    checks.append(
        check(
            "Motherboard mapping domain completeness",
            len(missing_domains) == 0,
            "coverage map includes all required merged-chip domains",
            {
                "mapped_domain_count": len(mapped_domains),
                "missing_domains": missing_domains,
            },
        )
    )

    checks.append(
        check(
            "Motherboard mapping rights completeness",
            len(missing_rights) == 0,
            "coverage map includes all required governed rights",
            {
                "mapped_right_count": len(mapped_rights),
                "missing_rights": missing_rights,
            },
        )
    )

    gateway = VoidApiGateway()
    gateway.platform.add_route(source_domain="io", action="tick", target_domain="memory", endpoint_id="mem-lane-mb")
    gateway.platform.peripheral_register(peripheral_id="mb-per-0", initial_state={"mode": "idle"})

    broad_cap = Capability(
        cap_id="cap-motherboard-eq",
        subject_id="svc-motherboard-eq",
        rights_mask=frozenset(expected_rights),
        subnet_scope="SOV-A",
        policy_hash="policy-motherboard-eq-v1",
        expires_at=2_200_000_000,
    )

    scenarios = [
        ("device", "register", {"device_id": "mb-dev-0", "device_class": "io_hub", "metadata": {"rev": "A"}}),
        ("power", "transition", {"target_state": "BOOTSTRAP"}),
        ("memory", "write", {"address": 8, "value": 88}),
        ("storage", "write", {"block_id": 1, "payload": "mb-storage"}),
        ("io", "emit", {"endpoint_id": "uart-mb", "payload": {"byte": 66}}),
        ("network", "tx", {"payload": {"dst": "node-mb", "msg": "hello"}}),
        ("peripheral", "command", {"peripheral_id": "mb-per-0", "command": "sample", "params": {"n": 1}}),
        ("platform", "route_event", {"source_domain": "io", "route_action": "tick", "payload": {"v": 1}}),
    ]

    dispatch_results: list[dict[str, Any]] = []
    all_gateway_ok = True
    for idx, (domain, action, payload) in enumerate(scenarios, start=1):
        intent = gateway.build_intent(
            domain_id=domain,
            subnet_scope="SOV-A",
            action=action,
            payload=payload,
            signer_id="ops-mb",
            nonce=f"mb-{idx}",
        )
        out = gateway.dispatch(intent=intent, cap=broad_cap, now_epoch_s=1_900_000_000)
        item = {
            "domain": domain,
            "action": action,
            "ok": out.ok,
            "code": out.code,
            "detail": out.detail,
            "event_id": out.event_id,
        }
        dispatch_results.append(item)
        if not out.ok:
            all_gateway_ok = False

    checks.append(
        check(
            "Motherboard gateway domain smoke",
            all_gateway_ok,
            "all motherboard-equivalent gateway domain actions dispatch successfully",
            {
                "dispatch_results": dispatch_results,
            },
        )
    )

    overall_pass = all(c["pass"] for c in checks)
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

    print("[motherboard_equivalence_conformance] check_count:", payload["check_count"])
    print("[motherboard_equivalence_conformance] pass_count:", payload["pass_count"])
    print("[motherboard_equivalence_conformance] overall_pass:", payload["overall_pass"])
    print("[motherboard_equivalence_conformance] report:", REPORT_PATH)
    return 0 if overall_pass else 34


if __name__ == "__main__":
    raise SystemExit(main())
