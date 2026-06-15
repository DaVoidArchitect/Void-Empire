from __future__ import annotations

from dataclasses import asdict, dataclass

from ..kernel.capabilities import Capability
from ..kernel.mutation_coordinator import MutationCoordinator


@dataclass
class Proposal:
    proposal_id: str
    subnet_scope: str
    title: str
    body_hash: str
    created_by: str
    yes_votes: int = 0
    no_votes: int = 0
    finalized: bool = False
    accepted: bool = False


@dataclass(frozen=True)
class GovernanceActionResult:
    ok: bool
    code: str
    committed: bool
    event_id: str
    detail: str = ""


class GovernanceService:
    """Deterministic governance service with audit-coupled state transitions."""

    def __init__(self, *, coordinator: MutationCoordinator | None = None) -> None:
        self._coordinator = coordinator or MutationCoordinator()
        self._proposals: dict[str, Proposal] = {}

    @property
    def committed_state(self) -> dict[str, dict[str, object]]:
        return self._coordinator.committed_state

    def snapshot(self) -> dict[str, object]:
        return {
            "proposals": {
                proposal_id: asdict(proposal)
                for proposal_id, proposal in sorted(self._proposals.items())
            },
            "coordinator": self._coordinator.snapshot(),
        }

    def proposal(self, proposal_id: str) -> Proposal | None:
        return self._proposals.get(str(proposal_id))

    def create_proposal(
        self,
        *,
        proposal_id: str,
        subnet_scope: str,
        title: str,
        body_hash: str,
        created_by: str,
    ) -> Proposal:
        p = Proposal(
            proposal_id=str(proposal_id),
            subnet_scope=str(subnet_scope),
            title=str(title),
            body_hash=str(body_hash),
            created_by=str(created_by),
        )
        self._proposals[p.proposal_id] = p
        return p

    def cast_vote_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        proposal_id: str,
        subnet_scope: str,
        vote: str,
        force_audit_fail: bool = False,
    ) -> GovernanceActionResult:
        p = self._proposals.get(str(proposal_id))
        if p is None:
            return GovernanceActionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                detail="proposal not found",
            )
        if p.finalized:
            return GovernanceActionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                detail="proposal already finalized",
            )
        vote_norm = str(vote).strip().lower()
        if vote_norm not in {"yes", "no"}:
            return GovernanceActionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                detail="vote must be yes or no",
            )

        mutation = self._coordinator.commit(
            event_id=str(event_id),
            cap=cap,
            required_right="GOVERNANCE_VOTE",
            subnet_scope=str(subnet_scope),
            now_epoch_s=int(now_epoch_s),
            staged_delta={
                "domain": "governance",
                "action": "cast_vote",
                "proposal_id": p.proposal_id,
                "vote": vote_norm,
            },
            force_audit_fail=bool(force_audit_fail),
        )
        if not mutation.ok:
            return GovernanceActionResult(
                ok=False,
                code=mutation.code,
                committed=False,
                event_id=mutation.event_id,
                detail=mutation.detail,
            )

        if vote_norm == "yes":
            p.yes_votes += 1
        else:
            p.no_votes += 1
        return GovernanceActionResult(ok=True, code="OK", committed=True, event_id=mutation.event_id)

    def finalize_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        proposal_id: str,
        subnet_scope: str,
        minimum_yes_votes: int = 1,
        force_audit_fail: bool = False,
    ) -> GovernanceActionResult:
        p = self._proposals.get(str(proposal_id))
        if p is None:
            return GovernanceActionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                detail="proposal not found",
            )
        if p.finalized:
            return GovernanceActionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                detail="proposal already finalized",
            )

        accepted = bool(p.yes_votes >= int(minimum_yes_votes) and p.yes_votes > p.no_votes)

        mutation = self._coordinator.commit(
            event_id=str(event_id),
            cap=cap,
            required_right="GOVERNANCE_FINALIZE",
            subnet_scope=str(subnet_scope),
            now_epoch_s=int(now_epoch_s),
            staged_delta={
                "domain": "governance",
                "action": "finalize",
                "proposal_id": p.proposal_id,
                "accepted": accepted,
                "yes_votes": p.yes_votes,
                "no_votes": p.no_votes,
                "minimum_yes_votes": int(minimum_yes_votes),
            },
            force_audit_fail=bool(force_audit_fail),
        )
        if not mutation.ok:
            return GovernanceActionResult(
                ok=False,
                code=mutation.code,
                committed=False,
                event_id=mutation.event_id,
                detail=mutation.detail,
            )

        p.finalized = True
        p.accepted = accepted
        return GovernanceActionResult(ok=True, code="OK", committed=True, event_id=mutation.event_id)
