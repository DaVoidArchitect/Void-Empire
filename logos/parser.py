"""
Logos Parser — Pure Declarative Recursive-Descent Parser

Parses a token stream into an AST of intents, resource declarations,
constraints, guarded state-machine transitions, and import directives.
No procedural statements exist in the grammar.

Grammar (EBNF)::

    Program         ::= (ImportDecl | IntentDef)*
    ImportDecl      ::= 'import' StringLiteral ';'
    IntentDef       ::= 'intent' Identifier '{' IntentBody* '}'
    IntentBody      ::= HeaderDef | RequireBlock | ConstraintBlock | StateDef
    HeaderDef       ::= Identifier ':' (StringLiteral | Number | Identifier) ';'?
    RequireBlock    ::= 'require' '{' ResourceDecl* '}'
    ConstraintBlock ::= 'constraint' '{' ConstraintDecl* '}'
    ResourceDecl    ::= ResourceType Number Unit ';'
    ConstraintDecl  ::= ResourceType ('max' | 'min' | Operator) Number Unit ';'
    StateDef        ::= 'state' Identifier '{' Transition* '}'
    Transition      ::= 'on' Identifier Guard? '->' Identifier TransBody? ';'?
    Guard           ::= '[' Expression ']'
    TransBody       ::= '{' TransRequire* '}'
    TransRequire    ::= 'require' ResourceType Number Unit ';'
    Expression      ::= LogicalOr
    LogicalOr       ::= LogicalAnd ('or' LogicalAnd)*
    LogicalAnd      ::= Equality ('and' Equality)*
    Equality        ::= Comparison (('==' | '!=') Comparison)*
    Comparison      ::= Term (('<' | '>' | '<=' | '>=') Term)*
    Term            ::= Factor (('+' | '-') Factor)*
    Factor          ::= Unary (('*' | '/') Unary)*
    Unary           ::= ('not' | '-') Unary | Primary
    Primary         ::= Number '%'? | StringLiteral | Identifier | '(' Expression ')'
"""

