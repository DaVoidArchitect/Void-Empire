from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MailboxResult:
    ok: bool
    code: str
    receipt_id: str
    reason: str = ""


class MailboxDriver:
    """Deterministic mailbox adapter with anti-replay semantics."""

    def __init__(self) -> None:
        self._seen_receipt_ids: set[str] = set()

    def submit_intent(self, envelope: dict[str, Any]) -> MailboxResult:
        payload = json.dumps(envelope, sort_keys=True, separators=(",", ":"))
        receipt_id = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        if receipt_id in self._seen_receipt_ids:
            return MailboxResult(
                ok=False,
                code="E_COUNTER_REPLAY",
                receipt_id=receipt_id,
                reason="replayed envelope",
            )

        self._seen_receipt_ids.add(receipt_id)
        return MailboxResult(ok=True, code="OK", receipt_id=receipt_id)

    def snapshot(self) -> dict[str, Any]:
        return {
            "seen_receipt_count": len(self._seen_receipt_ids),
            "seen_receipt_ids": sorted(self._seen_receipt_ids),
        }
