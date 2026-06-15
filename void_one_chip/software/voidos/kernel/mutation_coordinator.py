from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .capabilities import Capability, CapabilityGuard
from .event_journal import DeterministicEventJournal


@dataclass(frozen=True)
class MutationResult:
    ok: bool
    code: str
    committed: bool
    event_id: str
    detail: str = ""


class MutationCoordinator:
    """Capability- and audit-coupled state mutation coordinator."""

    def __init__(
        self,
        *,
        guard: CapabilityGuard | None = None,
        journal: DeterministicEventJournal | None = None,
    ) -> None:
        self.guard = guard or CapabilityGuard()
        self.journal = journal or DeterministicEventJournal()
        self._committed_state: dict[str, dict[str, Any]] = {}

    @property
    def committed_state(self) -> dict[str, dict[str, Any]]:
        return {k: dict(v) for k, v in self._committed_state.items()}

    def snapshot(self) -> dict[str, Any]:
        return {
            "committed_state": {k: dict(v) for k, v in sorted(self._committed_state.items())},
            "journal": self.journal.snapshot(),
        }

    def commit(
        self,
        *,
        event_id: str,
        cap: Capability,
        required_right: str,
        subnet_scope: str,
        now_epoch_s: int,
        staged_delta: dict[str, Any],
        force_audit_fail: bool = False,
    ) -> MutationResult:
        cap_ok, cap_code = self.guard.validate(
            cap,
            required_right=required_right,
            subnet_scope=subnet_scope,
            now_epoch_s=now_epoch_s,
        )
        if not cap_ok:
            return MutationResult(
                ok=False,
                code=cap_code,
                committed=False,
                event_id=str(event_id),
                detail="capability gate rejected mutation",
            )

        journal_ok, journal_code = self.journal.append(
            event_id=str(event_id),
            payload=staged_delta,
            force_fail=force_audit_fail,
        )
        if not journal_ok:
            return MutationResult(
                ok=False,
                code=journal_code,
                committed=False,
                event_id=str(event_id),
                detail="audit digest append failed; staged mutation rolled back",
            )

        self._committed_state[str(event_id)] = dict(staged_delta)
        return MutationResult(ok=True, code="OK", committed=True, event_id=str(event_id))
