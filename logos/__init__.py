"""
Logos — A Compiler for Physical Reality
========================================

Public API surface for the Logos declarative state machine language.
"""

from .lexer import tokenize, Token
from .parser import Parser
from .compiler import Compiler, resolve_imports
from .interpreter import LogosVM
from .exceptions import (
    LogosCompilerError,
    LogosSyntaxError,
    ThermodynamicConstraintError,
    CyclicImportError,
    LogosRuntimeError,
    TransitionFrozenError,
)


def compile_logos(code: str, mesh_context: dict, source_path: str = "<stdin>") -> dict:
    """
    Parse, resolve imports, verify thermodynamics, and compile Logos source
    into a JSON State Machine IR (SMIR).

    Parameters
    ----------
    code : str
        Logos source code.
    mesh_context : dict[str, float]
        Physical resource pool for the deployment mesh.
    source_path : str
        File path of the source (used for relative import resolution).

    Returns
    -------
    dict
        The compiled SMIR ready for execution by ``LogosVM``.

    Raises
    ------
    LogosSyntaxError
        On parse or lexer errors.
    ThermodynamicConstraintError
        When the mesh cannot satisfy declared resource requirements.
    CyclicImportError
        When the import graph contains a cycle.
    """
    tokens = tokenize(code)
    parser = Parser(tokens)
    program = parser.parse()
    program = resolve_imports(program, source_path)
    compiler = Compiler(mesh_context)
    return compiler.compile(program)
