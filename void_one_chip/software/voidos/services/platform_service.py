from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..hal.io_bus import IoBusAdapter
from ..hal.memory_fabric import MemoryFabricAdapter
from ..hal.network_link import NetworkLinkAdapter
from ..hal.peripheral_plane import PeripheralPlaneAdapter
from ..hal.storage_bridge import StorageBridgeAdapter
from ..kernel.boot_power_governor import BootPowerGovernor
from ..kernel.capabilities import Capability
from ..kernel.device_registry import DeviceRecord, DeviceRegistry
from ..kernel.event_router import EventRouter, RoutedEvent
from ..kernel.mutation_coordinator import MutationCoordinator


@dataclass(frozen=True)
class PlatformActionResult:
    ok: bool
    code: str
    committed: bool
    event_id: str
    detail: str = ""
    data: dict[str, Any] | None = None


class PlatformBoardService:
    """Motherboard-equivalent governed platform service."""

    def __init__(self, *, coordinator: MutationCoordinator | None = None) -> None:
        self._coordinator = coordinator or MutationCoordinator()
        self.memory = MemoryFabricAdapter()
        self.storage = StorageBridgeAdapter()
        self.io_bus = IoBusAdapter()
        self.network = NetworkLinkAdapter()
        self.peripherals = PeripheralPlaneAdapter()
        self.registry = DeviceRegistry()
        self.power = BootPowerGovernor()
        self.router = EventRouter()

    @property
    def committed_state(self) -> dict[str, dict[str, object]]:
        return self._coordinator.committed_state

    def snapshot(self) -> dict[str, Any]:
        return {
            "memory": self.memory.snapshot(),
            "storage": self.storage.snapshot(),
            "io": self.io_bus.snapshot(),
            "network": self.network.snapshot(),
            "peripherals": self.peripherals.snapshot(),
            "devices": self.registry.snapshot(),
            "power": {
                "state": self.power.state,
                "history": self.power.history,
            },
            "routing": self.router.snapshot(),
            "coordinator": self._coordinator.snapshot(),
        }

    def _commit(
        self,
        *,
        event_id: str,
        cap: Capability,
        required_right: str,
        subnet_scope: str,
        now_epoch_s: int,
        staged_delta: dict[str, Any],
        force_audit_fail: bool,
    ) -> PlatformActionResult:
        mutation = self._coordinator.commit(
            event_id=str(event_id),
            cap=cap,
            required_right=str(required_right),
            subnet_scope=str(subnet_scope),
            now_epoch_s=int(now_epoch_s),
            staged_delta=staged_delta,
            force_audit_fail=bool(force_audit_fail),
        )
        return PlatformActionResult(
            ok=mutation.ok,
            code=mutation.code,
            committed=mutation.committed,
            event_id=mutation.event_id,
            detail=mutation.detail,
        )

    def register_device_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        subnet_scope: str,
        device_id: str,
        device_class: str,
        metadata: dict[str, Any] | None = None,
        force_audit_fail: bool = False,
    ) -> PlatformActionResult:
        if self.registry.has_device(device_id=device_id):
            return PlatformActionResult(
                ok=False,
                code="E_LEDGER_CONFLICT",
                committed=False,
                event_id=str(event_id),
                detail="device already exists",
            )

        staged = {
            "domain": "device",
            "action": "register",
            "device_id": str(device_id),
            "device_class": str(device_class),
            "subnet_scope": str(subnet_scope),
            "metadata": dict(metadata or {}),
        }
        pre = self._commit(
            event_id=event_id,
            cap=cap,
            required_right="DEVICE_REGISTER",
            subnet_scope=subnet_scope,
            now_epoch_s=now_epoch_s,
            staged_delta=staged,
            force_audit_fail=force_audit_fail,
        )
        if not pre.ok:
            return pre

        ok, code, record = self.registry.register(
            device_id=str(device_id),
            device_class=str(device_class),
            subnet_scope=str(subnet_scope),
            metadata=dict(metadata or {}),
        )
        if not ok:
            return PlatformActionResult(
                ok=False,
                code=code,
                committed=False,
                event_id=pre.event_id,
                detail="device registry rejected registration",
            )
        return PlatformActionResult(
            ok=True,
            code="OK",
            committed=True,
            event_id=pre.event_id,
            data={"device": _device_to_dict(record)},
        )

    def remove_device_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        subnet_scope: str,
        device_id: str,
        force_audit_fail: bool = False,
    ) -> PlatformActionResult:
        if not self.registry.has_device(device_id=device_id):
            return PlatformActionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                detail="device not found",
            )

        staged = {
            "domain": "device",
            "action": "remove",
            "device_id": str(device_id),
            "subnet_scope": str(subnet_scope),
        }
        pre = self._commit(
            event_id=event_id,
            cap=cap,
            required_right="DEVICE_REMOVE",
            subnet_scope=subnet_scope,
            now_epoch_s=now_epoch_s,
            staged_delta=staged,
            force_audit_fail=force_audit_fail,
        )
        if not pre.ok:
            return pre

        ok, code, removed = self.registry.remove(device_id=str(device_id))
        if not ok:
            return PlatformActionResult(
                ok=False,
                code=code,
                committed=False,
                event_id=pre.event_id,
                detail="device registry removal failed",
            )
        return PlatformActionResult(
            ok=True,
            code="OK",
            committed=True,
            event_id=pre.event_id,
            data={"device": _device_to_dict(removed)},
        )

    def transition_power_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        subnet_scope: str,
        target_state: str,
        force_audit_fail: bool = False,
    ) -> PlatformActionResult:
        if not self.power.can_transition(target_state=str(target_state)):
            return PlatformActionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                detail=f"illegal transition {self.power.state} -> {str(target_state).upper()}",
            )

        staged = {
            "domain": "power",
            "action": "transition",
            "from_state": self.power.state,
            "to_state": str(target_state).upper(),
            "subnet_scope": str(subnet_scope),
        }
        pre = self._commit(
            event_id=event_id,
            cap=cap,
            required_right="POWER_TRANSITION",
            subnet_scope=subnet_scope,
            now_epoch_s=now_epoch_s,
            staged_delta=staged,
            force_audit_fail=force_audit_fail,
        )
        if not pre.ok:
            return pre

        transition = self.power.transition(target_state=str(target_state))
        if not transition.ok:
            return PlatformActionResult(
                ok=False,
                code=transition.code,
                committed=False,
                event_id=pre.event_id,
                detail=transition.reason,
            )
        return PlatformActionResult(
            ok=True,
            code="OK",
            committed=True,
            event_id=pre.event_id,
            data={"state": self.power.state, "history": self.power.history},
        )

    def memory_write_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        subnet_scope: str,
        address: int,
        value: int,
        force_audit_fail: bool = False,
    ) -> PlatformActionResult:
        if not self.memory.is_address_valid(address=int(address)):
            return PlatformActionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                detail="memory address out of range",
            )

        staged = {
            "domain": "memory",
            "action": "write",
            "address": int(address),
            "value": int(value),
            "subnet_scope": str(subnet_scope),
        }
        pre = self._commit(
            event_id=event_id,
            cap=cap,
            required_right="MEMORY_WRITE",
            subnet_scope=subnet_scope,
            now_epoch_s=now_epoch_s,
            staged_delta=staged,
            force_audit_fail=force_audit_fail,
        )
        if not pre.ok:
            return pre

        wr = self.memory.write_word(address=int(address), value=int(value))
        return PlatformActionResult(
            ok=wr.ok,
            code=wr.code,
            committed=wr.ok,
            event_id=pre.event_id,
            detail=wr.reason,
            data={"address": wr.address, "stored_value": wr.stored_value},
        )

    def memory_read_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        subnet_scope: str,
        address: int,
        force_audit_fail: bool = False,
    ) -> PlatformActionResult:
        if not self.memory.is_address_valid(address=int(address)):
            return PlatformActionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                detail="memory address out of range",
            )

        staged = {
            "domain": "memory",
            "action": "read",
            "address": int(address),
            "subnet_scope": str(subnet_scope),
        }
        pre = self._commit(
            event_id=event_id,
            cap=cap,
            required_right="MEMORY_READ",
            subnet_scope=subnet_scope,
            now_epoch_s=now_epoch_s,
            staged_delta=staged,
            force_audit_fail=force_audit_fail,
        )
        if not pre.ok:
            return pre

        rr = self.memory.read_word(address=int(address))
        return PlatformActionResult(
            ok=rr.ok,
            code=rr.code,
            committed=rr.ok,
            event_id=pre.event_id,
            detail=rr.reason,
            data={"address": rr.address, "value": rr.value},
        )

    def storage_write_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        subnet_scope: str,
        block_id: int,
        payload: str,
        force_audit_fail: bool = False,
    ) -> PlatformActionResult:
        if not self.storage.is_block_valid(block_id=int(block_id)):
            return PlatformActionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                detail="storage block out of range",
            )

        staged = {
            "domain": "storage",
            "action": "write",
            "block_id": int(block_id),
            "payload": str(payload),
            "subnet_scope": str(subnet_scope),
        }
        pre = self._commit(
            event_id=event_id,
            cap=cap,
            required_right="STORAGE_WRITE",
            subnet_scope=subnet_scope,
            now_epoch_s=now_epoch_s,
            staged_delta=staged,
            force_audit_fail=force_audit_fail,
        )
        if not pre.ok:
            return pre

        wr = self.storage.write_block(block_id=int(block_id), payload=str(payload))
        return PlatformActionResult(
            ok=wr.ok,
            code=wr.code,
            committed=wr.ok,
            event_id=pre.event_id,
            detail=wr.reason,
            data={"block_id": wr.block_id, "bytes_written": wr.bytes_written},
        )

    def storage_read_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        subnet_scope: str,
        block_id: int,
        force_audit_fail: bool = False,
    ) -> PlatformActionResult:
        if not self.storage.is_block_valid(block_id=int(block_id)):
            return PlatformActionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                detail="storage block out of range",
            )

        staged = {
            "domain": "storage",
            "action": "read",
            "block_id": int(block_id),
            "subnet_scope": str(subnet_scope),
        }
        pre = self._commit(
            event_id=event_id,
            cap=cap,
            required_right="STORAGE_READ",
            subnet_scope=subnet_scope,
            now_epoch_s=now_epoch_s,
            staged_delta=staged,
            force_audit_fail=force_audit_fail,
        )
        if not pre.ok:
            return pre

        rr = self.storage.read_block(block_id=int(block_id))
        return PlatformActionResult(
            ok=rr.ok,
            code=rr.code,
            committed=rr.ok,
            event_id=pre.event_id,
            detail=rr.reason,
            data={"block_id": rr.block_id, "payload": rr.payload},
        )

    def io_emit_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        subnet_scope: str,
        endpoint_id: str,
        payload: dict[str, Any],
        force_audit_fail: bool = False,
    ) -> PlatformActionResult:
        staged = {
            "domain": "io",
            "action": "emit",
            "endpoint_id": str(endpoint_id),
            "payload": dict(payload),
            "subnet_scope": str(subnet_scope),
        }
        pre = self._commit(
            event_id=event_id,
            cap=cap,
            required_right="IO_EMIT",
            subnet_scope=subnet_scope,
            now_epoch_s=now_epoch_s,
            staged_delta=staged,
            force_audit_fail=force_audit_fail,
        )
        if not pre.ok:
            return pre

        emit = self.io_bus.emit(endpoint_id=str(endpoint_id), payload=dict(payload))
        return PlatformActionResult(
            ok=emit.ok,
            code=emit.code,
            committed=emit.ok,
            event_id=pre.event_id,
            detail=emit.reason,
            data={"endpoint_id": emit.endpoint_id, "queue_depth": emit.queue_depth},
        )

    def io_poll_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        subnet_scope: str,
        endpoint_id: str,
        force_audit_fail: bool = False,
    ) -> PlatformActionResult:
        staged = {
            "domain": "io",
            "action": "poll",
            "endpoint_id": str(endpoint_id),
            "subnet_scope": str(subnet_scope),
        }
        pre = self._commit(
            event_id=event_id,
            cap=cap,
            required_right="IO_POLL",
            subnet_scope=subnet_scope,
            now_epoch_s=now_epoch_s,
            staged_delta=staged,
            force_audit_fail=force_audit_fail,
        )
        if not pre.ok:
            return pre

        poll = self.io_bus.poll(endpoint_id=str(endpoint_id))
        return PlatformActionResult(
            ok=poll.ok,
            code=poll.code,
            committed=poll.ok,
            event_id=pre.event_id,
            detail=poll.reason,
            data={
                "endpoint_id": poll.endpoint_id,
                "payload": dict(poll.payload),
                "remaining_depth": poll.remaining_depth,
            },
        )

    def network_tx_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        subnet_scope: str,
        payload: dict[str, Any],
        force_audit_fail: bool = False,
    ) -> PlatformActionResult:
        staged = {
            "domain": "network",
            "action": "tx",
            "payload": dict(payload),
            "subnet_scope": str(subnet_scope),
        }
        pre = self._commit(
            event_id=event_id,
            cap=cap,
            required_right="NETWORK_TX",
            subnet_scope=subnet_scope,
            now_epoch_s=now_epoch_s,
            staged_delta=staged,
            force_audit_fail=force_audit_fail,
        )
        if not pre.ok:
            return pre

        tx = self.network.transmit(payload=dict(payload))
        return PlatformActionResult(
            ok=tx.ok,
            code=tx.code,
            committed=tx.ok,
            event_id=pre.event_id,
            detail=tx.reason,
            data={"packet_id": tx.packet_id, "tx_queue_depth": tx.tx_queue_depth},
        )

    def network_rx_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        subnet_scope: str,
        force_audit_fail: bool = False,
    ) -> PlatformActionResult:
        staged = {
            "domain": "network",
            "action": "rx",
            "subnet_scope": str(subnet_scope),
        }
        pre = self._commit(
            event_id=event_id,
            cap=cap,
            required_right="NETWORK_RX",
            subnet_scope=subnet_scope,
            now_epoch_s=now_epoch_s,
            staged_delta=staged,
            force_audit_fail=force_audit_fail,
        )
        if not pre.ok:
            return pre

        rx = self.network.receive()
        return PlatformActionResult(
            ok=rx.ok,
            code=rx.code,
            committed=rx.ok,
            event_id=pre.event_id,
            detail=rx.reason,
            data={
                "packet_id": rx.packet_id,
                "payload": dict(rx.payload),
                "remaining_depth": rx.remaining_depth,
            },
        )

    def peripheral_register(self, *, peripheral_id: str, initial_state: dict[str, Any] | None = None) -> None:
        self.peripherals.register(peripheral_id=str(peripheral_id), initial_state=dict(initial_state or {}))

    def peripheral_command_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        subnet_scope: str,
        peripheral_id: str,
        command: str,
        params: dict[str, Any] | None = None,
        force_audit_fail: bool = False,
    ) -> PlatformActionResult:
        staged = {
            "domain": "peripheral",
            "action": "command",
            "peripheral_id": str(peripheral_id),
            "command": str(command),
            "params": dict(params or {}),
            "subnet_scope": str(subnet_scope),
        }
        pre = self._commit(
            event_id=event_id,
            cap=cap,
            required_right="PERIPHERAL_COMMAND",
            subnet_scope=subnet_scope,
            now_epoch_s=now_epoch_s,
            staged_delta=staged,
            force_audit_fail=force_audit_fail,
        )
        if not pre.ok:
            return pre

        cmd = self.peripherals.command(
            peripheral_id=str(peripheral_id),
            command=str(command),
            params=dict(params or {}),
        )
        return PlatformActionResult(
            ok=cmd.ok,
            code=cmd.code,
            committed=cmd.ok,
            event_id=pre.event_id,
            detail=cmd.reason,
            data={"peripheral_id": cmd.peripheral_id, "command": cmd.command},
        )

    def peripheral_query_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        subnet_scope: str,
        peripheral_id: str,
        force_audit_fail: bool = False,
    ) -> PlatformActionResult:
        staged = {
            "domain": "peripheral",
            "action": "query",
            "peripheral_id": str(peripheral_id),
            "subnet_scope": str(subnet_scope),
        }
        pre = self._commit(
            event_id=event_id,
            cap=cap,
            required_right="PERIPHERAL_QUERY",
            subnet_scope=subnet_scope,
            now_epoch_s=now_epoch_s,
            staged_delta=staged,
            force_audit_fail=force_audit_fail,
        )
        if not pre.ok:
            return pre

        q = self.peripherals.query(peripheral_id=str(peripheral_id))
        return PlatformActionResult(
            ok=q.ok,
            code=q.code,
            committed=q.ok,
            event_id=pre.event_id,
            detail=q.reason,
            data={"peripheral_id": q.peripheral_id, "state": dict(q.state)},
        )

    def add_route(self, *, source_domain: str, action: str, target_domain: str, endpoint_id: str) -> None:
        self.router.add_route(
            source_domain=str(source_domain),
            action=str(action),
            target_domain=str(target_domain),
            endpoint_id=str(endpoint_id),
        )

    def route_event_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        subnet_scope: str,
        source_domain: str,
        action: str,
        payload: dict[str, Any],
        force_audit_fail: bool = False,
    ) -> PlatformActionResult:
        ok_route, code_route, routed = self.router.route(
            event_id=str(event_id),
            source_domain=str(source_domain),
            action=str(action),
            payload=dict(payload),
        )
        if not ok_route or routed is None:
            return PlatformActionResult(
                ok=False,
                code=code_route,
                committed=False,
                event_id=str(event_id),
                detail="route not found",
            )

        staged = {
            "domain": "platform",
            "action": "route_event",
            "source_domain": str(source_domain),
            "route_action": str(action),
            "target_domain": routed.target_domain,
            "endpoint_id": routed.endpoint_id,
            "payload": dict(payload),
            "subnet_scope": str(subnet_scope),
        }
        pre = self._commit(
            event_id=event_id,
            cap=cap,
            required_right="ROUTE_EVENT",
            subnet_scope=subnet_scope,
            now_epoch_s=now_epoch_s,
            staged_delta=staged,
            force_audit_fail=force_audit_fail,
        )
        if not pre.ok:
            return pre

        return PlatformActionResult(
            ok=True,
            code="OK",
            committed=True,
            event_id=pre.event_id,
            data={
                "routed": _routed_event_to_dict(routed),
            },
        )

    def order_routed_events(
        self,
        *,
        subnet_scope: str,
        routed_events: list[RoutedEvent],
    ) -> list[RoutedEvent]:
        return self.router.order_dispatches(subnet_scope=str(subnet_scope), routed_events=list(routed_events))


def _device_to_dict(device: DeviceRecord | None) -> dict[str, Any] | None:
    if device is None:
        return None
    return {
        "device_id": device.device_id,
        "device_class": device.device_class,
        "subnet_scope": device.subnet_scope,
        "metadata": dict(device.metadata),
    }


def _routed_event_to_dict(routed: RoutedEvent) -> dict[str, Any]:
    return {
        "event_id": routed.event_id,
        "source_domain": routed.source_domain,
        "action": routed.action,
        "target_domain": routed.target_domain,
        "endpoint_id": routed.endpoint_id,
        "payload": dict(routed.payload),
    }
