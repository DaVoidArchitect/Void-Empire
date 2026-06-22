import sys
import os
import json
import tempfile
import subprocess
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logos.lexer import tokenize, LogosSyntaxError
from logos.parser import Parser
from logos.compiler import Compiler, ThermodynamicConstraintError
from logos.interpreter import LogosVM, LogosRuntimeError
from logos.exceptions import CyclicImportError, TransitionFrozenError, LogosCompilerError

def run_test_suite():
    tests_run = 0
    tests_passed = 0
    bugs_found = []

    def test_case(category, name, fn):
        nonlocal tests_run, tests_passed
        tests_run += 1
        print(f"[{category}] Running {name}... ", end="", flush=True)
        try:
            fn()
            print("PASSED")
            tests_passed += 1
        except AssertionError as e:
            print(f"FAILED (AssertionError)")
            bugs_found.append(f"{category} - {name}: AssertionError: {str(e)}")
        except Exception as e:
            print(f"FAILED (Unhandled Exception: {type(e).__name__}: {str(e)})")
            bugs_found.append(f"{category} - {name}: Unhandled crash ({type(e).__name__}: {str(e)})")

    # ==========================================
    # LEXER CHAOS
    # ==========================================
    
    def lex_only_whitespace():
        tokens = tokenize("   \n  \t   \r\n")
        assert len(tokens) == 0, f"Expected 0 tokens, got {len(tokens)}"
    test_case("Lexer", "only_whitespace", lex_only_whitespace)

    def lex_only_comments():
        tokens = tokenize("# comment\n# another comment")
        assert len(tokens) == 0, f"Expected 0 tokens, got {len(tokens)}"
    test_case("Lexer", "only_comments", lex_only_comments)

    def lex_illegal_unicode():
        try:
            tokenize("intent T { steward: \"🚀💥 \u200b\"; }")
        except LogosSyntaxError as e:
            assert e.line > 0, "Expected line number in LogosSyntaxError"
    test_case("Lexer", "illegal_unicode", lex_illegal_unicode)

    def lex_extremely_long_id():
        long_id = "A" * 15000
        code = f"intent {long_id} {{}}"
        tokens = tokenize(code)
        assert len(tokens) > 0, "Expected tokens for long identifier"
        assert tokens[1].value == long_id, "Identifier value mismatch"
    test_case("Lexer", "extremely_long_id", lex_extremely_long_id)

    def lex_deeply_nested_brackets():
        code = "[[[[[[[[[[]]]]]]]]]]"
        tokens = tokenize(code)
        assert len(tokens) == 20, f"Expected 20 tokens, got {len(tokens)}"
    test_case("Lexer", "deeply_nested_brackets", lex_deeply_nested_brackets)

    def lex_unclosed_string():
        try:
            tokenize("intent T { steward: \"unclosed; }")
            raise AssertionError("Expected LogosSyntaxError for unclosed string")
        except LogosSyntaxError as e:
            assert e.line > 0
    test_case("Lexer", "unclosed_string", lex_unclosed_string)

    def lex_null_bytes():
        try:
            tokenize("intent T\x00 { steward: \"test\"; }")
        except LogosSyntaxError:
            pass  # Parser or Lexer error is acceptable
    test_case("Lexer", "embedded_null_bytes", lex_null_bytes)

    # ==========================================
    # PARSER CHAOS
    # ==========================================

    def parse_empty_intent_bodies():
        tokens = tokenize("intent T {}")
        prog = Parser(tokens).parse()
        assert len(prog.intents) == 1
    test_case("Parser", "empty_intent_bodies", parse_empty_intent_bodies)

    def parse_duplicate_require():
        code = "intent T { require { energy 10 J; } require { mass 1 kg; } }"
        try:
            Parser(tokenize(code)).parse()
            raise AssertionError("Expected LogosSyntaxError for duplicate require blocks")
        except LogosSyntaxError:
            pass
    test_case("Parser", "duplicate_require", parse_duplicate_require)

    def parse_duplicate_constraint():
        code = "intent T { constraint { energy max 10 J; } constraint { mass max 1 kg; } }"
        try:
            Parser(tokenize(code)).parse()
            raise AssertionError("Expected LogosSyntaxError for duplicate constraint blocks")
        except LogosSyntaxError:
            pass
    test_case("Parser", "duplicate_constraint", parse_duplicate_constraint)

    def parse_missing_semicolons():
        code = "intent T { steward: \"T\" require { energy 10 J } state S { on e -> S } }"
        try:
            Parser(tokenize(code)).parse()
            raise AssertionError("Expected LogosSyntaxError for missing semicolons")
        except LogosSyntaxError:
            pass
    test_case("Parser", "missing_semicolons", parse_missing_semicolons)

    def parse_missing_closing_braces():
        code = "intent T { state S { on e -> S"
        try:
            Parser(tokenize(code)).parse()
            raise AssertionError("Expected LogosSyntaxError for missing closing braces")
        except LogosSyntaxError:
            pass
    test_case("Parser", "missing_closing_braces", parse_missing_closing_braces)

    def parse_transition_without_target():
        code = "intent T { state S { on e -> ; } }"
        try:
            Parser(tokenize(code)).parse()
            raise AssertionError("Expected LogosSyntaxError for missing transition target")
        except LogosSyntaxError:
            pass
    test_case("Parser", "transition_without_target", parse_transition_without_target)

    def parse_guard_without_closing_bracket():
        code = "intent T { state S { on e [val == 1 -> S; } }"
        try:
            Parser(tokenize(code)).parse()
            raise AssertionError("Expected LogosSyntaxError for unclosed guard bracket")
        except LogosSyntaxError:
            pass
    test_case("Parser", "guard_without_closing_bracket", parse_guard_without_closing_bracket)

    def parse_import_with_non_string():
        code = "import 123;"
        try:
            Parser(tokenize(code)).parse()
            raise AssertionError("Expected LogosSyntaxError for non-string import path")
        except LogosSyntaxError:
            pass
    test_case("Parser", "import_with_non_string", parse_import_with_non_string)

    def parse_state_no_transitions():
        code = "intent T { state S {} }"
        prog = Parser(tokenize(code)).parse()
        assert len(prog.intents[0].states) == 1
    test_case("Parser", "state_no_transitions", parse_state_no_transitions)

    def parse_intent_no_states():
        code = "intent T { require { energy 10 J; } }"
        prog = Parser(tokenize(code)).parse()
        assert len(prog.intents[0].states) == 0
    test_case("Parser", "intent_no_states", parse_intent_no_states)

    def parse_nested_guard_expressions():
        nesting = "(" * 150 + "1 == 1" + ")" * 150
        code = f"intent T {{ state S {{ on e [{nesting}] -> S; }} }}"
        try:
            prog = Parser(tokenize(code)).parse()
            assert prog is not None
        except LogosSyntaxError:
            pass
    test_case("Parser", "nested_guard_expressions", parse_nested_guard_expressions)

    # ==========================================
    # COMPILER CHAOS
    # ==========================================

    def compile_mesh_zero_values():
        mesh = {'mass': 0.0, 'energy': 0.0, 'entropy': 0.0, 'cycle': 0.0}
        code = "intent T { require { energy 10 J; } }"
        prog = Parser(tokenize(code)).parse()
        try:
            Compiler(mesh).compile(prog)
            raise AssertionError("Expected ThermodynamicConstraintError for zero mesh capacity")
        except ThermodynamicConstraintError as e:
            assert "energy" in str(e).lower()
    test_case("Compiler", "mesh_zero_values", compile_mesh_zero_values)

    def compile_mesh_negative_values():
        mesh = {'mass': -10.0, 'energy': -100.0, 'entropy': 0.0, 'cycle': 0.0}
        code = "intent T { require { energy 10 J; } }"
        prog = Parser(tokenize(code)).parse()
        try:
            Compiler(mesh).compile(prog)
            raise AssertionError("Expected ThermodynamicConstraintError or LogosCompilerError for negative resources")
        except (ThermodynamicConstraintError, LogosCompilerError):
            pass
    test_case("Compiler", "mesh_negative_values", compile_mesh_negative_values)

    def compile_mesh_missing_keys():
        mesh = {'mass': 100.0}
        code = "intent T { require { energy 10 J; } }"
        prog = Parser(tokenize(code)).parse()
        try:
            Compiler(mesh).compile(prog)
            raise AssertionError("Expected error for missing mesh context keys")
        except Exception:
            pass
    test_case("Compiler", "mesh_missing_keys", compile_mesh_missing_keys)

    def compile_exceed_mesh_by_epsilon():
        mesh = {'mass': 100.0, 'energy': 100.0, 'entropy': 0.1, 'cycle': 0.9}
        code = "intent T { require { energy 100.000001 J; } }"
        prog = Parser(tokenize(code)).parse()
        try:
            Compiler(mesh).compile(prog)
            raise AssertionError("Expected ThermodynamicConstraintError for epsilon overflow")
        except ThermodynamicConstraintError:
            pass
    test_case("Compiler", "exceed_mesh_by_epsilon", compile_exceed_mesh_by_epsilon)

    def compile_requirements_exact_zero():
        mesh = {'mass': 100.0, 'energy': 100.0, 'entropy': 0.1, 'cycle': 0.9}
        code = "intent T { require { energy 0.0 J; } }"
        prog = Parser(tokenize(code)).parse()
        Compiler(mesh).compile(prog)
    test_case("Compiler", "requirements_exact_zero", compile_requirements_exact_zero)

    def compile_unknown_units():
        code = "intent T { require { energy 10 calories; } }"
        try:
            Parser(tokenize(code)).parse()
        except LogosSyntaxError:
            pass
    test_case("Compiler", "unknown_units", compile_unknown_units)

    def compile_cyclic_imports():
        with tempfile.TemporaryDirectory() as tmpdir:
            a_path = os.path.join(tmpdir, "a.logos")
            b_path = os.path.join(tmpdir, "b.logos")
            with open(a_path, "w") as f:
                f.write('import "b.logos";\nintent A { state S {} }')
            with open(b_path, "w") as f:
                f.write('import "a.logos";\nintent B { state S {} }')
            
            from logos.compiler import resolve_imports
            prog = Parser(tokenize(open(a_path).read())).parse()
            try:
                resolve_imports(prog, a_path)
                raise AssertionError("Expected LogosSyntaxError/CyclicImportError for cyclic import")
            except (LogosSyntaxError, CyclicImportError) as e:
                assert "cyclic" in str(e).lower()
    test_case("Compiler", "cyclic_imports", compile_cyclic_imports)

    def compile_diamond_imports():
        with tempfile.TemporaryDirectory() as tmpdir:
            a_path = os.path.join(tmpdir, "a.logos")
            b_path = os.path.join(tmpdir, "b.logos")
            c_path = os.path.join(tmpdir, "c.logos")
            d_path = os.path.join(tmpdir, "d.logos")
            with open(a_path, "w") as f:
                f.write('import "b.logos";\nimport "c.logos";\nintent A { state S {} }')
            with open(b_path, "w") as f:
                f.write('import "d.logos";\nintent B { state S {} }')
            with open(c_path, "w") as f:
                f.write('import "d.logos";\nintent C { state S {} }')
            with open(d_path, "w") as f:
                f.write('intent D { state S {} }')
            
            from logos.compiler import resolve_imports
            prog = Parser(tokenize(open(a_path).read())).parse()
            merged = resolve_imports(prog, a_path)
            assert len(merged.intents) >= 4
    test_case("Compiler", "diamond_imports", compile_diamond_imports)

    def compile_nonexistent_imports():
        with tempfile.TemporaryDirectory() as tmpdir:
            a_path = os.path.join(tmpdir, "a.logos")
            with open(a_path, "w") as f:
                f.write('import "missing.logos";\nintent A { state S {} }')
            from logos.compiler import resolve_imports
            prog = Parser(tokenize(open(a_path).read())).parse()
            try:
                resolve_imports(prog, a_path)
                raise AssertionError("Expected FileNotFoundError or LogosCompilerError for missing import")
            except Exception:
                pass
    test_case("Compiler", "nonexistent_imports", compile_nonexistent_imports)

    def compile_extremely_large_numbers():
        mesh = {'mass': 1e308, 'energy': 1e308, 'entropy': 0.1, 'cycle': 0.9}
        code = "intent T { require { energy 1e308 J; } }"
        prog = Parser(tokenize(code)).parse()
        Compiler(mesh).compile(prog)
    test_case("Compiler", "extremely_large_numbers", compile_extremely_large_numbers)

    # ==========================================
    # VM CHAOS
    # ==========================================

    def vm_event_nonexistent_intent():
        mesh = {'mass': 100.0, 'energy': 100.0, 'entropy': 0.1, 'cycle': 0.9}
        code = "intent T { state Init { on go -> End; } state End {} }"
        smir = Compiler(mesh).compile(Parser(tokenize(code)).parse())
        vm = LogosVM(smir, mesh)
        try:
            vm.send_event("NonExistent", "go")
            raise AssertionError("Expected LogosRuntimeError for non-existent intent")
        except LogosRuntimeError:
            pass
    test_case("VM", "event_nonexistent_intent", vm_event_nonexistent_intent)

    def vm_event_nonexistent_event():
        mesh = {'mass': 100.0, 'energy': 100.0, 'entropy': 0.1, 'cycle': 0.9}
        code = "intent T { state Init { on go -> End; } state End {} }"
        smir = Compiler(mesh).compile(Parser(tokenize(code)).parse())
        vm = LogosVM(smir, mesh, {'t_state': 'Init'})
        res = vm.send_event("T", "non_existent")
        assert res['status'] == 'no_match'
    test_case("VM", "event_nonexistent_event", vm_event_nonexistent_event)

    def vm_event_after_terminal():
        mesh = {'mass': 100.0, 'energy': 100.0, 'entropy': 0.1, 'cycle': 0.9}
        code = "intent T { state Init { on go -> End; } state End {} }"
        smir = Compiler(mesh).compile(Parser(tokenize(code)).parse())
        vm = LogosVM(smir, mesh, {'t_state': 'Init'})
        vm.send_event("T", "go")
        res = vm.send_event("T", "go")
        assert res['status'] == 'no_match'
    test_case("VM", "event_after_terminal", vm_event_after_terminal)

    def vm_event_1000_times():
        mesh = {'mass': 100.0, 'energy': 100.0, 'entropy': 0.1, 'cycle': 0.9}
        code = "intent T { state Init { on go -> End; } state End {} }"
        smir = Compiler(mesh).compile(Parser(tokenize(code)).parse())
        vm = LogosVM(smir, mesh, {'t_state': 'Init'})
        vm.send_event("T", "go")
        for _ in range(1000):
            res = vm.send_event("T", "go")
            assert res['status'] == 'no_match'
    test_case("VM", "event_1000_times", vm_event_1000_times)

    def vm_resource_exhaustion():
        mesh = {'mass': 1000.0, 'energy': 60.0, 'entropy': 0.01, 'cycle': 0.99}
        code = "intent T { state Init { on loop -> Init { require energy 10.0 J; } } }"
        smir = Compiler(mesh).compile(Parser(tokenize(code)).parse())
        vm = LogosVM(smir, mesh, {'t_state': 'Init'})
        for i in range(5):
            res = vm.send_event("T", "loop")
            assert res['status'] == 'transitioned'
        try:
            vm.send_event("T", "loop")
            raise AssertionError("Expected error or blocking behavior for resource depletion")
        except (LogosRuntimeError, ThermodynamicConstraintError):
            pass
    test_case("VM", "resource_exhaustion", vm_resource_exhaustion)

    def vm_division_by_zero():
        code = "intent T { state Init { on go [1 / 0 == 0] -> End; } state End {} }"
        try:
            prog = Parser(tokenize(code)).parse()
            mesh = {'mass': 100.0, 'energy': 100.0, 'entropy': 0.1, 'cycle': 0.9}
            smir = Compiler(mesh).compile(prog)
            vm = LogosVM(smir, mesh, {'t_state': 'Init'})
            vm.send_event("T", "go")
        except (LogosSyntaxError, LogosRuntimeError):
            pass
    test_case("VM", "division_by_zero", vm_division_by_zero)

    def vm_guard_missing_keys():
        code = "intent T { state Init { on go [missing == 1] -> End; } state End {} }"
        mesh = {'mass': 100.0, 'energy': 100.0, 'entropy': 0.1, 'cycle': 0.9}
        smir = Compiler(mesh).compile(Parser(tokenize(code)).parse())
        vm = LogosVM(smir, mesh, {'t_state': 'Init'})
        res = vm.send_event("T", "go")
        assert res['status'] == 'no_match'
    test_case("VM", "guard_missing_keys", vm_guard_missing_keys)

    def vm_empty_context_guarded():
        code = "intent T { state Init { on go [enabled == 1] -> End; } state End {} }"
        mesh = {'mass': 100.0, 'energy': 100.0, 'entropy': 0.1, 'cycle': 0.9}
        smir = Compiler(mesh).compile(Parser(tokenize(code)).parse())
        vm = LogosVM(smir, mesh)
        res = vm.send_event("T", "go")
        assert res['status'] == 'no_match'
    test_case("VM", "empty_context_guarded", vm_empty_context_guarded)

    def vm_constraint_boundary():
        mesh = {'mass': 100.0, 'energy': 100.0, 'entropy': 0.1, 'cycle': 0.9}
        code = "intent T { require { energy 100.0 J; } }"
        smir = Compiler(mesh).compile(Parser(tokenize(code)).parse())
        assert smir is not None
    test_case("VM", "constraint_boundary", vm_constraint_boundary)

    # ==========================================
    # INTEGRATION CHAOS
    # ==========================================

    def integration_corrupted_smir():
        mesh = {'mass': 100.0, 'energy': 100.0, 'entropy': 0.1, 'cycle': 0.9}
        corrupt_smir = '{"logos_version": "2.0-declarative", "intents": [{"name": "T", "states": [{"name": "Init", "transitions": [{"event": "go", "target": "End"}]}]}]}'
        try:
            vm = LogosVM(corrupt_smir, mesh)
            vm.send_event("T", "go")
        except (LogosRuntimeError, KeyError):
            pass
    test_case("Integration", "corrupted_smir", integration_corrupted_smir)

    def integration_logosc_nonexistent_file():
        res = subprocess.run(["logos/bin/logosc.exe", "non_existent.logos"], capture_output=True, text=True)
        assert res.returncode == 1
        assert "source file not found" in res.stderr.lower() or "source file not found" in res.stdout.lower()
    test_case("Integration", "logosc_nonexistent_file", integration_logosc_nonexistent_file)

    def integration_logosc_binary_file():
        res = subprocess.run(["logos/bin/logosc.exe", "logos/bin/logosc.exe"], capture_output=True, text=True)
        assert res.returncode != 0
    test_case("Integration", "logosc_binary_file", integration_logosc_binary_file)

    def integration_logos_vm_nonexistent_file():
        res = subprocess.run(["logos/bin/logos_vm.exe", "non_existent.smir.json"], capture_output=True, text=True)
        assert res.returncode == 1
        assert "smir file not found" in res.stderr.lower() or "smir file not found" in res.stdout.lower()
    test_case("Integration", "logos_vm_nonexistent_file", integration_logos_vm_nonexistent_file)

    # ==========================================
    # SUMMARY
    # ==========================================
    print("\n==========================================")
    print("           CHAOS TEST SUMMARY")
    print("==========================================")
    print(f"Total Tests Run: {tests_run}")
    print(f"Passed: {tests_passed}")
    print(f"Failed (Bugs): {len(bugs_found)}")
    if bugs_found:
        print("\nNature of bugs found:")
        for bug in bugs_found:
            print(f"- {bug}")
    else:
        print("\nNo bugs discovered during chaos testing.")
    print("==========================================")
    
    verdict = "HARDENED" if len(bugs_found) == 0 else "NOT HARDENED"
    print(f"VERDICT: {verdict}")

if __name__ == '__main__':
    run_test_suite()
