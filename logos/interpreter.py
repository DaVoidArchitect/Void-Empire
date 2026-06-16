"""
Logos VM — Declarative State Machine Virtual Machine

Executes a compiled SMIR (State Machine Intermediate Representation) by
processing event streams against the state machine graph. The VM enforces:

1.  **Atomic State Rollover**: Before committing *any* transition, the VM
    reads *all* localized resource requirements into a provisional deduction
    set.  If *every* requirement can be satisfied, the deductions are
    applied atomically.  If *any single* requirement fails, **no** resource
    is deducted and the transition is frozen (blocked).
2.  **Guard Evaluation**: Guard expressions are evaluated against a runtime
    context dictionary.  A transition is only eligible if its guard
    evaluates to True (or has no guard).
3.  **Constraint Enforcement**: Operating constraints (max/min) are checked
    *after* provisional deduction to ensure bounds are not violated.
"""

from __future__ import annotations

import copy
from typing import Any

from .exceptions import ThermodynamicConstraintError, LogosRuntimeError


class LogosVM:
    """
    Executes a compiled Logos SMIR.

    Parameters
    ----------
    smir : dict
        The compiled State Machine IR emitted by the Compiler.
    mesh_context : dict[str, float]
        Live resource pool that the VM will deduct from during execution.
    runtime_context : dict[str, Any] | None
        Key-value context for evaluating guard expressions (e.g.,
        ``{"priority": 5, "approved": True}``).
    """

    def __init__(
        self,
        smir: dict | bytes,
        mesh_context: dict[str, float],
        runtime_context: dict[str, Any] | None = None,
    ):
        if isinstance(smir, bytes):
            from .vsmb import decode_vsmb
            smir = decode_vsmb(smir)
        self.smir = smir
        self.mesh = dict(mesh_context)  # working copy — will be mutated
        self.runtime_ctx = runtime_context or {}

        # Per-intent execution state
        self._intent_states: dict[str, str] = {}  # intent_name -> current_state_name
        self._intent_lookup: dict[str, dict] = {}  # intent_name -> compiled intent dict
        self._state_lookup: dict[str, dict[str, dict]] = {}  # intent -> {state_name: state_dict}

        # Event log (audit trail)
        self.event_log: list[dict] = []

        self._initialise()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _initialise(self):
        for intent in self.smir.get("intents", []):
            name = intent["name"]
            self._intent_lookup[name] = intent

            states = intent.get("states", [])
            state_map = {s["name"]: s for s in states}
            self._state_lookup[name] = state_map

            # First declared state is the initial state
            if states:
                self._intent_states[name] = states[0]["name"]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def current_state(self, intent_name: str) -> str:
        """Return the current state of an intent."""
        return self._intent_states.get(intent_name, "<undefined>")

    def send_event(self, intent_name: str, event: str) -> dict:
        """
        Send an *event* to the named intent's state machine.

        Returns a result dictionary::

            {
                "status": "transitioned" | "blocked" | "no_match",
                "from": "...",
                "to": "...",
                "event": "...",
                "detail": "...",
            }
        """
        if intent_name not in self._intent_lookup:
            raise LogosRuntimeError(f"Unknown intent: '{intent_name}'")

        current_state_name = self._intent_states[intent_name]
        state_dict = self._state_lookup[intent_name].get(current_state_name)

        if not state_dict:
            return self._log_result(intent_name, event, current_state_name, current_state_name,
                                    "no_match", "Current state has no definition.")

        for trans in state_dict.get("transitions", []):
            if trans["event"] != event:
                continue

            # 1. Evaluate guard (if any)
            if "guard" in trans:
                if not self._eval_guard(trans["guard"]):
                    continue  # guard failed — try next matching transition

            # 2. Atomic resource deduction check
            requires = trans.get("requires", [])
            if requires:
                success, detail = self._atomic_deduct(requires, trans.get("line", -1))
                if not success:
                    return self._log_result(
                        intent_name, event, current_state_name, trans["target"],
                        "blocked", detail,
                    )

            # 3. Constraint enforcement (post-deduction bounds check)
            intent_dict = self._intent_lookup[intent_name]
            constraints = intent_dict.get("constraints", [])
            if constraints:
                violation = self._check_constraints(constraints)
                if violation:
                    # Rollback the deduction we just made
                    for req in requires:
                        self.mesh[req["resource"]] = self.mesh.get(req["resource"], 0.0) + req["value"]
                    return self._log_result(
                        intent_name, event, current_state_name, trans["target"],
                        "blocked", f"Constraint violation: {violation}",
                    )

            # 4. Commit transition
            self._intent_states[intent_name] = trans["target"]
            return self._log_result(
                intent_name, event, current_state_name, trans["target"],
                "transitioned", "OK",
            )

        # No matching transition found
        return self._log_result(
            intent_name, event, current_state_name, current_state_name,
            "no_match", f"No transition for event '{event}' in state '{current_state_name}'.",
        )

    # ------------------------------------------------------------------
    # Atomic resource deduction
    # ------------------------------------------------------------------

    def _atomic_deduct(self, requires: list[dict], line: int) -> tuple[bool, str]:
        """
        Check *all* requirements against the mesh in a read-only pass.
        If all pass, apply deductions atomically.
        If any fail, return without modifying the mesh.
        """
        # Phase 1: Read-only verification
        for req in requires:
            resource = req["resource"]
            needed = req["value"]
            available = self.mesh.get(resource, 0.0)
            if needed > available:
                deficit = needed - available
                return (
                    False,
                    f"Insufficient {resource}: need {needed} {req['unit']}, "
                    f"have {available} {req['unit']} (deficit: {deficit} {req['unit']}). "
                    f"Transition FROZEN — no resources deducted.",
                )

        # Phase 2: Commit deductions atomically
        for req in requires:
            self.mesh[req["resource"]] -= req["value"]

        return (True, "")

    # ------------------------------------------------------------------
    # Constraint checking (post-deduction bounds)
    # ------------------------------------------------------------------

    def _check_constraints(self, constraints: list[dict]) -> str | None:
        """
        Verify operating constraints are still within bounds *after*
        a deduction.  Returns an error string on violation, None on success.
        """
        for c in constraints:
            resource = c["resource"]
            op = c["operator"]
            limit = c["value"]
            current = self.mesh.get(resource, 0.0)

            violated = False
            if op == 'max' and current > limit:
                violated = True
            elif op == 'min' and current < limit:
                violated = True
            elif op == '<' and not (current < limit):
                violated = True
            elif op == '>' and not (current > limit):
                violated = True
            elif op == '<=' and not (current <= limit):
                violated = True
            elif op == '>=' and not (current >= limit):
                violated = True
            elif op == '==' and not (current == limit):
                violated = True
            elif op == '!=' and not (current != limit):
                violated = True

            if violated:
                return (
                    f"{resource} constraint '{op} {limit} {c['unit']}' violated. "
                    f"Current mesh value: {current} {c['unit']}."
                )
        return None

    # ------------------------------------------------------------------
    # Guard evaluation
    # ------------------------------------------------------------------

    def _eval_guard(self, guard: dict) -> bool:
        """Evaluate a compiled guard expression against the runtime context."""
        result = self._eval_expr(guard["expr"])
        return bool(result)

    def _eval_expr(self, node: dict) -> Any:
        """Recursively evaluate a compiled expression node."""
        ntype = node["type"]

        if ntype == "literal":
            vtype = node["value_type"]
            val = node["value"]
            if vtype == 'IDENTIFIER':
                return self.runtime_ctx.get(val, 0)
            elif vtype == 'NUMBER':
                return val
            elif vtype == 'PERCENT':
                return val / 100.0
            elif vtype == 'STRING':
                return val
            return val

        elif ntype == "binary":
            left = self._eval_expr(node["left"])
            right = self._eval_expr(node["right"])
            op = node["op"]

            if op == '+':     return left + right
            elif op == '-':   return left - right
            elif op == '*':   return left * right
            elif op == '/':   return left / right if right != 0 else 0
            elif op == '<':   return left < right
            elif op == '>':   return left > right
            elif op == '<=':  return left <= right
            elif op == '>=':  return left >= right
            elif op == '==':  return left == right
            elif op == '!=':  return left != right
            elif op == 'and': return left and right
            elif op == 'or':  return left or right
            else:
                raise LogosRuntimeError(f"Unknown binary operator: {op}")

        elif ntype == "unary":
            val = self._eval_expr(node["expr"])
            op = node["op"]
            if op == 'not':  return not val
            elif op == '-':  return -val
            else:
                raise LogosRuntimeError(f"Unknown unary operator: {op}")

        raise LogosRuntimeError(f"Unknown expression node type: {ntype}")

    # ------------------------------------------------------------------
    # Audit log
    # ------------------------------------------------------------------

    def _log_result(
        self, intent: str, event: str, from_state: str, to_state: str,
        status: str, detail: str,
    ) -> dict:
        result = {
            "intent": intent,
            "event": event,
            "from": from_state,
            "to": to_state,
            "status": status,
            "detail": detail,
            "mesh_snapshot": dict(self.mesh),
        }
        self.event_log.append(result)
        return result
