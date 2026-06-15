from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IoEmitResult:
    ok: bool
    code: str
    endpoint_id: str
    queue_depth: int
    reason: str = ""


@dataclass(frozen=True)
class IoPollResult:
    ok: bool
    code: str
    endpoint_id: str
    payload: dict[str, Any]
    remaining_depth: int
    reason: str = ""


class IoBusAdapter:
    """Deterministic endpoint queue model for board I/O lanes."""

    def __init__(self) -> None:
        self._queues: dict[str, list[dict[str, Any]]] = {}

    def emit(self, *, endpoint_id: str, payload: dict[str, Any]) -> IoEmitResult:
        eid = str(endpoint_id)
        q = self._queues.setdefault(eid, [])
        q.append(dict(payload))
        return IoEmitResult(ok=True, code="OK", endpoint_id=eid, queue_depth=len(q))

    def poll(self, *, endpoint_id: str) -> IoPollResult:
        eid = str(endpoint_id)
        q = self._queues.setdefault(eid, [])
        if not q:
            return IoPollResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                endpoint_id=eid,
                payload={},
                remaining_depth=0,
                reason="endpoint queue is empty",
            )

        payload = q.pop(0)
        return IoPollResult(ok=True, code="OK", endpoint_id=eid, payload=payload, remaining_depth=len(q))

    def snapshot_depth(self) -> dict[str, int]:
        return {k: len(v) for k, v in sorted(self._queues.items())}

    def snapshot(self) -> dict[str, Any]:
        return {
            "depth": self.snapshot_depth(),
            "queues": {
                endpoint: [dict(item) for item in queue]
                for endpoint, queue in sorted(self._queues.items())
            },
        }
