from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DeviceRecord:
    device_id: str
    device_class: str
    subnet_scope: str
    metadata: dict[str, Any]


class DeviceRegistry:
    """Deterministic board-device registry with conflict protection."""

    def __init__(self) -> None:
        self._devices: dict[str, DeviceRecord] = {}

    def has_device(self, *, device_id: str) -> bool:
        return str(device_id) in self._devices

    def register(
        self,
        *,
        device_id: str,
        device_class: str,
        subnet_scope: str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[bool, str, DeviceRecord | None]:
        did = str(device_id)
        if did in self._devices:
            return (False, "E_LEDGER_CONFLICT", None)

        record = DeviceRecord(
            device_id=did,
            device_class=str(device_class),
            subnet_scope=str(subnet_scope),
            metadata=dict(metadata or {}),
        )
        self._devices[did] = record
        return (True, "OK", record)

    def remove(self, *, device_id: str) -> tuple[bool, str, DeviceRecord | None]:
        did = str(device_id)
        record = self._devices.pop(did, None)
        if record is None:
            return (False, "E_POLICY_BLOCKED", None)
        return (True, "OK", record)

    def get(self, *, device_id: str) -> DeviceRecord | None:
        return self._devices.get(str(device_id))

    def snapshot(self) -> dict[str, dict[str, Any]]:
        return {
            key: {
                "device_id": rec.device_id,
                "device_class": rec.device_class,
                "subnet_scope": rec.subnet_scope,
                "metadata": dict(rec.metadata),
            }
            for key, rec in sorted(self._devices.items())
        }