from .lexer import Token
from .exceptions import LogosSyntaxError
from .logos_ast import (
    ASTNode, ProgramNode, ImportNode, IntentNode,
    RequireNode, ConstraintBlockNode, ResourceDeclNode, ConstraintNode,
    StateNode, TransitionNode, GuardNode,
    BinaryOpNode, UnaryOpNode, LiteralNode,
)


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # ------------------------------------------------------------------
    # Token navigation helpers
    # ------------------------------------------------------------------

    def peek(self) -> Token | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def previous(self) -> Token:
        return self.tokens[self.pos - 1]

    def is_at_end(self) -> bool:
        return self.pos >= len(self.tokens)

    def advance(self) -> Token:
        if not self.is_at_end():
            self.pos += 1
        return self.previous()

    def check(self, type_: str, value: str | None = None) -> bool:
        t = self.peek()
        if not t or t.type != type_:
            return False
        return value is None or t.value == value

    def accept(self, type_: str, value: str | None = None) -> bool:
        if self.check(type_, value):
            self.advance()
            return True
        return False

    def expect(self, type_: str, value: str | None = None, err_msg: str = "") -> Token:
        t = self.peek()
        if not t:
            raise LogosSyntaxError(err_msg or f"Expected token of type {type_}", -1, -1)
        if t.type != type_ or (value is not None and t.value != value):
            val_str = f" '{value}'" if value is not None else ""
            raise LogosSyntaxError(
                err_msg or f"Expected {type_}{val_str}, got {t.type} '{t.value}'",
                t.line, t.column,
            )
        return self.advance()

    # ------------------------------------------------------------------
    # Top-level: Program
    # ------------------------------------------------------------------

    def parse(self) -> ProgramNode:
        imports: list[ImportNode] = []
        intents: list[IntentNode] = []

        while not self.is_at_end():
            if self.check('KEYWORD', 'import'):
                imports.append(self._parse_import())
            elif self.check('KEYWORD', 'intent'):
                intents.append(self._parse_intent())
            else:
                t = self.peek()
                raise LogosSyntaxError(
                    f"Expected 'import' or 'intent' at top level, got {t.type} '{t.value}'",
                    t.line, t.column,
                )

        return ProgramNode(imports, intents)

    # ------------------------------------------------------------------
    # Import directive
    # ------------------------------------------------------------------

    def _parse_import(self) -> ImportNode:
        imp_tok = self.expect('KEYWORD', 'import')
        path_tok = self.expect('STRING', err_msg="Expected file path string after 'import'.")
        self.accept('SEMICOLON')  # optional trailing semicolon
        return ImportNode(path_tok.value, imp_tok.line)

    # ------------------------------------------------------------------
    # Intent definition
    # ------------------------------------------------------------------

    def _parse_intent(self) -> IntentNode:
        self.expect('KEYWORD', 'intent', "Expected 'intent' keyword.")
        name_tok = self.expect('IDENTIFIER', err_msg="Expected intent name identifier.")
        self.expect('LBRACE', err_msg="Expected '{' to open intent body.")

        headers: dict = {}
        require_block: RequireNode | None = None
        constraint_block: ConstraintBlockNode | None = None
        states: list[StateNode] = []

        while not self.accept('RBRACE'):
            if self.is_at_end():
                raise LogosSyntaxError("Unclosed intent body, expected '}'", name_tok.line, name_tok.column)

            t = self.peek()

            if t.type == 'KEYWORD' and t.value == 'require':
                if require_block is not None:
                    raise LogosSyntaxError("Duplicate require block in intent.", t.line, t.column)
                require_block = self._parse_require_block()

            elif t.type == 'KEYWORD' and t.value == 'constraint':
                if constraint_block is not None:
                    raise LogosSyntaxError("Duplicate constraint block in intent.", t.line, t.column)
                constraint_block = self._parse_constraint_block()

            elif t.type == 'KEYWORD' and t.value == 'state':
                states.append(self._parse_state())

            elif t.type in ('IDENTIFIER', 'KEYWORD') and t.value not in ('require', 'constraint', 'state'):
                key, val = self._parse_header()
                headers[key] = val
            else:
                raise LogosSyntaxError(
                    f"Unexpected token inside intent body: {t.type} '{t.value}'",
                    t.line, t.column,
                )

        return IntentNode(name_tok.value, headers, require_block, constraint_block, states)

    # ------------------------------------------------------------------
    # Headers (key-value metadata)
    # ------------------------------------------------------------------

    def _parse_header(self) -> tuple:
        t = self.peek()
        if not t or t.type not in ('IDENTIFIER', 'KEYWORD'):
            raise LogosSyntaxError("Expected header key identifier.", t.line if t else -1, t.column if t else -1)

        key_tok = self.advance()
        self.expect('COLON', err_msg="Expected ':' after header key.")

        # Lifetime is special: number + optional unit
        if key_tok.value == "lifetime":
            val_tok = self.expect('NUMBER', err_msg="Expected numeric value for lifetime.")
            val = float(val_tok.value) if '.' in val_tok.value else int(val_tok.value)
            unit = ""
            if self.check('UNIT'):
                unit = self.advance().value
            self.accept('SEMICOLON')
            return key_tok.value, {"value": val, "unit": unit}

        val_tok = self.peek()
        if not val_tok:
            raise LogosSyntaxError("Expected header value after ':'.", key_tok.line, key_tok.column)

        if val_tok.type in ('STRING', 'NUMBER', 'IDENTIFIER', 'KEYWORD'):
            self.advance()
            val = val_tok.value
            if val_tok.type == 'NUMBER':
                val = float(val) if '.' in val else int(val)
            self.accept('SEMICOLON')
            return key_tok.value, val
        else:
            raise LogosSyntaxError(
                f"Invalid header value token: {val_tok.type} '{val_tok.value}'",
                val_tok.line, val_tok.column,
            )

    # ------------------------------------------------------------------
    # Require block (hard resource minimums)
    # ------------------------------------------------------------------

    def _parse_require_block(self) -> RequireNode:
        req_tok = self.expect('KEYWORD', 'require')
        self.expect('LBRACE', err_msg="Expected '{' after 'require'.")

        requirements: list[ResourceDeclNode] = []
        while not self.accept('RBRACE'):
            if self.is_at_end():
                raise LogosSyntaxError("Unclosed require block, expected '}'", req_tok.line, req_tok.column)
            requirements.append(self._parse_resource_decl())

        return RequireNode(requirements)

    def _parse_resource_decl(self) -> ResourceDeclNode:
        res_tok = self.expect('RESOURCE', err_msg="Expected resource primitive (mass, energy, entropy, cycle).")
        val_tok = self.expect('NUMBER', err_msg="Expected numeric value for resource.")
        val = float(val_tok.value)

        unit = ""
        if self.check('UNIT'):
            unit = self.advance().value

        self.accept('SEMICOLON')
        return ResourceDeclNode(res_tok.value, val, unit, res_tok.line)

    # ------------------------------------------------------------------
    # Constraint block (operating boundaries)
    # ------------------------------------------------------------------

    def _parse_constraint_block(self) -> ConstraintBlockNode:
        con_tok = self.expect('KEYWORD', 'constraint')
        self.expect('LBRACE', err_msg="Expected '{' after 'constraint'.")

        constraints: list[ConstraintNode] = []
        while not self.accept('RBRACE'):
            if self.is_at_end():
                raise LogosSyntaxError("Unclosed constraint block, expected '}'", con_tok.line, con_tok.column)
            constraints.append(self._parse_constraint_decl())

        return ConstraintBlockNode(constraints)

    def _parse_constraint_decl(self) -> ConstraintNode:
        res_tok = self.expect('RESOURCE', err_msg="Expected resource primitive in constraint.")

        # Operator: 'max', 'min', or comparison operator
        t = self.peek()
        if not t:
            raise LogosSyntaxError("Expected constraint operator.", res_tok.line, res_tok.column)

        if t.type == 'KEYWORD' and t.value in ('max', 'min'):
            op = self.advance().value
        elif t.type == 'OPERATOR':
            op = self.advance().value
        else:
            raise LogosSyntaxError(
                f"Expected 'max', 'min', or comparison operator, got {t.type} '{t.value}'",
                t.line, t.column,
            )

        val_tok = self.expect('NUMBER', err_msg="Expected numeric value for constraint.")
        val = float(val_tok.value)

        unit = ""
        if self.check('UNIT'):
            unit = self.advance().value

        self.accept('SEMICOLON')
        return ConstraintNode(res_tok.value, op, val, unit, res_tok.line)

    # ------------------------------------------------------------------
    # State definition
    # ------------------------------------------------------------------

    def _parse_state(self) -> StateNode:
        state_tok = self.expect('KEYWORD', 'state')
        name_tok = self.expect('IDENTIFIER', err_msg="Expected state name identifier.")
        self.expect('LBRACE', err_msg="Expected '{' after state name.")

        transitions: list[TransitionNode] = []
        while not self.accept('RBRACE'):
            if self.is_at_end():
                raise LogosSyntaxError("Unclosed state body, expected '}'", state_tok.line, state_tok.column)
            transitions.append(self._parse_transition())

        return StateNode(name_tok.value, transitions)

    # ------------------------------------------------------------------
    # Transition (with optional guard and transition-level requirements)
    # ------------------------------------------------------------------

    def _parse_transition(self) -> TransitionNode:
        on_tok = self.expect('KEYWORD', 'on', err_msg="Expected 'on' keyword in transition.")
        evt_tok = self.expect('IDENTIFIER', err_msg="Expected event identifier after 'on'.")

        # Optional guard: [expression]
        guard: GuardNode | None = None
        if self.accept('LBRACKET'):
            guard_expr = self._parse_expression()
            self.expect('RBRACKET', err_msg="Expected ']' to close guard expression.")
            guard = GuardNode(guard_expr)

        self.expect('ARROW', err_msg="Expected '->' after event (or guard).")
        target_tok = self.expect('IDENTIFIER', err_msg="Expected target state identifier after '->'.")

        # Optional transition body with localized resource requirements
        transition_requires: list[ResourceDeclNode] = []
        if self.accept('LBRACE'):
            while not self.accept('RBRACE'):
                if self.is_at_end():
                    raise LogosSyntaxError(
                        "Unclosed transition body, expected '}'", on_tok.line, on_tok.column
                    )
                self.expect('KEYWORD', 'require', err_msg="Expected 'require' inside transition body.")
                transition_requires.append(self._parse_resource_decl())

        self.accept('SEMICOLON')

        return TransitionNode(
            event=evt_tok.value,
            target=target_tok.value,
            guard=guard,
            transition_requires=transition_requires,
            line=on_tok.line,
        )

    # ------------------------------------------------------------------
    # Expressions (used only inside guard brackets)
    # ------------------------------------------------------------------

    def _parse_expression(self) -> ASTNode:
        return self._parse_logical_or()

    def _parse_logical_or(self) -> ASTNode:
        node = self._parse_logical_and()
        while self.check('KEYWORD', 'or'):
            op_tok = self.advance()
            right = self._parse_logical_and()
            node = BinaryOpNode(node, op_tok.value, right, op_tok.line)
        return node

    def _parse_logical_and(self) -> ASTNode:
        node = self._parse_equality()
        while self.check('KEYWORD', 'and'):
            op_tok = self.advance()
            right = self._parse_equality()
            node = BinaryOpNode(node, op_tok.value, right, op_tok.line)
        return node

    def _parse_equality(self) -> ASTNode:
        node = self._parse_comparison()
        while self.check('OPERATOR', '==') or self.check('OPERATOR', '!='):
            op_tok = self.advance()
            right = self._parse_comparison()
            node = BinaryOpNode(node, op_tok.value, right, op_tok.line)
        return node

    def _parse_comparison(self) -> ASTNode:
        node = self._parse_term()
        while self.peek() and self.peek().type == 'OPERATOR' and self.peek().value in ('<', '>', '<=', '>='):
            op_tok = self.advance()
            right = self._parse_term()
            node = BinaryOpNode(node, op_tok.value, right, op_tok.line)
        return node

    def _parse_term(self) -> ASTNode:
        node = self._parse_factor()
        while self.check('PLUS') or self.check('MINUS'):
            op_tok = self.advance()
            right = self._parse_factor()
            node = BinaryOpNode(node, op_tok.value, right, op_tok.line)
        return node

    def _parse_factor(self) -> ASTNode:
        node = self._parse_unary()
        while self.check('TIMES') or self.check('DIVIDE'):
            op_tok = self.advance()
            right = self._parse_unary()
            node = BinaryOpNode(node, op_tok.value, right, op_tok.line)
        return node

    def _parse_unary(self) -> ASTNode:
        if self.check('KEYWORD', 'not') or self.check('MINUS'):
            op_tok = self.advance()
            right = self._parse_unary()
            return UnaryOpNode(op_tok.value, right, op_tok.line)
        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        t = self.peek()
        if not t:
            raise LogosSyntaxError("Expected expression", -1, -1)

        if t.type == 'NUMBER':
            self.advance()
            if self.check('UNIT', '%'):
                self.advance()
                return LiteralNode(float(t.value), 'PERCENT', t.line)
            val = float(t.value) if '.' in t.value else int(t.value)
            return LiteralNode(val, 'NUMBER', t.line)

        elif t.type == 'STRING':
            self.advance()
            return LiteralNode(t.value, 'STRING', t.line)

        elif t.type == 'IDENTIFIER':
            self.advance()
            return LiteralNode(t.value, 'IDENTIFIER', t.line)

        elif t.type == 'LPAREN':
            self.advance()
            expr = self._parse_expression()
            self.expect('RPAREN', err_msg="Expected ')' to close grouped expression.")
            return expr

        raise LogosSyntaxError(
            f"Unexpected token in expression: {t.type} '{t.value}'", t.line, t.column
        )
