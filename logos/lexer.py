"""
Logos Lexer — Pure Declarative Token Scanner

Scans raw Logos source into a stream of typed tokens for the recursive-descent
parser. Supports the full declarative grammar: intents, require blocks,
constraint blocks, state machines, transition guards, and import directives.
"""

import re
from .exceptions import LogosSyntaxError


class Token:
    __slots__ = ('type', 'value', 'line', 'column')

    def __init__(self, type_: str, value: str, line: int, column: int):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self) -> str:
        return f"Token({self.type}, {repr(self.value)}, Line {self.line}, Col {self.column})"


# Token specification — ordered by match priority (longest match first).
TOKEN_SPECIFICATION = [
    ('ARROW',       r'->'),
    ('SEMICOLON',   r';'),
    ('COLON',       r':'),
    ('LBRACE',      r'\{'),
    ('RBRACE',      r'\}'),
    ('LBRACKET',    r'\['),
    ('RBRACKET',    r'\]'),
    ('LPAREN',      r'\('),
    ('RPAREN',      r'\)'),
    ('COMMA',       r','),
    ('OPERATOR',    r'<=|>=|==|!=|<|>'),
    ('PLUS',        r'\+'),
    ('MINUS',       r'-'),
    ('TIMES',       r'\*'),
    ('COMMENT',     r'//[^\n]*|#[^\n]*'),
    ('DIVIDE',      r'\/'),
    ('UNIT_PCT',    r'%'),
    ('NUMBER',      r'\d+(\.\d+)?'),
    ('STRING',      r'"[^"\\]*"'),
    ('IDENTIFIER',  r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('NEWLINE',     r'\n'),
    ('SKIP',        r'[ \t\r]+'),
    ('MISMATCH',    r'.'),
]

# Keywords in the declarative Logos grammar.
KEYWORDS = {
    'intent', 'require', 'constraint', 'state', 'on', 'import',
    'steward', 'target', 'license', 'scope', 'provenance', 'lifetime',
    'max', 'min', 'and', 'or', 'not',
}

# Thermodynamic resource primitives.
RESOURCES = {'mass', 'energy', 'entropy', 'cycle'}

# Recognised physical units (SI and convenience aliases).
UNITS = {
    'kg', 'g', 'mg', 't',
    'kWh', 'MWh', 'Wh', 'kJ', 'J',
    's', 'seconds', 'm', 'minutes', 'h', 'hours', 'd', 'days', 'cycles',
}


def tokenize(code: str) -> list[Token]:
    """Scan *code* into a list of Logos tokens."""
    tokens: list[Token] = []
    line_num = 1
    line_start = 0

    tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in TOKEN_SPECIFICATION)

    for m in re.finditer(tok_regex, code):
        kind = m.lastgroup
        value = m.group(kind)
        column = m.start() - line_start + 1

        if kind == 'NEWLINE':
            line_start = m.end()
            line_num += 1
        elif kind in ('SKIP', 'COMMENT'):
            continue
        elif kind == 'IDENTIFIER':
            if value in KEYWORDS:
                kind = 'KEYWORD'
            elif value in RESOURCES:
                kind = 'RESOURCE'
            elif value in UNITS:
                kind = 'UNIT'
            tokens.append(Token(kind, value, line_num, column))
        elif kind == 'UNIT_PCT':
            tokens.append(Token('UNIT', '%', line_num, column))
        elif kind == 'MISMATCH':
            raise LogosSyntaxError(f"Unexpected character {repr(value)}", line_num, column)
        else:
            if kind == 'STRING':
                value = value[1:-1]  # strip quotes
            tokens.append(Token(kind, value, line_num, column))

    return tokens
