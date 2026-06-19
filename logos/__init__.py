from logos.lexer import Token, tokenize
from logos.parser import Parser
from logos.exceptions import (
    LogosCompilerError,
    LogosSyntaxError,
    LogosRuntimeError,
    ThermodynamicConstraintError,
    CyclicImportError,
    TransitionFrozenError
)
from logos.compiler import Compiler, resolve_imports

def compile_logos(code: str, mesh: dict = None, source_path: str = None) -> dict:
    if mesh is None:
        mesh = {'mass': 1e12, 'energy': 1e12, 'entropy': 1e12, 'cycle': 1e12}
    tokens = tokenize(code)
    parser = Parser(tokens)
    program = parser.parse()
    if source_path:
        program = resolve_imports(program, source_path)
    compiler = Compiler(mesh)
    return compiler.compile(program)
