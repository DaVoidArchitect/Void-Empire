from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PeripheralCommandResult:
    ok: bool
    code: str
    peripheral_id: str
    command: str
    reason: str = ""


@dataclass(frozen=True)
class PeripheralQueryResult:
    ok: bool
    code: str
    peripheral_id: str
    state: dict[str, Any]
    reason: str = ""


class PeripheralPlaneAdapter:
    """Deterministic peripheral state plane model."""

    def __init__(self) -> None:
        self._state: dict[str, dict[str, Any]] = {}

    def register(self, *, peripheral_id: str, initial_state: dict[str, Any] | None = None) -> None:
        self._state[str(peripheral_id)] = dict(initial_state or {})

    def command(self, *, peripheral_id: str, command: str, params: dict[str, Any] | None = None) -> PeripheralCommandResult:
        pid = str(peripheral_id)
        if pid not in self._state:
            return PeripheralCommandResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                peripheral_id=pid,
                command=str(command),
                reason="peripheral not registered",
            )

        state = self._state[pid]
        state["last_command"] = str(command)
        state["last_params"] = dict(params or {})
        state["command_count"] = int(state.get("command_count", 0)) + 1
        return PeripheralCommandResult(ok=True, code="OK", peripheral_id=pid, command=str(command))

    def query(self, *, peripheral_id: str) -> PeripheralQueryResult:
        pid = str(peripheral_id)
        if pid not in self._state:
            return PeripheralQueryResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                peripheral_id=pid,
                state={},
                reason="peripheral not registered",
            )

        return PeripheralQueryResult(ok=True, code="OK", peripheral_id=pid, state=dict(self._state[pid]))

    def snapshot(self) -> dict[str, dict[str, Any]]:
        return {k: dict(v) for k, v in sorted(self._state.items())}
