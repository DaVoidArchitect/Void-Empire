from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NetworkTxResult:
    ok: bool
    code: str
    packet_id: str
    tx_queue_depth: int
    reason: str = ""


@dataclass(frozen=True)
class NetworkRxResult:
    ok: bool
    code: str
    packet_id: str
    payload: dict[str, Any]
    remaining_depth: int
    reason: str = ""


class NetworkLinkAdapter:
    """Deterministic packet link with duplicate suppression."""

    def __init__(self) -> None:
        self._rx_queue: list[tuple[str, dict[str, Any]]] = []
        self._seen_packet_ids: set[str] = set()

    def _packet_id(self, payload: dict[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def transmit(self, *, payload: dict[str, Any]) -> NetworkTxResult:
        packet = dict(payload)
        packet_id = self._packet_id(packet)
        if packet_id in self._seen_packet_ids:
            return NetworkTxResult(
                ok=False,
                code="E_COUNTER_REPLAY",
                packet_id=packet_id,
                tx_queue_depth=len(self._rx_queue),
                reason="duplicate packet detected",
            )

        self._seen_packet_ids.add(packet_id)
        self._rx_queue.append((packet_id, packet))
        return NetworkTxResult(ok=True, code="OK", packet_id=packet_id, tx_queue_depth=len(self._rx_queue))

    def receive(self) -> NetworkRxResult:
        if not self._rx_queue:
            return NetworkRxResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                packet_id="",
                payload={},
                remaining_depth=0,
                reason="rx queue empty",
            )

        packet_id, payload = self._rx_queue.pop(0)
        return NetworkRxResult(
            ok=True,
            code="OK",
            packet_id=packet_id,
            payload=dict(payload),
            remaining_depth=len(self._rx_queue),
        )

    def queue_depth(self) -> int:
        return len(self._rx_queue)

    def snapshot(self) -> dict[str, Any]:
        return {
            "rx_queue_depth": len(self._rx_queue),
            "rx_queue": [
                {"packet_id": packet_id, "payload": dict(payload)}
                for packet_id, payload in self._rx_queue
            ],
            "seen_packet_count": len(self._seen_packet_ids),
            "seen_packet_ids": sorted(self._seen_packet_ids),
        }
