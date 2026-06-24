from .lexer import tokenize, Token
from .parser import Parser
from .compiler import Compiler, resolve_imports
from .exceptions import (
    LogosCompilerError,
    LogosSyntaxError,
    ThermodynamicConstraintError,
    CyclicImportError,
)

def compile_logos(code: str, mesh_context: dict = None, source_path: str = "<stdin>") -> dict:
    """
    Parses and compiles Logos source code. Verifies that all declared thermodynamic
    limits are satisfied by the provided mesh_context.
    
    Returns a dictionary describing the compiled state machines.
    Raises LogosSyntaxError or ThermodynamicConstraintError if compilation fails.
    """
    if mesh_context is None:
        mesh_context = {
            "mass": 1e12,
            "energy": 1e12,
            "entropy": 1e12,
            "cycle": 1e12,
        }
    tokens = tokenize(code)
    parser = Parser(tokens)
    program = parser.parse()
    program = resolve_imports(program, source_path)
    compiler = Compiler(mesh_context)
    return compiler.compile(program)
