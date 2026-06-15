"""
Logos AST — Pure Declarative Abstract Syntax Tree

All nodes represent immutable declarations.  There are no procedural
statement nodes (no variables, no assignments, no conditionals, no loops).
The AST describes intents, resource requirements, constraints, state
machines, guarded transitions, and import directives.
"""

from __future__ import annotations
from typing import Any


class ASTNode:
    """Base class for all Logos AST nodes."""
    pass


# ---------------------------------------------------------------------------
# Top-level nodes
# ---------------------------------------------------------------------------

class ProgramNode(ASTNode):
    """Root node containing imports and intent definitions."""
    def __init__(self, imports: list[ImportNode], intents: list[IntentNode]):
        self.imports = imports
        self.intents = intents

    def __repr__(self) -> str:
        return f"ProgramNode(imports={self.imports}, intents={self.intents})"


class ImportNode(ASTNode):
    """An import directive: ``import "path/to/file.logos";``"""
    def __init__(self, path: str, line: int):
        self.path = path
        self.line = line

    def __repr__(self) -> str:
        return f'ImportNode("{self.path}", Line {self.line})'


# ---------------------------------------------------------------------------
# Intent structure
# ---------------------------------------------------------------------------

class IntentNode(ASTNode):
    """An intent definition block."""
    def __init__(
        self,
        name: str,
        headers: dict[str, Any],
        require_block: RequireNode | None,
        constraint_block: ConstraintBlockNode | None,
        states: list[StateNode],
    ):
        self.name = name
        self.headers = headers
        self.require_block = require_block
        self.constraint_block = constraint_block
        self.states = states
        # First-class vocabulary fields
        self.steward = headers.get("steward")
        self.target = headers.get("target")
        self.license = headers.get("license")
        self.scope = headers.get("scope")
        self.provenance = headers.get("provenance")
        self.lifetime = headers.get("lifetime")

    def __repr__(self) -> str:
        return (
            f"IntentNode({self.name}, headers={self.headers}, "
            f"require={self.require_block}, constraint={self.constraint_block}, "
            f"states={self.states})"
        )


# ---------------------------------------------------------------------------
# Resource declarations
# ---------------------------------------------------------------------------

class RequireNode(ASTNode):
    """A ``require { ... }`` block listing hard resource minimums."""
    def __init__(self, requirements: list[ResourceDeclNode]):
        self.requirements = requirements

    def __repr__(self) -> str:
        return f"RequireNode({self.requirements})"


class ConstraintBlockNode(ASTNode):
    """A ``constraint { ... }`` block listing operating boundaries."""
    def __init__(self, constraints: list[ConstraintNode]):
        self.constraints = constraints

    def __repr__(self) -> str:
        return f"ConstraintBlockNode({self.constraints})"


class ResourceDeclNode(ASTNode):
    """A single resource requirement: ``mass 500.0 kg;``"""
    def __init__(self, resource: str, value: float, unit: str, line: int):
        self.resource = resource
        self.value = value
        self.unit = unit
        self.line = line

    def __repr__(self) -> str:
        return f"ResourceDeclNode({self.resource} {self.value} {self.unit}, Line {self.line})"


class ConstraintNode(ASTNode):
    """A single constraint: ``energy max 1.2 kWh;``"""
    def __init__(self, resource: str, operator: str, value: float, unit: str, line: int):
        self.resource = resource
        self.operator = operator  # 'max', 'min', or comparison operators
        self.value = value
        self.unit = unit
        self.line = line

    def __repr__(self) -> str:
        return f"ConstraintNode({self.resource} {self.operator} {self.value} {self.unit}, Line {self.line})"


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

class StateNode(ASTNode):
    """A state block in the intent's state machine."""
    def __init__(self, name: str, transitions: list[TransitionNode]):
        self.name = name
        self.transitions = transitions

    def __repr__(self) -> str:
        return f"StateNode({self.name}, transitions={self.transitions})"


class TransitionNode(ASTNode):
    """
    A guarded state transition with optional localized resource requirements.

    Syntax variants::

        on event -> TargetState;
        on event [guard_expr] -> TargetState;
        on event -> TargetState { require energy 0.1 Wh; }
        on event [guard_expr] -> TargetState { require energy 0.1 Wh; }
    """
    def __init__(
        self,
        event: str,
        target: str,
        guard: GuardNode | None = None,
        transition_requires: list[ResourceDeclNode] | None = None,
        line: int = -1,
    ):
        self.event = event
        self.target = target
        self.guard = guard
        self.transition_requires = transition_requires or []
        self.line = line

    def __repr__(self) -> str:
        guard_str = f" [{self.guard}]" if self.guard else ""
        req_str = f" requires={self.transition_requires}" if self.transition_requires else ""
        return f"TransitionNode({self.event}{guard_str} -> {self.target}{req_str})"


class GuardNode(ASTNode):
    """A guard expression on a transition: ``[priority > 2]``"""
    def __init__(self, expr: ExprNode):
        self.expr = expr

    def __repr__(self) -> str:
        return f"GuardNode({self.expr})"


# ---------------------------------------------------------------------------
# Expression nodes (used only inside guards, NOT procedural statements)
# ---------------------------------------------------------------------------

class ExprNode(ASTNode):
    """Base class for expression nodes."""
    pass


class BinaryOpNode(ExprNode):
    """Binary operation: ``left op right``"""
    def __init__(self, left: ExprNode, op: str, right: ExprNode, line: int):
        self.left = left
        self.op = op
        self.right = right
        self.line = line

    def __repr__(self) -> str:
        return f"BinaryOpNode({self.left} {self.op} {self.right})"


class UnaryOpNode(ExprNode):
    """Unary operation: ``not expr`` or ``-expr``"""
    def __init__(self, op: str, expr: ExprNode, line: int):
        self.op = op
        self.expr = expr
        self.line = line

    def __repr__(self) -> str:
        return f"UnaryOpNode({self.op} {self.expr})"


class LiteralNode(ExprNode):
    """A literal value: number, string, percentage, or identifier reference."""
    def __init__(self, value: Any, type_: str, line: int):
        self.value = value
        self.type = type_  # 'NUMBER', 'STRING', 'PERCENT', 'IDENTIFIER'
        self.line = line

    def __repr__(self) -> str:
        return f"LiteralNode({self.type}: {repr(self.value)})"
