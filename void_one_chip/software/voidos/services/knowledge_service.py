from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ..kernel.capabilities import Capability
from ..kernel.mutation_coordinator import MutationCoordinator


@dataclass(frozen=True)
class KnowledgeArtifact:
    artifact_id: str
    subnet_scope: str
    owner_id: str
    license_tier: str
    payload_hash: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class KnowledgeAccessDecision:
    ok: bool
    code: str
    committed: bool
    event_id: str
    artifact_id: str
    detail: str = ""


@dataclass(frozen=True)
class KnowledgeRegistrationDecision:
    ok: bool
    code: str
    committed: bool
    event_id: str
    artifact: KnowledgeArtifact | None
    detail: str = ""


class KnowledgeLicensingService:
    """Scoped knowledge artifact registration and access grant service."""

    def __init__(self, *, coordinator: MutationCoordinator | None = None) -> None:
        self._coordinator = coordinator or MutationCoordinator()
        self._artifacts: dict[str, KnowledgeArtifact] = {}
        self._grants: dict[tuple[str, str], set[str]] = {}

    @property
    def committed_state(self) -> dict[str, dict[str, object]]:
        return self._coordinator.committed_state

    def snapshot(self) -> dict[str, Any]:
        return {
            "artifacts": {
                artifact_id: asdict(artifact)
                for artifact_id, artifact in sorted(self._artifacts.items())
            },
            "grants": {
                f"{artifact_id}:{subject_id}": sorted(tiers)
                for (artifact_id, subject_id), tiers in sorted(self._grants.items())
            },
            "coordinator": self._coordinator.snapshot(),
        }

    def register_artifact(
        self,
        *,
        artifact_id: str,
        subnet_scope: str,
        owner_id: str,
        license_tier: str,
        payload_hash: str,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeArtifact:
        artifact = KnowledgeArtifact(
            artifact_id=str(artifact_id),
            subnet_scope=str(subnet_scope),
            owner_id=str(owner_id),
            license_tier=str(license_tier),
            payload_hash=str(payload_hash),
            metadata=dict(metadata or {}),
        )
        self._artifacts[artifact.artifact_id] = artifact
        return artifact

    def register_artifact_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        artifact_id: str,
        subnet_scope: str,
        owner_id: str,
        license_tier: str,
        payload_hash: str,
        metadata: dict[str, Any] | None = None,
        force_audit_fail: bool = False,
    ) -> KnowledgeRegistrationDecision:
        artifact_key = str(artifact_id)
        if artifact_key in self._artifacts:
            return KnowledgeRegistrationDecision(
                ok=False,
                code="E_LEDGER_CONFLICT",
                committed=False,
                event_id=str(event_id),
                artifact=None,
                detail="artifact already exists",
            )

        staged_delta = {
            "domain": "knowledge",
            "action": "register_artifact",
            "artifact_id": artifact_key,
            "subnet_scope": str(subnet_scope),
            "owner_id": str(owner_id),
            "license_tier": str(license_tier),
            "payload_hash": str(payload_hash),
            "metadata": dict(metadata or {}),
        }
        mutation = self._coordinator.commit(
            event_id=str(event_id),
            cap=cap,
            required_right="KNOWLEDGE_REGISTER",
            subnet_scope=str(subnet_scope),
            now_epoch_s=int(now_epoch_s),
            staged_delta=staged_delta,
            force_audit_fail=bool(force_audit_fail),
        )
        if not mutation.ok:
            return KnowledgeRegistrationDecision(
                ok=False,
                code=mutation.code,
                committed=False,
                event_id=mutation.event_id,
                artifact=None,
                detail=mutation.detail,
            )

        artifact = self.register_artifact(
            artifact_id=artifact_key,
            subnet_scope=str(subnet_scope),
            owner_id=str(owner_id),
            license_tier=str(license_tier),
            payload_hash=str(payload_hash),
            metadata=dict(metadata or {}),
        )
        return KnowledgeRegistrationDecision(
            ok=True,
            code="OK",
            committed=True,
            event_id=mutation.event_id,
            artifact=artifact,
        )

    def artifact(self, artifact_id: str) -> KnowledgeArtifact | None:
        return self._artifacts.get(str(artifact_id))

    def grant_access_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        now_epoch_s: int,
        subnet_scope: str,
        artifact_id: str,
        subject_id: str,
        requested_tier: str,
        force_audit_fail: bool = False,
    ) -> KnowledgeAccessDecision:
        artifact = self._artifacts.get(str(artifact_id))
        if artifact is None:
            return KnowledgeAccessDecision(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                artifact_id=str(artifact_id),
                detail="artifact not found",
            )
        if str(artifact.subnet_scope) != str(subnet_scope):
            return KnowledgeAccessDecision(
                ok=False,
                code="E_SCOPE_VIOLATION",
                committed=False,
                event_id=str(event_id),
                artifact_id=str(artifact_id),
                detail="artifact subnet scope mismatch",
            )
        if str(requested_tier) != str(artifact.license_tier):
            return KnowledgeAccessDecision(
                ok=False,
                code="E_POLICY_BLOCKED",
                committed=False,
                event_id=str(event_id),
                artifact_id=str(artifact_id),
                detail="requested tier does not match artifact license",
            )

        staged_delta = {
            "domain": "knowledge",
            "action": "grant_access",
            "artifact_id": str(artifact_id),
            "subject_id": str(subject_id),
            "requested_tier": str(requested_tier),
            "subnet_scope": str(subnet_scope),
            "payload_hash": str(artifact.payload_hash),
        }
        mutation = self._coordinator.commit(
            event_id=str(event_id),
            cap=cap,
            required_right="KNOWLEDGE_GRANT",
            subnet_scope=str(subnet_scope),
            now_epoch_s=int(now_epoch_s),
            staged_delta=staged_delta,
            force_audit_fail=bool(force_audit_fail),
        )
        if not mutation.ok:
            return KnowledgeAccessDecision(
                ok=False,
                code=mutation.code,
                committed=False,
                event_id=mutation.event_id,
                artifact_id=str(artifact_id),
                detail=mutation.detail,
            )

        key = (str(artifact_id), str(subject_id))
        tiers = self._grants.setdefault(key, set())
        tiers.add(str(requested_tier))

        return KnowledgeAccessDecision(
            ok=True,
            code="OK",
            committed=True,
            event_id=mutation.event_id,
            artifact_id=str(artifact_id),
        )

    def check_access(self, *, artifact_id: str, subject_id: str, required_tier: str) -> tuple[bool, str]:
        artifact = self._artifacts.get(str(artifact_id))
        if artifact is None:
            return (False, "E_POLICY_BLOCKED")

        tiers = self._grants.get((str(artifact_id), str(subject_id)), set())
        if str(required_tier) not in tiers:
            return (False, "E_POLICY_BLOCKED")
        return (True, "OK")
