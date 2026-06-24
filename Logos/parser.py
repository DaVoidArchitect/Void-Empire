import sys
sys.setrecursionlimit(10000)

from Logos.lexer import Token
from Logos.exceptions import LogosSyntaxError
from Logos.logos_ast import *

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def peek(self) -> Token | None:
        if self.is_at_end():
            return None
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def is_at_end(self) -> bool:
        return self.current >= len(self.tokens)

    def check(self, type_: str, value: str | None = None) -> bool:
        if self.is_at_end():
            return False
        tok = self.peek()
        if tok.type != type_:
            return False
        if value is not None and tok.value != value:
            return False
        return True

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def accept(self, type_: str, value: str | None = None) -> bool:
        if self.check(type_, value):
            self.advance()
            return True
        return False

    def expect(self, type_: str, value: str | None = None, err_msg: str = '') -> Token:
        if self.accept(type_, value):
            return self.previous()
        t = self.peek()
        line = t.line if t else -1
        col = t.column if t else -1
        raise LogosSyntaxError(err_msg or f"Expected token {type_}", line, col)

    def parse(self) -> ProgramNode:
        imports = []
        items = []
        while not self.is_at_end():
            if self.check('KEYWORD', 'import'):
                imports.append(self._parse_import())
            elif self.check('KEYWORD', 'fractal'):
                self.advance()
                if self.check('KEYWORD', 'struct'):
                    items.append(self._parse_struct(is_fractal=True))
                elif self.check('KEYWORD', 'intent'):
                    items.append(self._parse_intent(is_fractal=True))
                else:
                    t = self.peek()
                    raise LogosSyntaxError(f"Expected 'struct' or 'intent' after 'fractal', got {t.type}", t.line, t.column)
            elif self.check('KEYWORD', 'struct'):
                items.append(self._parse_struct(is_fractal=False))
            elif self.check('KEYWORD', 'enum'):
                items.append(self._parse_enum())
            elif self.check('KEYWORD', 'intent'):
                items.append(self._parse_intent(is_fractal=False))
            elif self.check('KEYWORD', 'fn'):
                items.append(self._parse_func())
            else:
                t = self.peek()
                raise LogosSyntaxError(f"Unexpected token at top level, got {t.type} '{t.value}'", t.line, t.column)
        return ProgramNode(imports, items)

    def _parse_import(self) -> ImportNode:
        imp_tok = self.expect('KEYWORD', 'import')
        path_tok = self.expect('STRING', err_msg="Expected file path string after 'import'.")
        self.expect('SEMICOLON', err_msg="Expected ';' after import.")
        return ImportNode(path_tok.value, imp_tok.line)

    def _parse_struct(self, is_fractal: bool) -> StructDefNode:
        struct_tok = self.expect('KEYWORD', 'struct')
        name_tok = self.expect('IDENTIFIER', err_msg="Expected struct name")
        self.expect('LBRACE', err_msg="Expected '{' after struct name")
        
        fields = []
        while not self.accept('RBRACE'):
            if self.is_at_end():
                raise LogosSyntaxError("Unclosed struct body", name_tok.line, name_tok.column)
            f_name = self.expect('IDENTIFIER', err_msg="Expected field name")
            self.expect('COLON', err_msg="Expected ':' after field name")
            f_type = self._parse_type()
            self.expect('SEMICOLON', err_msg="Expected ';' after field definition")
            fields.append(FieldDefNode(f_name.value, f_type, f_name.line))
            
        return StructDefNode(name_tok.value, fields, is_fractal, struct_tok.line)

    def _parse_enum(self) -> EnumDefNode:
        enum_tok = self.expect('KEYWORD', 'enum')
        name_tok = self.expect('IDENTIFIER', err_msg="Expected enum name")
        self.expect('LBRACE', err_msg="Expected '{' after enum name")
        
        variants = []
        while not self.accept('RBRACE'):
            if self.is_at_end():
                raise LogosSyntaxError("Unclosed enum body", name_tok.line, name_tok.column)
            v_tok = self.expect('IDENTIFIER', err_msg="Expected enum variant name")
            variants.append(v_tok.value)
            self.accept('COMMA')
            
        return EnumDefNode(name_tok.value, variants, enum_tok.line)

    def _parse_type(self) -> str:
        if self.accept('BITWISE', '^'):
            t = self._parse_type()
            return f"^{t}"
        elif self.accept('LBRACKET'):
            t = self._parse_type()
            self.expect('SEMICOLON')
            size = self.expect('NUMBER')
            self.expect('RBRACKET')
            return f"[{t}; {size.value}]"
        
        # We can handle generic types or simple identifiers here
        t = self.expect('IDENTIFIER', err_msg="Expected type identifier")
        return t.value

    def _parse_intent(self, is_fractal: bool) -> IntentNode:
        self.expect('KEYWORD', 'intent')
        name_tok = self.expect('IDENTIFIER', err_msg='Expected intent name')
        self.expect('LBRACE', err_msg="Expected '{' after intent name")
        
        headers = {}
        require_block = None
        constraint_block = None
        states = []
        spatial_blocks = []
        socket_blocks = []
        functions = []

        while not self.accept('RBRACE'):
            if self.is_at_end():
                raise LogosSyntaxError("Unclosed intent body, expected '}'", name_tok.line, name_tok.column)
            
            t = self.peek()
            if t.type == 'KEYWORD' and t.value == 'require':
                if require_block is not None:
                    raise LogosSyntaxError('Duplicate require block in intent.', t.line, t.column)
                require_block = self._parse_require_block()
            elif t.type == 'KEYWORD' and t.value == 'constraint':
                if constraint_block is not None:
                    raise LogosSyntaxError('Duplicate constraint block in intent.', t.line, t.column)
                constraint_block = self._parse_constraint_block()
            elif t.type == 'KEYWORD' and t.value == 'state':
                states.append(self._parse_state())
            elif t.type == 'KEYWORD' and t.value == 'spatial':
                spatial_blocks.append(self._parse_spatial_block())
            elif t.type == 'KEYWORD' and t.value == 'socket':
                socket_blocks.append(self._parse_socket_block())
            elif t.type == 'KEYWORD' and t.value == 'fn':
                functions.append(self._parse_func())
            elif t.type in ('IDENTIFIER', 'KEYWORD'):
                key, val = self._parse_header()
                headers[key] = val
            else:
                raise LogosSyntaxError(f"Unexpected token inside intent body: {t.type} '{t.value}'", t.line, t.column)

        return IntentNode(name_tok.value, is_fractal, headers, require_block, constraint_block, states, spatial_blocks, socket_blocks, functions)

    def _parse_spatial_block(self) -> SpatialBlockNode:
        sp_tok = self.expect('KEYWORD', 'spatial')
        name_tok = self.expect('IDENTIFIER', err_msg="Expected spatial block name")
        self.expect('LBRACE', err_msg="Expected '{'")
        properties = []
        while not self.accept('RBRACE'):
            key_tok = self.expect('IDENTIFIER')
            self.expect('COLON')
            expr = self._parse_expression()
            self.expect('SEMICOLON')
            properties.append(KeyValNode(key_tok.value, expr, key_tok.line))
        return SpatialBlockNode(name_tok.value, properties, sp_tok.line)

    def _parse_socket_block(self) -> SocketBlockNode:
        so_tok = self.expect('KEYWORD', 'socket')
        name_tok = self.expect('IDENTIFIER', err_msg="Expected socket block name")
        self.expect('LBRACE', err_msg="Expected '{'")
        properties = []
        while not self.accept('RBRACE'):
            key_tok = self.expect('IDENTIFIER')
            self.expect('COLON')
            expr = self._parse_expression()
            self.expect('SEMICOLON')
            properties.append(KeyValNode(key_tok.value, expr, key_tok.line))
        return SocketBlockNode(name_tok.value, properties, so_tok.line)

    def _parse_header(self) -> tuple:
        key_tok = self.advance()
        self.expect('COLON', err_msg="Expected ':' after header key.")
        
        if key_tok.value == 'lifetime':
            val_tok = self.expect('NUMBER', err_msg='Expected numeric value for lifetime.')
            val = float(val_tok.value) if '.' in val_tok.value else int(val_tok.value)
            unit = ''
            if self.check('UNIT'):
                unit = self.advance().value
            self.expect('SEMICOLON', err_msg="Expected ';' after header declaration.")
            return (key_tok.value, {"value": val, "unit": unit})
        else:
            val_tok = self.advance()
            val = val_tok.value
            if val_tok.type == 'NUMBER':
                val = float(val) if '.' in val else int(val)
            self.expect('SEMICOLON', err_msg="Expected ';' after header declaration.")
            return (key_tok.value, val)

    def _parse_require_block(self) -> RequireNode:
        req_tok = self.expect('KEYWORD', 'require')
        self.expect('LBRACE', err_msg="Expected '{' after 'require'.")
        requirements = []
        while not self.accept('RBRACE'):
            res_tok = self.expect('RESOURCE', err_msg='Expected resource primitive.')
            self.expect('COLON')
            
            # Allow optional constraint op inside require block due to some old code syntax
            if self.check('OPERATOR') or self.check('KEYWORD', 'min') or self.check('KEYWORD', 'max'):
                self.advance()
                
            val_tok = self.expect('NUMBER', err_msg='Expected numeric value.')
            val = float(val_tok.value)
            unit = ''
            if self.check('UNIT'):
                unit = self.advance().value
            self.expect('SEMICOLON', err_msg="Expected ';' after resource declaration.")
            requirements.append(ResourceDeclNode(res_tok.value, val, unit, res_tok.line))
        return RequireNode(requirements)

    def _parse_constraint_block(self) -> ConstraintBlockNode:
        con_tok = self.expect('KEYWORD', 'constraint')
        self.expect('LBRACE', err_msg="Expected '{' after 'constraint'.")
        constraints = []
        while not self.accept('RBRACE'):
            res_tok = self.expect('RESOURCE', err_msg='Expected resource primitive in constraint.')
            self.expect('COLON')
            op = '=='
            if self.check('OPERATOR') or self.check('KEYWORD') or (self.check('IDENTIFIER') and self.peek().value in ('max', 'min')):
                op = self.advance().value
            
            val_tok = self.expect('NUMBER', err_msg='Expected numeric value for constraint.')
            val = float(val_tok.value)
            unit = ''
            if self.check('UNIT'):
                unit = self.advance().value
            self.expect('SEMICOLON', err_msg="Expected ';' after constraint declaration.")
            constraints.append(ConstraintNode(res_tok.value, op, val, unit, res_tok.line))
        return ConstraintBlockNode(constraints)

    def _parse_state(self) -> StateNode:
        state_tok = self.expect('KEYWORD', 'state')
        name_tok = self.expect('IDENTIFIER', err_msg='Expected state name')
        self.expect('LBRACE', err_msg="Expected '{' after state name.")
        transitions = []
        while not self.accept('RBRACE'):
            on_tok = self.expect('KEYWORD', 'on', err_msg="Expected 'on' keyword in transition.")
            evt_tok = self.expect('IDENTIFIER', err_msg="Expected event identifier after 'on'.")
            
            guard = None
            if self.accept('LBRACKET'):
                guard_expr = self._parse_expression()
                self.expect('RBRACKET', err_msg="Expected ']' to close guard expression.")
                guard = GuardNode(guard_expr)
                
            self.expect('ARROW', err_msg="Expected '->' after event (or guard).")
            target_tok = self.expect('IDENTIFIER', err_msg="Expected target state identifier after '->'.")
            
            transition_requires = []
            if self.accept('LBRACE'):
                if not self.accept('RBRACE'):
                    while True:
                        if self.is_at_end():
                            raise LogosSyntaxError("Unclosed transition body", on_tok.line, on_tok.column)
                        self.expect('KEYWORD', 'require')
                        self.expect('LBRACE')
                        while not self.accept('RBRACE'):
                            res_tok = self.expect('RESOURCE')
                            self.expect('COLON')
                            val_tok = self.expect('NUMBER')
                            val = float(val_tok.value)
                            unit = ''
                            if self.check('UNIT'):
                                unit = self.advance().value
                            self.expect('SEMICOLON')
                            transition_requires.append(ResourceDeclNode(res_tok.value, val, unit, res_tok.line))
                        if self.accept('RBRACE'):
                            break
            
            self.accept('SEMICOLON')
            transitions.append(TransitionNode(event=evt_tok.value, target=target_tok.value, guard=guard, transition_requires=transition_requires, line=on_tok.line))
        return StateNode(name_tok.value, transitions)

    def _parse_func(self) -> FuncDefNode:
        fn_tok = self.expect('KEYWORD', 'fn')
        name_tok = self.expect('IDENTIFIER', err_msg="Expected function name after 'fn'.")
        self.expect('LPAREN', err_msg="Expected '(' after function name.")
        
        params = []
        if not self.check('RPAREN'):
            while True:
                is_mut = self.accept('KEYWORD', 'mut')
                p_name = self.expect('IDENTIFIER', err_msg="Expected parameter name.")
                self.expect('COLON', err_msg="Expected ':' after parameter name.")
                p_type = self._parse_type()
                params.append({'name': p_name.value, 'type': p_type, 'is_mut': is_mut})
                if not self.accept('COMMA'):
                    break
        self.expect('RPAREN', err_msg="Expected ')' after parameter list.")
        
        return_type = None
        if self.accept('ARROW'):
            return_type = self._parse_type()

        pre_contracts = []
        post_contracts = []
        while self.check('KEYWORD', 'pre') or self.check('KEYWORD', 'post'):
            kind_tok = self.advance()
            self.expect('LBRACE')
            exprs = []
            while not self.accept('RBRACE'):
                exprs.append(self._parse_expression())
                self.expect('SEMICOLON')
            if kind_tok.value == 'pre':
                pre_contracts.append(PreBlockNode(exprs, kind_tok.line))
            else:
                post_contracts.append(PostBlockNode(exprs, kind_tok.line))

        body = self._parse_block()
        return FuncDefNode(name_tok.value, params, return_type, pre_contracts, post_contracts, body, fn_tok.line)

    def _parse_block(self) -> BlockNode:
        lb = self.expect('LBRACE')
        stmts = []
        while not self.accept('RBRACE'):
            stmts.append(self._parse_statement())
        return BlockNode(stmts, lb.line)

    def _parse_statement(self) -> StmtNode:
        if self.check('KEYWORD', 'let'):
            return self._parse_let()
        elif self.check('KEYWORD', 'if'):
            return self._parse_if()
        elif self.check('KEYWORD', 'match'):
            return self._parse_match()
        elif self.check('KEYWORD', 'loop') or self.check('KEYWORD', 'while'):
            return self._parse_loop()
        elif self.check('KEYWORD', 'return'):
            return self._parse_return()
        elif self.check('KEYWORD', 'break'):
            b = self.advance()
            self.expect('SEMICOLON')
            return BreakStmtNode(b.line)
        elif self.check('KEYWORD', 'continue'):
            c = self.advance()
            self.expect('SEMICOLON')
            return ContinueStmtNode(c.line)
        else:
            expr = self._parse_expression()
            self.expect('SEMICOLON', err_msg="Expected ';' after expression statement")
            return ExprStmtNode(expr, expr.line)

    def _parse_let(self) -> LetStmtNode:
        l = self.expect('KEYWORD', 'let')
        is_mut = self.accept('KEYWORD', 'mut')
        name_tok = self.expect('IDENTIFIER')
        type_ann = None
        if self.accept('COLON'):
            type_ann = self._parse_type()
        self.expect('ASSIGN')
        val = self._parse_expression()
        self.expect('SEMICOLON')
        return LetStmtNode(name_tok.value, is_mut, type_ann, val, l.line)

    def _parse_if(self) -> IfStmtNode:
        i = self.expect('KEYWORD', 'if')
        self.expect('LPAREN')
        cond = self._parse_expression()
        self.expect('RPAREN')
        then_block = self._parse_block()
        else_block = None
        if self.accept('KEYWORD', 'else'):
            if self.check('KEYWORD', 'if'):
                else_block = self._parse_if()
            else:
                else_block = self._parse_block()
        return IfStmtNode(cond, then_block, else_block, i.line)

    def _parse_match(self) -> MatchStmtNode:
        m = self.expect('KEYWORD', 'match')
        self.expect('LPAREN')
        expr = self._parse_expression()
        self.expect('RPAREN')
        self.expect('LBRACE')
        arms = []
        while not self.accept('RBRACE'):
            pat = self._parse_type() # Simplified matching pattern
            self.expect('ARROW')
            block = self._parse_block()
            arms.append(MatchArmNode(pat, block, block.line))
        return MatchStmtNode(expr, arms, m.line)

    def _parse_loop(self) -> LoopStmtNode:
        l = self.advance()
        cond = None
        if l.value == 'while':
            self.expect('LPAREN')
            cond = self._parse_expression()
            self.expect('RPAREN')
        body = self._parse_block()
        return LoopStmtNode(cond, body, l.line)

    def _parse_return(self) -> ReturnStmtNode:
        r = self.expect('KEYWORD', 'return')
        val = None
        if not self.check('SEMICOLON'):
            val = self._parse_expression()
        self.expect('SEMICOLON')
        return ReturnStmtNode(val, r.line)

    # -------------------------------------------------------------------------
    # RIGHT-TO-LEFT (RTL) EXPRESSION PARSER
    # The APL/BQN style parser evaluates strictly Right-to-Left natively.
    # An Expression is an Operand followed by an Operator followed by an Expression.
    # -------------------------------------------------------------------------
    def _parse_expression(self) -> ExprNode:
        left = self._parse_operand()
        
        t = self.peek()
        if not t:
            return left
            
        if self._is_operator(t):
            op_tok = self.advance()
            # Recursive call forms the RTL tree directly without stack juggling
            right = self._parse_expression()
            return BinaryOpNode(left, op_tok.value, right, op_tok.line)
            
        return left

    def _is_operator(self, t: Token) -> bool:
        ops = {'OPERATOR', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULO', 'MODULO_OR_PCT', 
               'BITWISE', 'BITWISE_SHIFT', 'ASSIGN', 'TENSOR', 'POLYMORPH', 'VIEWPORT'}
        if t.type in ops:
            return True
        if t.type == 'KEYWORD' and t.value in ('and', 'or', '==', '!='):
            return True
        return False

    def _parse_operand(self) -> ExprNode:
        if self.check('KEYWORD', 'not') or self.check('MINUS') or self.check('REFLECTION') or \
           self.check('KEYWORD', 'alloc') or self.check('KEYWORD', 'free') or \
           self.check('TIMES') or self.check('BITWISE', '&') or self.check('BITWISE', '~'):
            op_tok = self.advance()
            expr = self._parse_operand()
            return UnaryOpNode(op_tok.value, expr, op_tok.line)
        
        return self._parse_call()

    def _parse_call(self) -> ExprNode:
        node = self._parse_primary()
        while True:
            if self.accept('LPAREN'):
                args = []
                if not self.check('RPAREN'):
                    while True:
                        args.append(self._parse_expression())
                        if not self.accept('COMMA'):
                            break
                self.expect('RPAREN')
                node = CallNode(node, args, node.line)
            elif self.accept('DOT'):
                member = self.expect('IDENTIFIER')
                node = MemberAccessNode(node, member.value, member.line)
            elif self.accept('LBRACKET'):
                idx = self._parse_expression()
                self.expect('RBRACKET')
                node = IndexAccessNode(node, idx, node.line)
            else:
                break
        return node

    def _parse_primary(self) -> ExprNode:
        t = self.peek()
        if not t:
            raise LogosSyntaxError('Expected expression', -1, -1)
            
        if t.type == 'NUMBER':
            self.advance()
            if self.check('MODULO_OR_PCT'):
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
            self.expect('RPAREN')
            return expr
        else:
            raise LogosSyntaxError(f"Unexpected token in expression: {t.type} '{t.value}'", t.line, t.column)

