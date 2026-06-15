from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class JournalRecord:
    event_id: str
    digest_prev: str
    digest_curr: str
    payload: dict[str, Any]


class DeterministicEventJournal:
    """Append-only deterministic event journal with hash chaining."""

    def __init__(self) -> None:
        self._records: list[JournalRecord] = []
        self._event_ids: set[str] = set()
        self._head: str = "GENESIS"

    @property
    def head(self) -> str:
        return self._head

    @property
    def records(self) -> list[JournalRecord]:
        return list(self._records)

    def append(self, *, event_id: str, payload: dict[str, Any], force_fail: bool = False) -> tuple[bool, str]:
        event_id = str(event_id)
        if event_id in self._event_ids:
            return (False, "E_COUNTER_REPLAY")
        if force_fail:
            return (False, "E_AUDIT_COMMIT_FAILED")

        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest_curr = hashlib.sha256(f"{self._head}|{event_id}|{canonical}".encode("utf-8")).hexdigest()

        record = JournalRecord(
            event_id=event_id,
            digest_prev=self._head,
            digest_curr=digest_curr,
            payload=payload,
        )
        self._records.append(record)
        self._event_ids.add(event_id)
        self._head = digest_curr
        return (True, "OK")

    def snapshot(self) -> dict[str, Any]:
        return {
            "head": str(self._head),
            "record_count": len(self._records),
            "records": [
                {
                    "event_id": r.event_id,
                    "digest_prev": r.digest_prev,
                    "digest_curr": r.digest_curr,
                    "payload": dict(r.payload),
                }
                for r in self._records
            ],
        }
