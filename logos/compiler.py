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

    def compile_to_binary(self, program: ProgramNode) -> bytes:
        """Compile the program and return the dense binary VSMB bytecode."""
        smir = self.compile(program)
        from .vsmb import encode_vsmb
        return encode_vsmb(smir)

    def compile_to_c(self, program: ProgramNode | dict) -> str:
        """Compile the Logos program directly into freestanding, native C code."""
        if isinstance(program, dict):
            smir = program
        else:
            smir = self.compile(program)
            
        def find_identifiers(expr):
            if expr["type"] == "literal":
                if expr["value_type"] == "IDENTIFIER":
                    return {expr["value"]}
            elif expr["type"] == "binary":
                return find_identifiers(expr["left"]) | find_identifiers(expr["right"])
            elif expr["type"] == "unary":
                return find_identifiers(expr["expr"])
            return set()
            
        guard_vars = set()
        for intent in smir["intents"]:
            for state in intent["states"]:
                for trans in state["transitions"]:
                    if "guard" in trans:
                        guard_vars.update(find_identifiers(trans["guard"]["expr"]))
                        
        all_vars = {"priority", "is_inter_subnet", "replayed", "is_valid_sig", "is_authorized", "request_size", "limit", "enabled"} | guard_vars
        
        C_PART1 = """#include <stdio.h>
#include <stdlib.h>
#include <string.h>

double safe_div(double a, double b) {
    if (b == 0.0) return 0.0;
    return a / b;
}

void print_escaped(FILE* f, const char* s) {
    for (int i = 0; s[i] != '\\0'; i++) {
        if (s[i] == '\\\\') fprintf(f, "\\\\\\\\");
        else if (s[i] == '"') fprintf(f, "\\\\\\"");
        else if (s[i] == '\\n') fprintf(f, "\\\\n");
        else fputc(s[i], f);
    }
}
"""
        c2 = []
        c2.append("struct MeshContext {")
        c2.append("    double mass;")
        c2.append("    double energy;")
        c2.append("    double entropy;")
        c2.append("    double cycle;")
        c2.append("};")
        c2.append("")
        c2.append("struct MeshContext mesh = {1e12, 1e12, 1e12, 1e12};")
        c2.append("")
        c2.append("// Runtime context guard variables")
        for var in sorted(all_vars):
            init_val = "1.0" if var == "enabled" else ("10000.0" if var == "limit" else "0.0")
            c2.append(f"double {var} = {init_val};")
        c2.append("")
        c2.append("struct TransitionResult {")
        c2.append("    const char* status;")
        c2.append("    const char* from;")
        c2.append("    const char* to;")
        c2.append("    const char* detail;")
        c2.append("};")
        c2.append("")
        
        for intent in smir["intents"]:
            name = intent["name"]
            initial_state = intent["states"][0]["name"] if intent["states"] else "Idle"
            c2.append(f"const char* {name.lower()}_state = \"{initial_state}\";")
            
        c2.append("")
        c2.append("struct TransitionResult process_event(const char* intent, const char* event) {")
        c2.append("    struct TransitionResult res;")
        c2.append("    res.status = \"no_match\";")
        c2.append("    res.from = \"\";")
        c2.append("    res.to = \"\";")
        c2.append("    res.detail = \"\";")
        c2.append("")
        c2.append("    struct MeshContext backup = mesh; // Transaction register backup")
        c2.append("")
        
        for intent in smir["intents"]:
            name = intent["name"]
            c2.append(f"    if (strcmp(intent, \"{name}\") == 0) {{")
            c2.append(f"        res.from = {name.lower()}_state;")
            c2.append(f"        res.to = {name.lower()}_state;")
            c2.append("")
            
            for state in intent["states"]:
                state_name = state["name"]
                c2.append(f"        if (strcmp({name.lower()}_state, \"{state_name}\") == 0) {{")
                
                for trans in state["transitions"]:
                    evt = trans["event"]
                    target = trans["target"]
                    c2.append(f"            if (strcmp(event, \"{evt}\") == 0) {{")
                    
                    guard_check = "1"
                    if "guard" in trans:
                        def compile_expr(expr):
                            etype = expr["type"]
                            if etype == "literal":
                                vtype = expr["value_type"]
                                val = expr["value"]
                                if vtype == "IDENTIFIER":
                                    return str(val)
                                elif vtype == "PERCENT":
                                    return f"({float(val) / 100.0})"
                                elif vtype == "NUMBER":
                                    return str(val)
                                elif vtype == "STRING":
                                    return f"\"{val}\""
                            elif etype == "binary":
                                op = expr["op"]
                                if op == "and":
                                    return f"({compile_expr(expr['left'])} && {compile_expr(expr['right'])})"
                                elif op == "or":
                                    return f"({compile_expr(expr['left'])} || {compile_expr(expr['right'])})"
                                elif op == "/":
                                    return f"safe_div({compile_expr(expr['left'])}, {compile_expr(expr['right'])})"
                                return f"({compile_expr(expr['left'])} {op} {compile_expr(expr['right'])})"
                            elif etype == "unary":
                                op = expr["op"]
                                if op == "not":
                                    op = "!"
                                return f"({op}{compile_expr(expr['expr'])})"
                            return "0"
                        guard_check = compile_expr(trans["guard"]["expr"])
                        
                    c2.append(f"                if ({guard_check}) {{")
                    
                    reqs = trans.get("requires", [])
                    for r in reqs:
                        res_name = r["resource"]
                        val = r["value"]
                        multiplier = 1.0618 if res_name in ("energy", "cycle") else 1.0
                        total_deduct = val * multiplier
                        
                        c2.append(f"                    if (mesh.{res_name} < {total_deduct}) {{")
                        c2.append(f"                        res.status = \"blocked\";")
                        c2.append(f"                        res.detail = \"Insufficient {res_name} (with 6.18% fee). Transition FROZEN.\";")
                        c2.append(f"                        mesh = backup; // Rollback registers")
                        c2.append(f"                        return res;")
                        c2.append(f"                    }}")
                        c2.append(f"                    mesh.{res_name} -= {total_deduct};")
                        
                    consts = intent.get("constraints", [])
                    for c in consts:
                        res_name = c["resource"]
                        op = c["operator"]
                        val = c["value"]
                        violation_check = "0"
                        if op == "max":
                            violation_check = f"mesh.{res_name} > {val}"
                        elif op == "min":
                            violation_check = f"mesh.{res_name} < {val}"
                        elif op == "<":
                            violation_check = f"!(mesh.{res_name} < {val})"
                        elif op == ">":
                            violation_check = f"!(mesh.{res_name} > {val})"
                        elif op == "<=":
                            violation_check = f"!(mesh.{res_name} <= {val})"
                        elif op == ">=":
                            violation_check = f"!(mesh.{res_name} >= {val})"
                        elif op == "==":
                            violation_check = f"mesh.{res_name} != {val}"
                        elif op == "!=":
                            violation_check = f"mesh.{res_name} == {val}"
                            
                        c2.append(f"                    if ({violation_check}) {{")
                        c2.append(f"                        res.status = \"blocked\";")
                        c2.append(f"                        res.detail = \"Constraint violation on {res_name}.\";")
                        c2.append(f"                        mesh = backup; // Rollback registers")
                        c2.append(f"                        return res;")
                        c2.append(f"                    }}")
                        
                    c2.append(f"                    {name.lower()}_state = \"{target}\";")
                    c2.append(f"                    res.to = \"{target}\";")
                    c2.append(f"                    res.status = \"transitioned\";")
                    c2.append(f"                    res.detail = \"OK\";")
                    c2.append(f"                    return res;")
                    c2.append(f"                }}")
                    c2.append(f"            }}")
                    
                c2.append(f"        }}")
                
            c2.append(f"    }}")
            
        c2.append("    return res;")
        c2.append("}")
        c2.append("")
        c2.append("void parse_mesh(const char* filepath) {")
        c2.append("    FILE* f = fopen(filepath, \"r\");")
        c2.append("    if (!f) return;")
        c2.append("    char buf[4096];")
        c2.append("    size_t len = fread(buf, 1, sizeof(buf) - 1, f);")
        c2.append("    buf[len] = '\\0';")
        c2.append("    fclose(f);")
        c2.append("")
        c2.append("    char* p;")
        c2.append("    if ((p = strstr(buf, \"\\\"mass\\\"\"))) {")
        c2.append("        sscanf(p + 6, \"%*[: \\t]%lf\", &mesh.mass);")
        c2.append("    }")
        c2.append("    if ((p = strstr(buf, \"\\\"energy\\\"\"))) {")
        c2.append("        sscanf(p + 8, \"%*[: \\t]%lf\", &mesh.energy);")
        c2.append("    }")
        c2.append("    if ((p = strstr(buf, \"\\\"entropy\\\"\"))) {")
        c2.append("        sscanf(p + 9, \"%*[: \\t]%lf\", &mesh.entropy);")
        c2.append("    }")
        c2.append("    if ((p = strstr(buf, \"\\\"cycle\\\"\"))) {")
        c2.append("        sscanf(p + 7, \"%*[: \\t]%lf\", &mesh.cycle);")
        c2.append("    }")
        c2.append("}")
        c2.append("")
        c2.append("void parse_context(const char* filepath) {")
        c2.append("    FILE* f = fopen(filepath, \"r\");")
        c2.append("    if (!f) return;")
        c2.append("    char buf[4096];")
        c2.append("    size_t len = fread(buf, 1, sizeof(buf) - 1, f);")
        c2.append("    buf[len] = '\\0';")
        c2.append("    fclose(f);")
        c2.append("")
        c2.append("    char* p;")
        for var in sorted(all_vars):
            c2.append(f"    if ((p = strstr(buf, \"\\\"{var}\\\"\"))) {{")
            c2.append(f"        sscanf(p + {len(var) + 2}, \"%*[: \\t]%lf\", &{var});")
            c2.append(f"    }}")
        for intent in smir["intents"]:
            name = intent["name"]
            var_name = f"{name.lower()}_state"
            c2.append(f"    if ((p = strstr(buf, \"\\\"{var_name}\\\"\"))) {{")
            c2.append(f"        static char state_buf_{name.lower()}[128];")
            c2.append(f"        if (sscanf(p + {len(var_name) + 2}, \"%*[: \\t\\\"]%127[^\\\"]\", state_buf_{name.lower()}) == 1) {{")
            c2.append(f"            {var_name} = state_buf_{name.lower()};")
            c2.append(f"        }}")
            c2.append(f"    }}")
        c2.append("}")
        c2.append("")
        c2.append("void run_events(const char* filepath) {")
        c2.append("    FILE* f = fopen(filepath, \"r\");")
        c2.append("    if (!f) return;")
        c2.append("    char buf[65536];")
        c2.append("    size_t len = fread(buf, 1, sizeof(buf) - 1, f);")
        c2.append("    buf[len] = '\\0';")
        c2.append("    fclose(f);")
        c2.append("")
        c2.append("    int event_index = 0;")
        c2.append("    char* obj_start = strchr(buf, '{');")
        c2.append("    while (obj_start) {")
        c2.append("        char* obj_end = strchr(obj_start, '}');")
        c2.append("        if (!obj_end) break;")
        c2.append("        *obj_end = '\\0';")
        c2.append("")
        c2.append("        char intent[128] = {0};")
        c2.append("        char event[128] = {0};")
        c2.append("")
        c2.append("        char* p;")
        c2.append("        if ((p = strstr(obj_start, \"\\\"intent\\\"\"))) {")
        c2.append("            sscanf(p + 8, \"%*[: \\t\\\"]%127[^\\\"]\", intent);")
        c2.append("        }")
        c2.append("        if ((p = strstr(obj_start, \"\\\"event\\\"\"))) {")
        c2.append("            sscanf(p + 7, \"%*[: \\t\\\"]%127[^\\\"]\", event);")
        c2.append("        }")
        for var in sorted(all_vars):
            c2.append(f"        if ((p = strstr(obj_start, \"\\\"{var}\\\"\"))) {{")
            c2.append(f"            sscanf(p + {len(var) + 2}, \"%*[: \\t]%lf\", &{var});")
            c2.append(f"        }}")
        c2.append("")
        c2.append("        struct TransitionResult res = process_event(intent, event);")
        c2.append("        char icon = '?';")
        c2.append("        if (strcmp(res.status, \"transitioned\") == 0) icon = '+';")
        c2.append("        else if (strcmp(res.status, \"blocked\") == 0) icon = '-';")
        c2.append("")
        c2.append("        printf(\"[EVENT %d] %c %s --(%s)--> %s [%s]\\n\", event_index, icon, res.from, event, res.to, res.status);")
        c2.append("        if (strcmp(res.status, \"transitioned\") != 0) {")
        c2.append("            printf(\"          Detail: %s\\n\", res.detail);")
        c2.append("        }")
        c2.append("")
        c2.append("        event_index++;")
        c2.append("        obj_start = strchr(obj_end + 1, '{');")
        c2.append("    }")
        c2.append("")
        c2.append("    printf(\"\\n[LOGOS VM] Execution complete.\\n\");")
        c2.append("    printf(\"[LOGOS VM] Final mesh:\\n\");")
        c2.append("    printf(\"  mass: %.4f\\n\", mesh.mass);")
        c2.append("    printf(\"  energy: %.4f\\n\", mesh.energy);")
        c2.append("    printf(\"  entropy: %.4f\\n\", mesh.entropy);")
        c2.append("    printf(\"  cycle: %.4f\\n\", mesh.cycle);")
        c2.append("}")
        c2.append("")
        c2.append("int main(int argc, char** argv) {")
        c2.append("    if (argc < 2) {")
        c2.append("        printf(\"Usage: logos_app <events.json> [-m mesh.json] [-c context.json] [-o output_file]\\n\");")
        c2.append("        return 0;")
        c2.append("    }")
        c2.append("")
        c2.append("    const char* events_path = argv[1];")
        c2.append("    const char* output_path = NULL;")
        c2.append("    for (int i = 2; i < argc; i++) {")
        c2.append("        if (strcmp(argv[i], \"-m\") == 0 && i + 1 < argc) {")
        c2.append("            parse_mesh(argv[i+1]);")
        c2.append("            i++;")
        c2.append("        } else if (strcmp(argv[i], \"-c\") == 0 && i + 1 < argc) {")
        c2.append("            parse_context(argv[i+1]);")
        c2.append("            i++;")
        c2.append("        } else if (strcmp(argv[i], \"-o\") == 0 && i + 1 < argc) {")
        c2.append("            output_path = argv[i+1];")
        c2.append("            i++;")
        c2.append("        }")
        c2.append("    }")
        c2.append("")
        c2.append("    run_events(events_path);")
        c2.append("")
        c2.append("    if (output_path != NULL) {")
        c2.append("        FILE* out_f = fopen(output_path, \"w\");")
        c2.append("        if (out_f) {")
        c2.append("            fprintf(out_f, \"%s\", C_PART1);")
        c2.append("            fprintf(out_f, \"const char* C_PART1 = \\\"\");")
        c2.append("            print_escaped(out_f, C_PART1);")
        c2.append("            fprintf(out_f, \"\\\";\\nconst char* C_PART2 = \\\"\");")
        c2.append("            print_escaped(out_f, C_PART2);")
        c2.append("            fprintf(out_f, \"\\\";\\n\");")
        c2.append("            fprintf(out_f, \"%s\", C_PART2);")
        c2.append("            fclose(out_f);")
        c2.append("        }")
        c2.append("    }")
        c2.append("    return 0;")
        c2.append("}")
        
        C_PART2 = "\n".join(c2)
        def escape_c_str(s: str) -> str:
            res = []
            for char in s:
                if char == '\\':
                    res.append('\\\\')
                elif char == '"':
                    res.append('\\"')
                elif char == '\n':
                    res.append('\\n')
                elif char == '\r':
                    continue
                else:
                    res.append(char)
            return "".join(res)
            
        escaped_c1 = escape_c_str(C_PART1)
        escaped_c2 = escape_c_str(C_PART2)
        return C_PART1 + f'const char* C_PART1 = "{escaped_c1}";\nconst char* C_PART2 = "{escaped_c2}";\n' + C_PART2


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
