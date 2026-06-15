#!/usr/bin/env python3
"""Motherboard-equivalent platform conformance checks.

Writes:
- validation/platform_board_conformance_report.json
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
from software.voidos.apis.gateway import VoidApiGateway
from software.voidos.kernel.capabilities import Capability
from software.voidos.services.platform_service import PlatformBoardService


REPORT_PATH = Path(__file__).resolve().parent / "platform_board_conformance_report.json"


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


def main() -> int:
    version = read_json(ROOT / "VERSION.json")
    now_epoch = 1_900_000_000
    checks: list[dict[str, Any]] = []

    rights = frozenset(
        {
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
        }
    )
    cap = Capability(
        cap_id="cap-platform-board",
        subject_id="svc-platform",
        rights_mask=rights,
        subnet_scope="SOV-A",
        policy_hash="policy-board-v1",
        expires_at=2_200_000_000,
    )

    platform = PlatformBoardService()

    # 1) Device registry governance.
    d_reg = platform.register_device_governed(
        event_id="pb-device-reg-1",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        device_id="dev-memory-ctrl-0",
        device_class="memory_controller",
        metadata={"lane": "M0"},
    )
    d_dup = platform.register_device_governed(
        event_id="pb-device-reg-dup",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        device_id="dev-memory-ctrl-0",
        device_class="memory_controller",
        metadata={"lane": "M0"},
    )
    d_remove = platform.remove_device_governed(
        event_id="pb-device-remove-1",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        device_id="dev-memory-ctrl-0",
    )
    d_remove_missing = platform.remove_device_governed(
        event_id="pb-device-remove-missing",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        device_id="dev-memory-ctrl-0",
    )
    checks.append(
        check(
            "Platform device registry governance",
            (
                d_reg.ok
                and d_reg.code == "OK"
                and (not d_dup.ok)
                and d_dup.code == "E_LEDGER_CONFLICT"
                and d_remove.ok
                and d_remove.code == "OK"
                and (not d_remove_missing.ok)
                and d_remove_missing.code == "E_POLICY_BLOCKED"
            ),
            "device registration/removal is governed and conflict-safe",
            {
                "register": asdict(d_reg),
                "duplicate": asdict(d_dup),
                "remove": asdict(d_remove),
                "remove_missing": asdict(d_remove_missing),
            },
        )
    )

    # 2) Boot-power legal transitions.
    p_bootstrap = platform.transition_power_governed(
        event_id="pb-power-bootstrap",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        target_state="BOOTSTRAP",
    )
    p_ready = platform.transition_power_governed(
        event_id="pb-power-ready",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        target_state="READY",
    )
    p_illegal = platform.transition_power_governed(
        event_id="pb-power-illegal",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        target_state="BOOTSTRAP",
    )
    state_before_fail = platform.power.state
    p_audit_fail = platform.transition_power_governed(
        event_id="pb-power-audit-fail",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        target_state="DEGRADED",
        force_audit_fail=True,
    )
    state_after_fail = platform.power.state
    p_degraded = platform.transition_power_governed(
        event_id="pb-power-degraded",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        target_state="DEGRADED",
    )
    checks.append(
        check(
            "Platform boot/power transition governance",
            (
                p_bootstrap.ok
                and p_ready.ok
                and (not p_illegal.ok)
                and p_illegal.code == "E_POLICY_BLOCKED"
                and (not p_audit_fail.ok)
                and p_audit_fail.code == "E_AUDIT_COMMIT_FAILED"
                and state_before_fail == state_after_fail
                and p_degraded.ok
                and platform.power.state == "DEGRADED"
            ),
            "power transitions are legal-state constrained and audit-coupled",
            {
                "bootstrap": asdict(p_bootstrap),
                "ready": asdict(p_ready),
                "illegal": asdict(p_illegal),
                "audit_fail": asdict(p_audit_fail),
                "degraded": asdict(p_degraded),
                "history": platform.power.history,
            },
        )
    )

    # 3) Memory governance.
    m_write = platform.memory_write_governed(
        event_id="pb-mem-write-1",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        address=5,
        value=0x1234,
    )
    m_read = platform.memory_read_governed(
        event_id="pb-mem-read-1",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        address=5,
    )
    m_range_fail = platform.memory_write_governed(
        event_id="pb-mem-range-fail",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        address=999999,
        value=1,
    )
    m_audit_fail = platform.memory_write_governed(
        event_id="pb-mem-audit-fail",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        address=6,
        value=0xAAAA,
        force_audit_fail=True,
    )
    m_read_6 = platform.memory_read_governed(
        event_id="pb-mem-read-6",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        address=6,
    )
    checks.append(
        check(
            "Platform memory governance",
            (
                m_write.ok
                and m_read.ok
                and int((m_read.data or {}).get("value", -1)) == 0x1234
                and (not m_range_fail.ok)
                and m_range_fail.code == "E_POLICY_BLOCKED"
                and (not m_audit_fail.ok)
                and m_audit_fail.code == "E_AUDIT_COMMIT_FAILED"
                and m_read_6.ok
                and int((m_read_6.data or {}).get("value", -1)) == 0
            ),
            "memory fabric reads/writes are bounded and audit-gated",
            {
                "write": asdict(m_write),
                "read": asdict(m_read),
                "range_fail": asdict(m_range_fail),
                "audit_fail": asdict(m_audit_fail),
                "read_after_fail": asdict(m_read_6),
            },
        )
    )

    # 4) Storage governance.
    s_write = platform.storage_write_governed(
        event_id="pb-storage-write-1",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        block_id=2,
        payload="blob-001",
    )
    s_read = platform.storage_read_governed(
        event_id="pb-storage-read-1",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        block_id=2,
    )
    s_range_fail = platform.storage_read_governed(
        event_id="pb-storage-range-fail",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        block_id=999999,
    )
    s_audit_fail = platform.storage_write_governed(
        event_id="pb-storage-audit-fail",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        block_id=3,
        payload="blocked",
        force_audit_fail=True,
    )
    s_read_3 = platform.storage_read_governed(
        event_id="pb-storage-read-3",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        block_id=3,
    )
    checks.append(
        check(
            "Platform storage governance",
            (
                s_write.ok
                and s_read.ok
                and str((s_read.data or {}).get("payload", "")) == "blob-001"
                and (not s_range_fail.ok)
                and s_range_fail.code == "E_POLICY_BLOCKED"
                and (not s_audit_fail.ok)
                and s_audit_fail.code == "E_AUDIT_COMMIT_FAILED"
                and s_read_3.ok
                and str((s_read_3.data or {}).get("payload", "")) == ""
            ),
            "storage bridge enforces block bounds and audit-coupled updates",
            {
                "write": asdict(s_write),
                "read": asdict(s_read),
                "range_fail": asdict(s_range_fail),
                "audit_fail": asdict(s_audit_fail),
                "read_after_fail": asdict(s_read_3),
            },
        )
    )

    # 5) I/O governance.
    io_emit = platform.io_emit_governed(
        event_id="pb-io-emit-1",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        endpoint_id="uart0",
        payload={"byte": 65},
    )
    io_poll = platform.io_poll_governed(
        event_id="pb-io-poll-1",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        endpoint_id="uart0",
    )
    io_poll_empty = platform.io_poll_governed(
        event_id="pb-io-poll-empty",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        endpoint_id="uart0",
    )
    checks.append(
        check(
            "Platform I/O bus governance",
            (
                io_emit.ok
                and io_poll.ok
                and int(((io_poll.data or {}).get("payload") or {}).get("byte", -1)) == 65
                and (not io_poll_empty.ok)
                and io_poll_empty.code == "E_POLICY_BLOCKED"
            ),
            "I/O endpoint emits/polls are deterministic and bounded",
            {
                "emit": asdict(io_emit),
                "poll": asdict(io_poll),
                "poll_empty": asdict(io_poll_empty),
            },
        )
    )

    # 6) Network governance.
    net_tx = platform.network_tx_governed(
        event_id="pb-net-tx-1",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        payload={"dst": "node-a", "msg": "hello"},
    )
    net_tx_dup = platform.network_tx_governed(
        event_id="pb-net-tx-dup",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        payload={"dst": "node-a", "msg": "hello"},
    )
    net_rx = platform.network_rx_governed(
        event_id="pb-net-rx-1",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
    )
    net_rx_empty = platform.network_rx_governed(
        event_id="pb-net-rx-empty",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
    )
    checks.append(
        check(
            "Platform network governance",
            (
                net_tx.ok
                and (not net_tx_dup.ok)
                and net_tx_dup.code == "E_COUNTER_REPLAY"
                and net_rx.ok
                and str(((net_rx.data or {}).get("payload") or {}).get("msg", "")) == "hello"
                and (not net_rx_empty.ok)
                and net_rx_empty.code == "E_POLICY_BLOCKED"
            ),
            "network tx/rx is duplicate-safe and deterministic",
            {
                "tx": asdict(net_tx),
                "tx_dup": asdict(net_tx_dup),
                "rx": asdict(net_rx),
                "rx_empty": asdict(net_rx_empty),
            },
        )
    )

    # 7) Peripheral governance.
    platform.peripheral_register(peripheral_id="sensor-0", initial_state={"mode": "idle"})
    per_cmd = platform.peripheral_command_governed(
        event_id="pb-per-cmd-1",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        peripheral_id="sensor-0",
        command="calibrate",
        params={"level": 2},
    )
    per_query = platform.peripheral_query_governed(
        event_id="pb-per-query-1",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        peripheral_id="sensor-0",
    )
    per_unknown = platform.peripheral_query_governed(
        event_id="pb-per-query-unknown",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        peripheral_id="sensor-404",
    )
    checks.append(
        check(
            "Platform peripheral governance",
            (
                per_cmd.ok
                and per_query.ok
                and int(((per_query.data or {}).get("state") or {}).get("command_count", 0)) == 1
                and (not per_unknown.ok)
                and per_unknown.code == "E_POLICY_BLOCKED"
            ),
            "peripheral commands/queries are governed and stateful",
            {
                "command": asdict(per_cmd),
                "query": asdict(per_query),
                "query_unknown": asdict(per_unknown),
            },
        )
    )

    # 8) Event routing + deterministic ordering.
    platform.add_route(source_domain="io", action="sensor_tick", target_domain="memory", endpoint_id="mem-lane-0")
    platform.add_route(
        source_domain="network",
        action="ingress_packet",
        target_domain="storage",
        endpoint_id="ssd-lane-0",
    )
    route1 = platform.route_event_governed(
        event_id="pb-route-1",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        source_domain="io",
        action="sensor_tick",
        payload={"sample": 12},
    )
    route2 = platform.route_event_governed(
        event_id="pb-route-2",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        source_domain="network",
        action="ingress_packet",
        payload={"bytes": 128},
    )
    route_missing = platform.route_event_governed(
        event_id="pb-route-missing",
        cap=cap,
        now_epoch_s=now_epoch,
        subnet_scope="SOV-A",
        source_domain="io",
        action="unknown_action",
        payload={},
    )
    ok_a, _, routed_a = platform.router.route(
        event_id="pb-order-a",
        source_domain="network",
        action="ingress_packet",
        payload={"bytes": 1},
    )
    ok_b, _, routed_b = platform.router.route(
        event_id="pb-order-b",
        source_domain="io",
        action="sensor_tick",
        payload={"sample": 1},
    )
    ordered_targets: list[str] = []
    if ok_a and ok_b and routed_a is not None and routed_b is not None:
        ordered = platform.order_routed_events(
            subnet_scope="SOV-A",
            routed_events=[routed_a, routed_b],
        )
        ordered_targets = [ev.target_domain for ev in ordered]

    checks.append(
        check(
            "Platform event routing determinism",
            (
                route1.ok
                and route2.ok
                and (not route_missing.ok)
                and route_missing.code == "E_POLICY_BLOCKED"
                and ordered_targets == ["memory", "storage"]
            ),
            "board routing resolves legal routes and preserves deterministic dispatch ordering",
            {
                "route1": asdict(route1),
                "route2": asdict(route2),
                "route_missing": asdict(route_missing),
                "ordered_targets": ordered_targets,
            },
        )
    )

    # 9) API contract extension for board errors.
    api_ok, api_reason = validate_response(ApiResponse(ok=False, code="E_DEVICE_NOT_FOUND", message="missing"))
    checks.append(
        check(
            "API contract board error code",
            api_ok and api_reason == "OK",
            "board-level API error codes are accepted by contract validator",
            {
                "api_ok": api_ok,
                "api_reason": api_reason,
            },
        )
    )

    # 10) Gateway board-domain dispatch.
    gateway = VoidApiGateway()
    gateway.platform.add_route(source_domain="io", action="tick", target_domain="memory", endpoint_id="mem-lane-gw")

    gateway_cap = Capability(
        cap_id="cap-gateway-board",
        subject_id="svc-gateway",
        rights_mask=rights,
        subnet_scope="SOV-A",
        policy_hash="policy-gateway-board",
        expires_at=2_200_000_000,
    )

    gi_device = gateway.build_intent(
        domain_id="device",
        subnet_scope="SOV-A",
        action="register",
        payload={"device_id": "gw-dev-1", "device_class": "io_hub", "metadata": {"rev": "A"}},
        signer_id="ops-gateway",
        nonce="pbg-1",
    )
    gr_device = gateway.dispatch(intent=gi_device, cap=gateway_cap, now_epoch_s=now_epoch)

    gi_power = gateway.build_intent(
        domain_id="power",
        subnet_scope="SOV-A",
        action="transition",
        payload={"target_state": "BOOTSTRAP"},
        signer_id="ops-gateway",
        nonce="pbg-2",
    )
    gr_power = gateway.dispatch(intent=gi_power, cap=gateway_cap, now_epoch_s=now_epoch)

    gi_mem = gateway.build_intent(
        domain_id="memory",
        subnet_scope="SOV-A",
        action="write",
        payload={"address": 9, "value": 99},
        signer_id="ops-gateway",
        nonce="pbg-3",
    )
    gr_mem = gateway.dispatch(intent=gi_mem, cap=gateway_cap, now_epoch_s=now_epoch)
    gr_mem_replay = gateway.dispatch(intent=gi_mem, cap=gateway_cap, now_epoch_s=now_epoch)

    gi_route = gateway.build_intent(
        domain_id="platform",
        subnet_scope="SOV-A",
        action="route_event",
        payload={"source_domain": "io", "route_action": "tick", "payload": {"x": 1}},
        signer_id="ops-gateway",
        nonce="pbg-4",
    )
    gr_route = gateway.dispatch(intent=gi_route, cap=gateway_cap, now_epoch_s=now_epoch)

    gi_bad = gateway.build_intent(
        domain_id="memory",
        subnet_scope="SOV-A",
        action="invalid_action",
        payload={},
        signer_id="ops-gateway",
        nonce="pbg-5",
    )
    gr_bad = gateway.dispatch(intent=gi_bad, cap=gateway_cap, now_epoch_s=now_epoch)

    checks.append(
        check(
            "Gateway board-domain dispatch",
            (
                gr_device.ok
                and gr_power.ok
                and gr_mem.ok
                and (not gr_mem_replay.ok)
                and gr_mem_replay.code == "E_COUNTER_REPLAY"
                and gr_route.ok
                and (not gr_bad.ok)
                and gr_bad.code == "E_POLICY_BLOCKED"
            ),
            "gateway routes board-equivalent intents with policy and replay controls",
            {
                "device": asdict(gr_device),
                "power": asdict(gr_power),
                "memory": asdict(gr_mem),
                "memory_replay": asdict(gr_mem_replay),
                "route": asdict(gr_route),
                "bad": asdict(gr_bad),
            },
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

    print("[platform_board_conformance] check_count:", payload["check_count"])
    print("[platform_board_conformance] pass_count:", payload["pass_count"])
    print("[platform_board_conformance] overall_pass:", payload["overall_pass"])
    print("[platform_board_conformance] report:", REPORT_PATH)
    return 0 if overall_pass else 28


if __name__ == "__main__":
    raise SystemExit(main())
