from __future__ import annotations


class MonotonicCounterAdapter:
    """Monotonic counter source keyed by (domain_id, subnet_scope)."""

    def __init__(self) -> None:
        self._counters: dict[tuple[str, str], int] = {}

    def next(self, *, domain_id: str, subnet_scope: str) -> int:
        key = (str(domain_id), str(subnet_scope))
        value = self._counters.get(key, 0) + 1
        self._counters[key] = value
        return value

    def peek(self, *, domain_id: str, subnet_scope: str) -> int:
        return self._counters.get((str(domain_id), str(subnet_scope)), 0)

    def snapshot(self) -> dict[str, int]:
        return {
            f"{domain}:{subnet}": int(value)
            for (domain, subnet), value in sorted(self._counters.items())
        }
