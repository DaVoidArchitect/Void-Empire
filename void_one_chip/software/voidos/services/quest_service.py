from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ..kernel.capabilities import Capability
from ..kernel.mutation_coordinator import MutationCoordinator


@dataclass
class Quest:
    quest_id: str
    issuer_id: str
    subnet_scope: str
    payout_value: int
    proof_required: bool
    claimed_by: str | None = None
    proof_submitted: bool = False
    settled: bool = False


@dataclass(frozen=True)
class GovernedActionResult:
    ok: bool
    code: str
    committed: bool
    event_id: str
    detail: str = ""


class QuestService:
    """Minimal quest lifecycle service for Phase-1 executable skeleton."""

    def __init__(self, *, coordinator: MutationCoordinator | None = None) -> None:
        self._quests: dict[str, Quest] = {}
        self._coordinator = coordinator or MutationCoordinator()

    @property
    def committed_state(self) -> dict[str, dict[str, object]]:
        return self._coordinator.committed_state

    def snapshot(self) -> dict[str, Any]:
        return {
            "quests": {
                quest_id: asdict(quest)
                for quest_id, quest in sorted(self._quests.items())
            },
            "coordinator": self._coordinator.snapshot(),
        }

    def create(self, *, quest_id: str, issuer_id: str, subnet_scope: str, payout_value: int, proof_required: bool = True) -> Quest:
        quest = Quest(
            quest_id=str(quest_id),
            issuer_id=str(issuer_id),
            subnet_scope=str(subnet_scope),
            payout_value=max(0, int(payout_value)),
            proof_required=bool(proof_required),
        )
        self._quests[quest.quest_id] = quest
        return quest

    def claim(self, *, quest_id: str, subject_id: str) -> tuple[bool, str]:
        q = self._quests.get(str(quest_id))
        if q is None:
            return (False, "E_POLICY_BLOCKED")
        if q.claimed_by is not None:
            return (False, "E_POLICY_BLOCKED")
        q.claimed_by = str(subject_id)
        return (True, "OK")

    def submit_proof(self, *, quest_id: str, proof_payload: dict[str, Any]) -> tuple[bool, str]:
        q = self._quests.get(str(quest_id))
        if q is None:
            return (False, "E_PROOF_INVALID")
        if q.proof_required and not proof_payload:
            return (False, "E_PROOF_INVALID")
        q.proof_submitted = True
        return (True, "OK")

    def ready_to_settle(self, *, quest_id: str) -> bool:
        q = self._quests.get(str(quest_id))
        if q is None:
            return False
        if q.claimed_by is None:
            return False
        if q.proof_required and not q.proof_submitted:
            return False
        return not q.settled

    def mark_settled(self, *, quest_id: str) -> tuple[bool, str]:
        q = self._quests.get(str(quest_id))
        if q is None:
            return (False, "E_POLICY_BLOCKED")
        if not self.ready_to_settle(quest_id=quest_id):
            return (False, "E_POLICY_BLOCKED")
        q.settled = True
        return (True, "OK")

    def claim_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        quest_id: str,
        subject_id: str,
        force_audit_fail: bool = False,
    ) -> GovernedActionResult:
        q = self._quests.get(str(quest_id))
        if q is None:
            return GovernedActionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                detail="quest not found",
            )
        if q.claimed_by is not None:
            return GovernedActionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                detail="quest already claimed",
            )

        mutation = self._coordinator.commit(
            event_id=str(event_id),
            cap=cap,
            required_right="QUEST_CLAIM",
            subnet_scope=q.subnet_scope,
            now_epoch_s=int(now_epoch_s),
            staged_delta={
                "domain": "quest",
                "action": "claim",
                "quest_id": str(quest_id),
                "subject_id": str(subject_id),
            },
            force_audit_fail=bool(force_audit_fail),
        )
        if not mutation.ok:
            return GovernedActionResult(
                ok=False,
                code=mutation.code,
                committed=False,
                event_id=mutation.event_id,
                detail=mutation.detail,
            )
        q.claimed_by = str(subject_id)
        return GovernedActionResult(ok=True, code="OK", committed=True, event_id=mutation.event_id)

    def submit_proof_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        quest_id: str,
        proof_payload: dict[str, Any],
        force_audit_fail: bool = False,
    ) -> GovernedActionResult:
        q = self._quests.get(str(quest_id))
        if q is None:
            return GovernedActionResult(
                ok=False,
                code="E_PROOF_INVALID",
                committed=False,
                event_id=str(event_id),
                detail="quest not found",
            )
        if q.proof_required and not proof_payload:
            return GovernedActionResult(
                ok=False,
                code="E_PROOF_INVALID",
                committed=False,
                event_id=str(event_id),
                detail="empty proof payload for proof-required quest",
            )

        mutation = self._coordinator.commit(
            event_id=str(event_id),
            cap=cap,
            required_right="QUEST_SUBMIT_PROOF",
            subnet_scope=q.subnet_scope,
            now_epoch_s=int(now_epoch_s),
            staged_delta={
                "domain": "quest",
                "action": "submit_proof",
                "quest_id": str(quest_id),
                "proof_payload": dict(proof_payload),
            },
            force_audit_fail=bool(force_audit_fail),
        )
        if not mutation.ok:
            return GovernedActionResult(
                ok=False,
                code=mutation.code,
                committed=False,
                event_id=mutation.event_id,
                detail=mutation.detail,
            )
        q.proof_submitted = True
        return GovernedActionResult(ok=True, code="OK", committed=True, event_id=mutation.event_id)

    def mark_settled_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        quest_id: str,
        force_audit_fail: bool = False,
    ) -> GovernedActionResult:
        q = self._quests.get(str(quest_id))
        if q is None:
            return GovernedActionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                detail="quest not found",
            )
        if not self.ready_to_settle(quest_id=quest_id):
            return GovernedActionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                detail="quest not ready to settle",
            )

        mutation = self._coordinator.commit(
            event_id=str(event_id),
            cap=cap,
            required_right="QUEST_SETTLE",
            subnet_scope=q.subnet_scope,
            now_epoch_s=int(now_epoch_s),
            staged_delta={
                "domain": "quest",
                "action": "mark_settled",
                "quest_id": str(quest_id),
            },
            force_audit_fail=bool(force_audit_fail),
        )
        if not mutation.ok:
            return GovernedActionResult(
                ok=False,
                code=mutation.code,
                committed=False,
                event_id=mutation.event_id,
                detail=mutation.detail,
            )
        q.settled = True
        return GovernedActionResult(ok=True, code="OK", committed=True, event_id=mutation.event_id)
