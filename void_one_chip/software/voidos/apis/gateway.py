from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..hal.counter import MonotonicCounterAdapter
from ..kernel.capabilities import Capability
from ..services.governance_service import GovernanceService
from ..services.knowledge_service import KnowledgeLicensingService
from ..services.legacy_service import LegacyGraphService
from ..services.platform_service import PlatformBoardService
from ..services.quest_service import QuestService
from ..services.treasury_service import TreasurySettlementService
from .intent_adapter import PolicyBoundIntentAdapter, SignedIntent


@dataclass(frozen=True)
class GatewayResult:
    ok: bool
    code: str
    detail: str
    event_id: str = ""


class VoidApiGateway:
    """Policy-aware gateway for signed intent dispatch into governed services."""

    def __init__(self, *, adapter: PolicyBoundIntentAdapter | None = None) -> None:
        self._adapter = adapter or PolicyBoundIntentAdapter(shared_secret="void-default-secret")
        self._counter = MonotonicCounterAdapter()
        self.treasury = TreasurySettlementService()
        self.quest = QuestService()
        self.legacy = LegacyGraphService()
        self.knowledge = KnowledgeLicensingService()
        self.governance = GovernanceService()
        self.platform = PlatformBoardService()

    def build_intent(
        self,
        *,
        domain_id: str,
        subnet_scope: str,
        action: str,
        payload: dict[str, Any],
        signer_id: str,
        nonce: str,
    ) -> SignedIntent:
        ctr = self._counter.next(domain_id=domain_id, subnet_scope=subnet_scope)
        return self._adapter.build_intent(
            domain_id=domain_id,
            subnet_scope=subnet_scope,
            action=action,
            payload=payload,
            monotonic_counter=ctr,
            nonce=nonce,
            signer_id=signer_id,
        )

    def dispatch(self, *, intent: SignedIntent, cap: Capability, now_epoch_s: int) -> GatewayResult:
        decision = self._adapter.verify(intent)
        if not decision.ok:
            return GatewayResult(ok=False, code=decision.code, detail=decision.reason)

        payload = dict(intent.payload)
        event_id = intent.intent_id

        if intent.domain_id == "treasury" and intent.action == "settle":
            result = self.treasury.settle_governed(
                event_id=event_id,
                cap=cap,
                subnet_scope=intent.subnet_scope,
                now_epoch_s=now_epoch_s,
                src_subnet_id=int(payload.get("src_subnet_id", 0)),
                dst_subnet_id=int(payload.get("dst_subnet_id", 0)),
                tx_value=int(payload.get("tx_value", 0)),
                collapse_guard=bool(payload.get("collapse_guard", False)),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "treasury governed settlement",
                event_id=result.event_id,
            )

        if intent.domain_id == "quest" and intent.action == "claim":
            result = self.quest.claim_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                quest_id=str(payload.get("quest_id", "")),
                subject_id=str(payload.get("subject_id", "")),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "quest governed claim",
                event_id=result.event_id,
            )

        if intent.domain_id == "quest" and intent.action == "submit_proof":
            result = self.quest.submit_proof_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                quest_id=str(payload.get("quest_id", "")),
                proof_payload=dict(payload.get("proof_payload", {})),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "quest governed proof submission",
                event_id=result.event_id,
            )

        if intent.domain_id == "quest" and intent.action == "mark_settled":
            result = self.quest.mark_settled_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                quest_id=str(payload.get("quest_id", "")),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "quest governed settlement",
                event_id=result.event_id,
            )

        if intent.domain_id == "legacy" and intent.action == "append":
            result = self.legacy.append_event_governed(
                event_id=event_id,
                cap=cap,
                subnet_scope=intent.subnet_scope,
                now_epoch_s=now_epoch_s,
                subject_id=str(payload.get("subject_id", "")),
                subnet_id=str(payload.get("subnet_id", intent.subnet_scope)),
                quest_id=str(payload.get("quest_id", "")),
                impact_metrics=dict(payload.get("impact_metrics", {})),
                evidence_hashes=list(payload.get("evidence_hashes", [])),
                signer_set=list(payload.get("signer_set", [])),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "legacy governed append",
                event_id=result.event_id,
            )

        if intent.domain_id == "knowledge" and intent.action == "register":
            result = self.knowledge.register_artifact_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                artifact_id=str(payload.get("artifact_id", "")),
                subnet_scope=intent.subnet_scope,
                owner_id=str(payload.get("owner_id", "")),
                license_tier=str(payload.get("license_tier", "")),
                payload_hash=str(payload.get("payload_hash", "")),
                metadata=dict(payload.get("metadata", {})),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "knowledge governed registration",
                event_id=result.event_id,
            )

        if intent.domain_id == "knowledge" and intent.action == "grant":
            result = self.knowledge.grant_access_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                subnet_scope=intent.subnet_scope,
                artifact_id=str(payload.get("artifact_id", "")),
                subject_id=str(payload.get("subject_id", "")),
                requested_tier=str(payload.get("requested_tier", "")),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "knowledge governed grant",
                event_id=result.event_id,
            )

        if intent.domain_id == "governance" and intent.action == "vote":
            result = self.governance.cast_vote_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                proposal_id=str(payload.get("proposal_id", "")),
                subnet_scope=intent.subnet_scope,
                vote=str(payload.get("vote", "")),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "governance governed vote",
                event_id=result.event_id,
            )

        if intent.domain_id == "governance" and intent.action == "finalize":
            result = self.governance.finalize_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                proposal_id=str(payload.get("proposal_id", "")),
                subnet_scope=intent.subnet_scope,
                minimum_yes_votes=int(payload.get("minimum_yes_votes", 1)),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "governance governed finalize",
                event_id=result.event_id,
            )

        if intent.domain_id == "device" and intent.action == "register":
            result = self.platform.register_device_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                subnet_scope=intent.subnet_scope,
                device_id=str(payload.get("device_id", "")),
                device_class=str(payload.get("device_class", "")),
                metadata=dict(payload.get("metadata", {})),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "platform device registration",
                event_id=result.event_id,
            )

        if intent.domain_id == "device" and intent.action == "remove":
            result = self.platform.remove_device_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                subnet_scope=intent.subnet_scope,
                device_id=str(payload.get("device_id", "")),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "platform device removal",
                event_id=result.event_id,
            )

        if intent.domain_id == "power" and intent.action == "transition":
            result = self.platform.transition_power_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                subnet_scope=intent.subnet_scope,
                target_state=str(payload.get("target_state", "")),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "platform power transition",
                event_id=result.event_id,
            )

        if intent.domain_id == "memory" and intent.action == "write":
            result = self.platform.memory_write_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                subnet_scope=intent.subnet_scope,
                address=int(payload.get("address", 0)),
                value=int(payload.get("value", 0)),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "platform memory write",
                event_id=result.event_id,
            )

        if intent.domain_id == "memory" and intent.action == "read":
            result = self.platform.memory_read_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                subnet_scope=intent.subnet_scope,
                address=int(payload.get("address", 0)),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "platform memory read",
                event_id=result.event_id,
            )

        if intent.domain_id == "storage" and intent.action == "write":
            result = self.platform.storage_write_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                subnet_scope=intent.subnet_scope,
                block_id=int(payload.get("block_id", 0)),
                payload=str(payload.get("payload", "")),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "platform storage write",
                event_id=result.event_id,
            )

        if intent.domain_id == "storage" and intent.action == "read":
            result = self.platform.storage_read_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                subnet_scope=intent.subnet_scope,
                block_id=int(payload.get("block_id", 0)),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "platform storage read",
                event_id=result.event_id,
            )

        if intent.domain_id == "io" and intent.action == "emit":
            result = self.platform.io_emit_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                subnet_scope=intent.subnet_scope,
                endpoint_id=str(payload.get("endpoint_id", "")),
                payload=dict(payload.get("payload", {})),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "platform io emit",
                event_id=result.event_id,
            )

        if intent.domain_id == "io" and intent.action == "poll":
            result = self.platform.io_poll_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                subnet_scope=intent.subnet_scope,
                endpoint_id=str(payload.get("endpoint_id", "")),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "platform io poll",
                event_id=result.event_id,
            )

        if intent.domain_id == "network" and intent.action == "tx":
            result = self.platform.network_tx_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                subnet_scope=intent.subnet_scope,
                payload=dict(payload.get("payload", {})),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "platform network tx",
                event_id=result.event_id,
            )

        if intent.domain_id == "network" and intent.action == "rx":
            result = self.platform.network_rx_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                subnet_scope=intent.subnet_scope,
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "platform network rx",
                event_id=result.event_id,
            )

        if intent.domain_id == "peripheral" and intent.action == "command":
            result = self.platform.peripheral_command_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                subnet_scope=intent.subnet_scope,
                peripheral_id=str(payload.get("peripheral_id", "")),
                command=str(payload.get("command", "")),
                params=dict(payload.get("params", {})),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "platform peripheral command",
                event_id=result.event_id,
            )

        if intent.domain_id == "peripheral" and intent.action == "query":
            result = self.platform.peripheral_query_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                subnet_scope=intent.subnet_scope,
                peripheral_id=str(payload.get("peripheral_id", "")),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "platform peripheral query",
                event_id=result.event_id,
            )

        if intent.domain_id == "platform" and intent.action == "route_event":
            result = self.platform.route_event_governed(
                event_id=event_id,
                cap=cap,
                now_epoch_s=now_epoch_s,
                subnet_scope=intent.subnet_scope,
                source_domain=str(payload.get("source_domain", "")),
                action=str(payload.get("route_action", "")),
                payload=dict(payload.get("payload", {})),
                force_audit_fail=bool(payload.get("force_audit_fail", False)),
            )
            return GatewayResult(
                ok=result.ok,
                code=result.code,
                detail=result.detail or "platform route event",
                event_id=result.event_id,
            )

        return GatewayResult(
            ok=False,
            code="E_POLICY_BLOCKED",
            detail=f"unsupported route: {intent.domain_id}/{intent.action}",
            event_id=event_id,
        )
