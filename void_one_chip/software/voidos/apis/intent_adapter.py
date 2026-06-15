from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SignedIntent:
    intent_id: str
    domain_id: str
    subnet_scope: str
    action: str
    payload: dict[str, Any]
    monotonic_counter: int
    nonce: str
    signer_id: str
    signature: str


@dataclass(frozen=True)
class IntentDecision:
    ok: bool
    code: str
    reason: str


class PolicyBoundIntentAdapter:
    """Creates and verifies signed, policy-bound intent envelopes."""

    def __init__(self, *, shared_secret: str, allowed_domains: set[str] | None = None) -> None:
        self._shared_secret = str(shared_secret).encode("utf-8")
        self._allowed_domains = set(
            allowed_domains
            or {
                "treasury",
                "quest",
                "legacy",
                "knowledge",
                "governance",
                "device",
                "power",
                "memory",
                "storage",
                "io",
                "network",
                "peripheral",
                "platform",
            }
        )
        self._seen_nonces: set[str] = set()

    def _canonical_body(
        self,
        *,
        intent_id: str,
        domain_id: str,
        subnet_scope: str,
        action: str,
        payload: dict[str, Any],
        monotonic_counter: int,
        nonce: str,
        signer_id: str,
    ) -> str:
        body = {
            "intent_id": str(intent_id),
            "domain_id": str(domain_id),
            "subnet_scope": str(subnet_scope),
            "action": str(action),
            "payload": dict(payload),
            "monotonic_counter": int(monotonic_counter),
            "nonce": str(nonce),
            "signer_id": str(signer_id),
        }
        return json.dumps(body, sort_keys=True, separators=(",", ":"))

    def _sign(self, canonical_body: str) -> str:
        return hmac.new(self._shared_secret, canonical_body.encode("utf-8"), hashlib.sha256).hexdigest()

    def build_intent(
        self,
        *,
        domain_id: str,
        subnet_scope: str,
        action: str,
        payload: dict[str, Any],
        monotonic_counter: int,
        nonce: str,
        signer_id: str,
    ) -> SignedIntent:
        canonical = self._canonical_body(
            intent_id=f"{domain_id}:{subnet_scope}:{monotonic_counter}:{nonce}",
            domain_id=domain_id,
            subnet_scope=subnet_scope,
            action=action,
            payload=payload,
            monotonic_counter=monotonic_counter,
            nonce=nonce,
            signer_id=signer_id,
        )
        signature = self._sign(canonical)
        body = json.loads(canonical)
        return SignedIntent(
            intent_id=str(body["intent_id"]),
            domain_id=str(body["domain_id"]),
            subnet_scope=str(body["subnet_scope"]),
            action=str(body["action"]),
            payload=dict(body["payload"]),
            monotonic_counter=int(body["monotonic_counter"]),
            nonce=str(body["nonce"]),
            signer_id=str(body["signer_id"]),
            signature=signature,
        )

    def verify(self, intent: SignedIntent) -> IntentDecision:
        if intent.domain_id not in self._allowed_domains:
            return IntentDecision(ok=False, code="E_POLICY_BLOCKED", reason="domain not allowed by adapter policy")

        canonical = self._canonical_body(
            intent_id=intent.intent_id,
            domain_id=intent.domain_id,
            subnet_scope=intent.subnet_scope,
            action=intent.action,
            payload=intent.payload,
            monotonic_counter=intent.monotonic_counter,
            nonce=intent.nonce,
            signer_id=intent.signer_id,
        )
        expected = self._sign(canonical)
        if not hmac.compare_digest(expected, intent.signature):
            return IntentDecision(ok=False, code="E_POLICY_BLOCKED", reason="signature mismatch")

        nonce_key = f"{intent.signer_id}:{intent.nonce}"
        if nonce_key in self._seen_nonces:
            return IntentDecision(ok=False, code="E_COUNTER_REPLAY", reason="intent nonce replay detected")
        self._seen_nonces.add(nonce_key)

        return IntentDecision(ok=True, code="OK", reason="verified")
