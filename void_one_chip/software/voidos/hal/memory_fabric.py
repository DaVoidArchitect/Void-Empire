from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryWriteResult:
    ok: bool
    code: str
    address: int
    stored_value: int
    reason: str = ""


@dataclass(frozen=True)
class MemoryReadResult:
    ok: bool
    code: str
    address: int
    value: int
    reason: str = ""


class MemoryFabricAdapter:
    """Deterministic word-addressable memory fabric model."""

    def __init__(self, *, address_space_words: int = 4096, word_bits: int = 64) -> None:
        self._address_space_words = max(1, int(address_space_words))
        self._word_bits = max(1, int(word_bits))
        self._mask = (1 << self._word_bits) - 1
        self._cells: dict[int, int] = {}

    def _in_range(self, address: int) -> bool:
        return 0 <= int(address) < self._address_space_words

    def is_address_valid(self, *, address: int) -> bool:
        return self._in_range(int(address))

    def write_word(self, *, address: int, value: int) -> MemoryWriteResult:
        addr = int(address)
        if not self._in_range(addr):
            return MemoryWriteResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                address=addr,
                stored_value=0,
                reason="address out of range",
            )

        stored = int(value) & self._mask
        self._cells[addr] = stored
        return MemoryWriteResult(ok=True, code="OK", address=addr, stored_value=stored)

    def read_word(self, *, address: int) -> MemoryReadResult:
        addr = int(address)
        if not self._in_range(addr):
            return MemoryReadResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                address=addr,
                value=0,
                reason="address out of range",
            )

        return MemoryReadResult(ok=True, code="OK", address=addr, value=int(self._cells.get(addr, 0)))

    def snapshot(self) -> dict[str, int]:
        return {str(k): int(v) for k, v in sorted(self._cells.items())}
