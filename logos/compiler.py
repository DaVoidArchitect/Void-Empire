"""
Logos Compiler (logosc) — Declarative State Machine Compiler

Compiles a Logos AST into a verified JSON State Machine Intermediate
Representation (SMIR). The compiler is responsible for:

1.  **SI Normalisation**: All resource quantities are normalised to base SI
    units (kg, J, J/K, cycles) at compile time.
2.  **Import DAG Resolution**: Imported files are parsed and merged, with a
    strict acyclic dependency check to prevent circular imports.
3.  **Thermodynamic Verification**: Every intent's ``require`` block is
    verified against the provided ``mesh_context`` *before* SMIR emission.
    Constraint bounds are encoded into the SMIR for runtime enforcement.
4.  **Atomic Transition Requirements**: Transition-level resource requirements
    are verified against the mesh *at compile time* for initial feasibility.

The compiler emits a ``dict`` that constitutes the complete JSON SMIR or
raises ``ThermodynamicConstraintError`` / ``LogosSyntaxError`` on failure.
"""

from __future__ import annotations

import os
from typing import Any

from .lexer import tokenize
from .logos_ast import (
    ProgramNode, ImportNode, IntentNode,
    RequireNode, ConstraintBlockNode, ResourceDeclNode, ConstraintNode,
    StateNode, TransitionNode, GuardNode,
    BinaryOpNode, UnaryOpNode, LiteralNode,
)
from .parser import Parser
from .exceptions import LogosSyntaxError, ThermodynamicConstraintError


# ---------------------------------------------------------------------------
# SI normalisation tables
# ---------------------------------------------------------------------------

_SI_MASS = {
    'kg': 1.0,
    'g': 0.001,
    'mg': 1e-6,
    't': 1000.0,
}

_SI_ENERGY = {
    'J': 1.0,
    'kJ': 1000.0,
    'Wh': 3600.0,
    'kWh': 3_600_000.0,
    'MWh': 3_600_000_000.0,
}

_SI_TIME = {
    's': 1.0,
    'seconds': 1.0,
    'm': 60.0,
    'minutes': 60.0,
    'h': 3600.0,
    'hours': 3600.0,
    'd': 86400.0,
    'days': 86400.0,
}

_SI_ENTROPY = {
    '': 1.0,    # default: J/K
}

_SI_CYCLE = {
    '': 1.0,
    'cycles': 1.0,
}

_SI_TABLES = {
    'mass': ('kg', _SI_MASS),
    'energy': ('J', _SI_ENERGY),
    'entropy': ('J/K', _SI_ENTROPY),
    'cycle': ('cycles', _SI_CYCLE),
}


def normalise_resource(resource: str, value: float, unit: str, line: int) -> tuple[float, str]:
    """Normalise *value* to the base SI unit for *resource*."""
    if resource not in _SI_TABLES:
        raise LogosSyntaxError(f"Unknown resource primitive '{resource}'", line, -1)

    base_unit, table = _SI_TABLES[resource]

    # Accept unitless quantities for entropy/cycle
    if unit == '' and resource in ('entropy', 'cycle'):
        return (value, base_unit)

    # Time-based units for cycle durations
    if resource == 'cycle' and unit in _SI_TIME:
        return (value * _SI_TIME[unit], 's')

    if unit not in table:
        raise LogosSyntaxError(f"Unknown unit '{unit}' for resource '{resource}'", line, -1)

    return (value * table[unit], base_unit)


# ---------------------------------------------------------------------------
# DAG Import Resolution
# ---------------------------------------------------------------------------

def resolve_imports(
    program: ProgramNode,
    source_path: str = "<stdin>",
    _visited: set[str] | None = None,
) -> ProgramNode:
    """
    Recursively resolve ``import`` directives, merging imported intents
    into the root program.  Raises on cyclic dependencies.
    """
    if _visited is None:
        _visited = set()

    abs_source = os.path.abspath(source_path)
    if abs_source in _visited:
        raise LogosSyntaxError(
            f"Cyclic import detected: '{source_path}' has already been imported.",
            -1, -1,
        )
    _visited.add(abs_source)

    merged_intents: list[IntentNode] = []

    for imp in program.imports:
        # Resolve relative to the importing file's directory
        base_dir = os.path.dirname(abs_source) if os.path.isfile(abs_source) else os.getcwd()
        imp_path = os.path.normpath(os.path.join(base_dir, imp.path))

        if not os.path.isfile(imp_path):
            raise LogosSyntaxError(f"Import target not found: '{imp.path}'", imp.line, -1)

        with open(imp_path, 'r', encoding='utf-8') as f:
            imported_code = f.read()

        imported_tokens = tokenize(imported_code)
        imported_program = Parser(imported_tokens).parse()
        # Recurse into imported file
        imported_program = resolve_imports(imported_program, imp_path, _visited)
        merged_intents.extend(imported_program.intents)

    # Root intents come *after* imported ones (import-first ordering)
    merged_intents.extend(program.intents)
    return ProgramNode([], merged_intents)


