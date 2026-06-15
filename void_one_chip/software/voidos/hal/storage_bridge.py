from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StorageWriteResult:
    ok: bool
    code: str
    block_id: int
    bytes_written: int
    reason: str = ""


@dataclass(frozen=True)
class StorageReadResult:
    ok: bool
    code: str
    block_id: int
    payload: str
    reason: str = ""


class StorageBridgeAdapter:
    """Deterministic block storage bridge model."""

    def __init__(self, *, block_count: int = 1024, block_size: int = 4096) -> None:
        self._block_count = max(1, int(block_count))
        self._block_size = max(1, int(block_size))
        self._blocks: dict[int, str] = {}

    def _in_range(self, block_id: int) -> bool:
        return 0 <= int(block_id) < self._block_count

    def is_block_valid(self, *, block_id: int) -> bool:
        return self._in_range(int(block_id))

    def write_block(self, *, block_id: int, payload: str) -> StorageWriteResult:
        bid = int(block_id)
        if not self._in_range(bid):
            return StorageWriteResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                block_id=bid,
                bytes_written=0,
                reason="block id out of range",
            )

        text = str(payload)
        truncated = text[: self._block_size]
        self._blocks[bid] = truncated
        return StorageWriteResult(ok=True, code="OK", block_id=bid, bytes_written=len(truncated.encode("utf-8")))

    def read_block(self, *, block_id: int) -> StorageReadResult:
        bid = int(block_id)
        if not self._in_range(bid):
            return StorageReadResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                block_id=bid,
                payload="",
                reason="block id out of range",
            )

        return StorageReadResult(ok=True, code="OK", block_id=bid, payload=str(self._blocks.get(bid, "")))

    def snapshot(self) -> dict[str, str]:
        return {str(k): v for k, v in sorted(self._blocks.items())}
