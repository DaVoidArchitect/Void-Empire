from __future__ import annotations

from dataclasses import dataclass


ERROR_CODES = {
    "OK",
    "E_CAP_INVALID",
    "E_CAP_EXPIRED",
    "E_SCOPE_VIOLATION",
    "E_POLICY_BLOCKED",
    "E_PROOF_INVALID",
    "E_LEDGER_CONFLICT",
    "E_AUDIT_COMMIT_FAILED",
    "E_COUNTER_REPLAY",
    "E_DEVICE_NOT_FOUND",
}


@dataclass(frozen=True)
class ApiResponse:
    ok: bool
    code: str
    message: str = ""


def validate_response(resp: ApiResponse) -> tuple[bool, str]:
    if resp.code not in ERROR_CODES:
        return (False, "unknown error code")
    if resp.ok and resp.code != "OK":
        return (False, "ok response must use code OK")
    if (not resp.ok) and resp.code == "OK":
        return (False, "error response cannot use code OK")
    return (True, "OK")
