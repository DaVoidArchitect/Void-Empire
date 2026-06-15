from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..kernel.capabilities import Capability
from ..kernel.mutation_coordinator import MutationCoordinator


@dataclass(frozen=True)
class LegacyEvent:
    event_id: str
    subject_id: str
    subnet_id: str
    quest_id: str
    impact_metrics: dict[str, Any]
    evidence_hashes: list[str]
    signer_set: list[str]


@dataclass(frozen=True)
class LegacyGovernedResult:
    ok: bool
    code: str
    committed: bool
    event_id: str
    legacy_event: LegacyEvent | None
    detail: str = ""


class LegacyGraphService:
    """Append-only legacy graph recorder for provenance-linked events."""

    def __init__(self, *, coordinator: MutationCoordinator | None = None) -> None:
        self._events: list[LegacyEvent] = []
        self._coordinator = coordinator or MutationCoordinator()

    @property
    def committed_state(self) -> dict[str, dict[str, object]]:
        return self._coordinator.committed_state

    @property
    def events(self) -> list[LegacyEvent]:
        return list(self._events)

    def snapshot(self) -> dict[str, Any]:
        return {
            "event_count": len(self._events),
            "events": [
                {
                    "event_id": ev.event_id,
                    "subject_id": ev.subject_id,
                    "subnet_id": ev.subnet_id,
                    "quest_id": ev.quest_id,
                    "impact_metrics": dict(ev.impact_metrics),
                    "evidence_hashes": list(ev.evidence_hashes),
                    "signer_set": list(ev.signer_set),
                }
                for ev in self._events
            ],
            "coordinator": self._coordinator.snapshot(),
        }

    def append_event(
        self,
        *,
        event_id: str,
        subject_id: str,
        subnet_id: str,
        quest_id: str,
        impact_metrics: dict[str, Any],
        evidence_hashes: list[str],
        signer_set: list[str],
    ) -> LegacyEvent:
        ev = LegacyEvent(
            event_id=str(event_id),
            subject_id=str(subject_id),
            subnet_id=str(subnet_id),
            quest_id=str(quest_id),
            impact_metrics=dict(impact_metrics),
            evidence_hashes=list(evidence_hashes),
            signer_set=list(signer_set),
        )
        self._events.append(ev)
        return ev

    def append_event_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        subnet_scope: str,
        now_epoch_s: int,
        subject_id: str,
        subnet_id: str,
        quest_id: str,
        impact_metrics: dict[str, Any],
        evidence_hashes: list[str],
        signer_set: list[str],
        force_audit_fail: bool = False,
    ) -> LegacyGovernedResult:
        if str(subnet_scope) != str(subnet_id):
            return LegacyGovernedResult(
                ok=False,
                code="E_SCOPE_VIOLATION",
                committed=False,
                event_id=str(event_id),
                legacy_event=None,
                detail="requested subnet scope does not match event subnet",
            )

        staged_delta = {
            "domain": "legacy",
            "action": "append_event",
            "subject_id": str(subject_id),
            "subnet_id": str(subnet_id),
            "quest_id": str(quest_id),
            "impact_metrics": dict(impact_metrics),
            "evidence_hashes": list(evidence_hashes),
            "signer_set": list(signer_set),
        }

        mutation = self._coordinator.commit(
            event_id=str(event_id),
            cap=cap,
            required_right="LEGACY_APPEND",
            subnet_scope=str(subnet_scope),
            now_epoch_s=int(now_epoch_s),
            staged_delta=staged_delta,
            force_audit_fail=bool(force_audit_fail),
        )
        if not mutation.ok:
            return LegacyGovernedResult(
                ok=False,
                code=mutation.code,
                committed=False,
                event_id=mutation.event_id,
                legacy_event=None,
                detail=mutation.detail,
            )

        ev = self.append_event(
            event_id=str(event_id),
            subject_id=str(subject_id),
            subnet_id=str(subnet_id),
            quest_id=str(quest_id),
            impact_metrics=dict(impact_metrics),
            evidence_hashes=list(evidence_hashes),
            signer_set=list(signer_set),
        )
        return LegacyGovernedResult(
            ok=True,
            code="OK",
            committed=True,
            event_id=str(event_id),
            legacy_event=ev,
        )