# ---------------------------------------------------------------------------
# Compiler
# ---------------------------------------------------------------------------

class Compiler:
    """
    Compiles a Logos ProgramNode into a JSON State Machine IR (SMIR).

    The ``mesh_context`` dictionary supplies the physical resources available
    to the deployment mesh.  Example::

        mesh_context = {
            "mass":    5000.0,   # kg
            "energy":  10000.0,  # J
            "entropy": 500.0,    # J/K
            "cycle":   100.0,    # cycles
        }
    """

    def __init__(self, mesh_context: dict[str, float]):
        self.mesh = dict(mesh_context)   # shallow copy — never mutate the caller's dict

    def compile(self, program: ProgramNode) -> dict:
        """Compile and verify the program, returning the SMIR dict."""
        compiled_intents = []

        for intent in program.intents:
            compiled_intents.append(self._compile_intent(intent))

        return {
            "logos_version": "2.0-declarative",
            "intents": compiled_intents,
        }

    # ------------------------------------------------------------------
    # Intent compilation
    # ------------------------------------------------------------------

    def _compile_intent(self, intent: IntentNode) -> dict:
        # 1. Normalise and verify require block
        norm_requirements = []
        if intent.require_block:
            for r in intent.require_block.requirements:
                norm_val, norm_unit = normalise_resource(r.resource, r.value, r.unit, r.line)
                self._verify_resource(r.resource, norm_val, norm_unit, r.line)
                norm_requirements.append({
                    "resource": r.resource,
                    "value": norm_val,
                    "unit": norm_unit,
                })

        # 2. Normalise and encode constraints
        norm_constraints = []
        if intent.constraint_block:
            for c in intent.constraint_block.constraints:
                norm_val, norm_unit = normalise_resource(c.resource, c.value, c.unit, c.line)
                norm_constraints.append({
                    "resource": c.resource,
                    "operator": c.operator,
                    "value": norm_val,
                    "unit": norm_unit,
                })

        # 3. Compile state machines
        compiled_states = []
        for state in intent.states:
            compiled_states.append(self._compile_state(state))

        return {
            "name": intent.name,
            "headers": intent.headers,
            "requirements": norm_requirements,
            "constraints": norm_constraints,
            "states": compiled_states,
        }

    # ------------------------------------------------------------------
    # State & transition compilation
    # ------------------------------------------------------------------

    def _compile_state(self, state: StateNode) -> dict:
        compiled_transitions = []
        for trans in state.transitions:
            compiled_transitions.append(self._compile_transition(trans))

        return {
            "name": state.name,
            "transitions": compiled_transitions,
        }

    def _compile_transition(self, trans: TransitionNode) -> dict:
        # Normalise and verify transition-level requirements
        norm_trans_reqs = []
        for r in trans.transition_requires:
            norm_val, norm_unit = normalise_resource(r.resource, r.value, r.unit, r.line)
            self._verify_resource(r.resource, norm_val, norm_unit, r.line)
            norm_trans_reqs.append({
                "resource": r.resource,
                "value": norm_val,
                "unit": norm_unit,
            })

        compiled = {
            "event": trans.event,
            "target": trans.target,
            "line": trans.line,
        }

        if trans.guard:
            compiled["guard"] = self._compile_guard(trans.guard)
        if norm_trans_reqs:
            compiled["requires"] = norm_trans_reqs

        return compiled

    def _compile_guard(self, guard: GuardNode) -> dict:
        return {"expr": self._compile_expr(guard.expr)}

    def _compile_expr(self, node) -> dict:
        if isinstance(node, BinaryOpNode):
            return {
                "type": "binary",
                "op": node.op,
                "left": self._compile_expr(node.left),
                "right": self._compile_expr(node.right),
            }
        elif isinstance(node, UnaryOpNode):
            return {
                "type": "unary",
                "op": node.op,
                "expr": self._compile_expr(node.expr),
            }
        elif isinstance(node, LiteralNode):
            return {
                "type": "literal",
                "value_type": node.type,
                "value": node.value,
            }
        else:
            raise LogosSyntaxError(
                f"Unsupported expression node in guard: {type(node).__name__}", -1, -1
            )

    # ------------------------------------------------------------------
    # Thermodynamic verification (compile-time mesh check)
    # ------------------------------------------------------------------

    def _verify_resource(self, resource: str, norm_value: float, norm_unit: str, line: int):
        """Verify that the mesh has sufficient capacity for *norm_value*."""
        available = self.mesh.get(resource, 0.0)
        if norm_value > available:
            raise ThermodynamicConstraintError(
                constraint_type=resource,
                required_value=norm_value,
                required_unit=norm_unit,
                available_value=available,
                available_unit=norm_unit,
                line=line,
                details=f"Intent requires {norm_value} {norm_unit} of {resource}, "
                        f"but the mesh only provides {available} {norm_unit}.",
            )
