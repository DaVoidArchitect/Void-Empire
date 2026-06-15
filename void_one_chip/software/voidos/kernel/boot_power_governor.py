from __future__ import annotations

from dataclasses import dataclass


LEGAL_TRANSITIONS: dict[str, set[str]] = {
    "OFF": {"BOOTSTRAP"},
    "BOOTSTRAP": {"READY", "DEGRADED"},
    "READY": {"DEGRADED", "SHUTDOWN"},
    "DEGRADED": {"RECOVERY", "SHUTDOWN"},
    "RECOVERY": {"READY", "DEGRADED", "SHUTDOWN"},
    "SHUTDOWN": {"OFF"},
}


@dataclass(frozen=True)
class PowerTransitionResult:
    ok: bool
    code: str
    from_state: str
    to_state: str
    reason: str = ""


class BootPowerGovernor:
    """Deterministic legal-transition governor for boot/power lifecycle."""

    def __init__(self) -> None:
        self._state = "OFF"
        self._history: list[str] = [self._state]

    @property
    def state(self) -> str:
        return self._state

    @property
    def history(self) -> list[str]:
        return list(self._history)

    def can_transition(self, *, target_state: str) -> bool:
        tgt = str(target_state).upper()
        legal_targets = LEGAL_TRANSITIONS.get(self._state, set())
        return tgt in legal_targets

    def transition(self, *, target_state: str) -> PowerTransitionResult:
        tgt = str(target_state).upper()
        if tgt not in LEGAL_TRANSITIONS.get(self._state, set()):
            return PowerTransitionResult(
                ok=False,
                code="E_POLICY_BLOCKED",
                from_state=self._state,
                to_state=tgt,
                reason="illegal power-state transition",
            )

        prev = self._state
        self._state = tgt
        self._history.append(self._state)
        return PowerTransitionResult(ok=True, code="OK", from_state=prev, to_state=tgt)
