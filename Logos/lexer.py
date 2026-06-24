import re
from Logos.exceptions import LogosSyntaxError

KEYWORDS = {
    'scope', 'constraint', 'on', 'or', 'intent', 'steward', 'lifetime',
    'min', 'and', 'state', 'import', 'require', 'target', 'max',
    'provenance', 'not', 'license', 'fn', 'pre', 'post',
    'struct', 'enum', 'spatial', 'socket', 'let', 'mut', 'if', 'else',
    'loop', 'while', 'break', 'continue', 'return', 'alloc', 'free', 'match',
    'fractal'
}

RESOURCES = {'entropy', 'cycle', 'mass', 'energy'}

UNITS = {
    'MWh', 'kg', 'kJ', 'm', 'g', 'seconds', 'minutes', 'J', 'mg',
    'Wh', 's', 'days', 'h', 't', 'kWh', 'd', 'hours', 'cycles'
}

TOKEN_SPECIFICATION = [
    ('ARROW', r'->'),
    ('SEMICOLON', r';'),
    ('COLON', r':'),
    ('LBRACE', r'\{'),
    ('RBRACE', r'\}'),
    ('LBRACKET', r'\['),
    ('RBRACKET', r'\]'),
    ('LPAREN', r'\('),
    ('RPAREN', r'\)'),
    ('COMMA', r','),
    ('DOT', r'\.'),
    ('REFLECTION', r'\^\^'),
    ('VIEWPORT', r'◰'),         # Spatial Layout Matrix
    ('TENSOR', r'⨀'),           # Tensor Composition
    ('POLYMORPH', r'⊸'),        # Polymorphic Mutation
    ('CHOOSE', r'◶'),
    ('BITWISE_SHIFT', r'<<|>>'),
    ('OPERATOR', r'<=|>=|==|!=|<|>'),
    ('ASSIGN', r'='),
    ('PLUS', r'\+'),
    ('MINUS', r'-'),
    ('TIMES', r'\*'),
    ('COMMENT', r'//[^\n]*|#[^\n]*'),
    ('DIVIDE', r'\/'),
    ('MODULO', r'%'),
    ('BITWISE', r'&|\||\^|~'),
    ('NUMBER', r'\d+(\.\d+)?([eE][+-]?\d+)?'),
    ('STRING', r'"[^"\\]*"'),
    ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('NEWLINE', r'\n'),
    ('SKIP', r'[ \t\r]+'),
    ('MISMATCH', r'.'),
]


class Token:
    def __init__(self, type_: str, value: str, line: int, column: int):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self) -> str:
        return f"Token({self.type}, {repr(self.value)}, Line {self.line}, Col {self.column})"


def tokenize(code: str) -> list[Token]:
    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION)
    line_num = 1
    line_start = 0
    tokens = []
    
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start + 1
        
        if kind == 'SKIP' or kind == 'COMMENT':
            continue
        elif kind == 'NEWLINE':
            line_num += 1
            line_start = mo.end()
            continue
        elif kind == 'MISMATCH':
            raise LogosSyntaxError(f"Unexpected character {repr(value)}", line_num, column)
        elif kind == 'IDENTIFIER':
            if value in KEYWORDS:
                kind = 'KEYWORD'
            elif value in RESOURCES:
                kind = 'RESOURCE'
            elif value in UNITS:
                kind = 'UNIT'
        elif kind == 'MODULO' or kind == 'UNIT_PCT':
            kind = 'MODULO_OR_PCT'
            
        if kind == 'STRING':
            value = value[1:-1]
            
        tokens.append(Token(kind, value, line_num, column))
        
    return tokens
