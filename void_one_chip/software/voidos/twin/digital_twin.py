from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from ..apis.gateway import VoidApiGateway
from ..kernel.capabilities import Capability


@dataclass(frozen=True)
class TwinReplayResult:
    ok: bool
    code: str
    step: int
    event_id: str
    detail: str = ""


class FullChipDigitalTwin:
    """Deterministic digital twin over platform + governed economy services."""

    def __init__(self, *, gateway: VoidApiGateway | None = None) -> None:
        self.gateway = gateway or VoidApiGateway()

    def snapshot(self) -> dict[str, Any]:
        return {
            "platform": self.gateway.platform.snapshot(),
            "treasury": self.gateway.treasury.snapshot(),
            "quest": self.gateway.quest.snapshot(),
            "legacy": self.gateway.legacy.snapshot(),
            "knowledge": self.gateway.knowledge.snapshot(),
            "governance": self.gateway.governance.snapshot(),
        }

    def state_digest(self) -> str:
        canonical = json.dumps(self.snapshot(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def replay_signed_intents(
        self,
        *,
        scenario: list[dict[str, Any]],
        cap: Capability,
        now_epoch_s: int,
    ) -> list[TwinReplayResult]:
        results: list[TwinReplayResult] = []
        for idx, item in enumerate(scenario, start=1):
            intent = self.gateway.build_intent(
                domain_id=str(item.get("domain", "")),
                subnet_scope=str(item.get("subnet_scope", "")),
                action=str(item.get("action", "")),
                payload=dict(item.get("payload", {})),
                signer_id=str(item.get("signer_id", "twin-operator")),
                nonce=str(item.get("nonce", f"twin-{idx}")),
            )
            out = self.gateway.dispatch(intent=intent, cap=cap, now_epoch_s=int(now_epoch_s))
            results.append(
                TwinReplayResult(
                    ok=out.ok,
                    code=out.code,
                    step=idx,
                    event_id=out.event_id,
                    detail=out.detail,
                )
            )
        return results
