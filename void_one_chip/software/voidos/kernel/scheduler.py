from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DEFAULT_DOMAIN_PRIORITY = {
    "root": 0,
    "treasury": 1,
    "quest": 2,
    "legacy": 3,
    "knowledge": 3,
    "governance": 3,
    "general": 4,
    "app": 4,
}


@dataclass(frozen=True)
class ScheduledIntent:
    domain_id: str
    subnet_scope: str
    monotonic_counter: int
    pulse_id: str
    payload: dict[str, Any]


class DeterministicDomainScheduler:
    """Deterministic scheduler for ordered intent execution."""

    def __init__(self, domain_priority: dict[str, int] | None = None) -> None:
        self._domain_priority = dict(DEFAULT_DOMAIN_PRIORITY)
        if domain_priority:
            self._domain_priority.update({str(k): int(v) for k, v in domain_priority.items()})

    def priority_of(self, domain_id: str) -> int:
        return int(self._domain_priority.get(str(domain_id), 99))

    def order(self, intents: list[ScheduledIntent]) -> list[ScheduledIntent]:
        return sorted(
            intents,
            key=lambda x: (
                self.priority_of(x.domain_id),
                str(x.domain_id),
                str(x.subnet_scope),
                int(x.monotonic_counter),
                str(x.pulse_id),
            ),
        )
