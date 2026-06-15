from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    cap_id: str
    subject_id: str
    rights_mask: frozenset[str]
    subnet_scope: str
    policy_hash: str
    expires_at: int


class CapabilityGuard:
    """Least-privilege capability checker for privileged operations."""

    def validate(
        self,
        cap: Capability,
        *,
        required_right: str,
        subnet_scope: str,
        now_epoch_s: int,
    ) -> tuple[bool, str]:
        if now_epoch_s > int(cap.expires_at):
            return (False, "E_CAP_EXPIRED")
        if str(subnet_scope) != str(cap.subnet_scope):
            return (False, "E_SCOPE_VIOLATION")
        if required_right not in cap.rights_mask:
            return (False, "E_POLICY_BLOCKED")
        return (True, "OK")
