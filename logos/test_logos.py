#!/usr/bin/env python3
"""
Logos Test Suite — Comprehensive Coverage for the Declarative State Machine Language

Tests cover:
  1.  Lexer — token generation, keywords, resources, units
  2.  Parser — full grammar coverage (imports, intents, headers, require,
      constraint, states, transitions with guards and transition-level requires)
  3.  Compiler — SI normalisation, thermodynamic verification, guard compilation
  4.  VM — atomic state rollover, guard evaluation, constraint enforcement,
      event processing, audit trail
  5.  Error paths — syntax errors, resource deficits, cyclic imports
"""

import os
import sys
import json
import tempfile
import unittest

# Ensure the logos package is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logos.lexer import tokenize
from logos.parser import Parser
from logos.compiler import Compiler, resolve_imports, normalise_resource
from logos.interpreter import LogosVM
from logos.exceptions import (
    LogosSyntaxError,
    ThermodynamicConstraintError,
    LogosRuntimeError,
)
from logos import compile_logos


# ==========================================================================
# 1. LEXER TESTS
# ==========================================================================

class TestLexer(unittest.TestCase):

    def test_empty_source(self):
        tokens = tokenize("")
        self.assertEqual(tokens, [])

    def test_comments_are_stripped(self):
        tokens = tokenize("// this is a comment\n# so is this\n")
        self.assertEqual(tokens, [])

    def test_keywords(self):
        tokens = tokenize("intent require constraint state on import")
        types = [t.type for t in tokens]
        self.assertTrue(all(t == 'KEYWORD' for t in types))
        vals = [t.value for t in tokens]
        self.assertEqual(vals, ["intent", "require", "constraint", "state", "on", "import"])

    def test_resources(self):
        tokens = tokenize("mass energy entropy cycle")
        types = [t.type for t in tokens]
        self.assertTrue(all(t == 'RESOURCE' for t in types))

    def test_units(self):
        tokens = tokenize("kg g kWh MWh Wh J kJ days hours cycles")
        types = [t.type for t in tokens]
        self.assertTrue(all(t == 'UNIT' for t in types))

    def test_numbers(self):
        tokens = tokenize("42 3.14 0.001")
        self.assertEqual(len(tokens), 3)
        self.assertTrue(all(t.type == 'NUMBER' for t in tokens))

    def test_string_literal(self):
        tokens = tokenize('"hello world"')
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, 'STRING')
        self.assertEqual(tokens[0].value, 'hello world')

    def test_operators_and_punctuation(self):
        tokens = tokenize("-> : ; { } [ ] ( ) , <= >= == != < >")
        types = [t.type for t in tokens]
        expected = ['ARROW', 'COLON', 'SEMICOLON', 'LBRACE', 'RBRACE',
                    'LBRACKET', 'RBRACKET', 'LPAREN', 'RPAREN', 'COMMA',
                    'OPERATOR', 'OPERATOR', 'OPERATOR', 'OPERATOR', 'OPERATOR', 'OPERATOR']
        self.assertEqual(types, expected)

    def test_unexpected_character_raises(self):
        with self.assertRaises(LogosSyntaxError):
            tokenize("@")

    def test_percentage_unit(self):
        tokens = tokenize("50 %")
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].type, 'NUMBER')
        self.assertEqual(tokens[1].type, 'UNIT')
        self.assertEqual(tokens[1].value, '%')


# ==========================================================================
# 2. PARSER TESTS
# ==========================================================================

MINIMAL_INTENT = """
intent TestIntent {
    steward: "TestSteward";
    require {
        energy 100 J;
    }
    state Start {
        on go -> End;
    }
    state End {
    }
}
"""

GUARDED_INTENT = """
intent GuardedIntent {
    require {
        energy 10 J;
    }
    state Idle {
        on activate [priority > 5] -> Active;
    }
    state Active {
        on deactivate -> Idle;
    }
}
"""

TRANSITION_REQUIRE_INTENT = """
intent TransReqIntent {
    require {
        energy 1000 J;
        mass 500 kg;
    }
    state Waiting {
        on process -> Processing {
            require energy 50 J;
            require mass 10 kg;
        }
    }
    state Processing {
        on complete -> Done;
    }
    state Done {
    }
}
"""

CONSTRAINT_INTENT = """
intent ConstrainedIntent {
    require {
        energy 100 J;
    }
    constraint {
        energy max 5000 J;
        mass min 10 kg;
    }
    state A {
        on go -> B;
    }
    state B {
    }
}
"""


class TestParser(unittest.TestCase):

    def _parse(self, code: str):
        tokens = tokenize(code)
        return Parser(tokens).parse()

    def test_empty_program(self):
        prog = self._parse("")
        self.assertEqual(len(prog.imports), 0)
        self.assertEqual(len(prog.intents), 0)

    def test_minimal_intent(self):
        prog = self._parse(MINIMAL_INTENT)
        self.assertEqual(len(prog.intents), 1)
        intent = prog.intents[0]
        self.assertEqual(intent.name, "TestIntent")
        self.assertEqual(intent.steward, "TestSteward")
        self.assertIsNotNone(intent.require_block)
        self.assertEqual(len(intent.require_block.requirements), 1)
        self.assertEqual(intent.require_block.requirements[0].resource, "energy")
        self.assertEqual(intent.require_block.requirements[0].value, 100.0)
        self.assertEqual(intent.require_block.requirements[0].unit, "J")
        self.assertEqual(len(intent.states), 2)

    def test_guarded_transition(self):
        prog = self._parse(GUARDED_INTENT)
        trans = prog.intents[0].states[0].transitions[0]
        self.assertEqual(trans.event, "activate")
        self.assertEqual(trans.target, "Active")
        self.assertIsNotNone(trans.guard)

    def test_transition_level_requires(self):
        prog = self._parse(TRANSITION_REQUIRE_INTENT)
        trans = prog.intents[0].states[0].transitions[0]
        self.assertEqual(len(trans.transition_requires), 2)
        self.assertEqual(trans.transition_requires[0].resource, "energy")
        self.assertEqual(trans.transition_requires[1].resource, "mass")

    def test_constraint_block(self):
        prog = self._parse(CONSTRAINT_INTENT)
        intent = prog.intents[0]
        self.assertIsNotNone(intent.constraint_block)
        self.assertEqual(len(intent.constraint_block.constraints), 2)
        self.assertEqual(intent.constraint_block.constraints[0].resource, "energy")
        self.assertEqual(intent.constraint_block.constraints[0].operator, "max")
        self.assertEqual(intent.constraint_block.constraints[1].resource, "mass")
        self.assertEqual(intent.constraint_block.constraints[1].operator, "min")

    def test_import_directive(self):
        prog = self._parse('import "other.logos";')
        self.assertEqual(len(prog.imports), 1)
        self.assertEqual(prog.imports[0].path, "other.logos")

    def test_multiple_intents(self):
        code = """
        intent A { state S1 { on go -> S2; } state S2 {} }
        intent B { state X1 { on start -> X2; } state X2 {} }
        """
        prog = self._parse(code)
        self.assertEqual(len(prog.intents), 2)
        self.assertEqual(prog.intents[0].name, "A")
        self.assertEqual(prog.intents[1].name, "B")

    def test_syntax_error_unclosed_brace(self):
        with self.assertRaises(LogosSyntaxError):
            self._parse("intent Bad {")

    def test_syntax_error_unexpected_token(self):
        with self.assertRaises(LogosSyntaxError):
            self._parse("foobar;")

    def test_header_types(self):
        code = """
        intent H {
            steward: "Alice";
            scope: regional;
            lifetime: 30 days;
            state S {}
        }
        """
        prog = self._parse(code)
        intent = prog.intents[0]
        self.assertEqual(intent.steward, "Alice")
        self.assertEqual(intent.headers["scope"], "regional")
        self.assertIsInstance(intent.headers["lifetime"], dict)
        self.assertEqual(intent.headers["lifetime"]["value"], 30)
        self.assertEqual(intent.headers["lifetime"]["unit"], "days")

    def test_guard_complex_expression(self):
        code = """
        intent G {
            state S {
                on go [x > 1 and y < 10 or not z == 0] -> T;
            }
            state T {}
        }
        """
        prog = self._parse(code)
        trans = prog.intents[0].states[0].transitions[0]
        self.assertIsNotNone(trans.guard)


# ==========================================================================
# 3. COMPILER TESTS
# ==========================================================================

class TestCompiler(unittest.TestCase):

    PERMISSIVE_MESH = {"mass": 1e12, "energy": 1e12, "entropy": 1e12, "cycle": 1e12}

    def _compile(self, code: str, mesh: dict | None = None):
        tokens = tokenize(code)
        prog = Parser(tokens).parse()
        compiler = Compiler(mesh or self.PERMISSIVE_MESH)
        return compiler.compile(prog)

    def test_si_normalisation_mass(self):
        val, unit = normalise_resource("mass", 500, "g", 1)
        self.assertAlmostEqual(val, 0.5)
        self.assertEqual(unit, "kg")

    def test_si_normalisation_energy(self):
        val, unit = normalise_resource("energy", 1, "kWh", 1)
        self.assertAlmostEqual(val, 3_600_000.0)
        self.assertEqual(unit, "J")

    def test_si_normalisation_unknown_unit(self):
        with self.assertRaises(LogosSyntaxError):
            normalise_resource("mass", 1, "furlongs", 1)

    def test_compile_minimal(self):
        smir = self._compile(MINIMAL_INTENT)
        self.assertEqual(smir["logos_version"], "2.0-declarative")
        self.assertEqual(len(smir["intents"]), 1)
        intent = smir["intents"][0]
        self.assertEqual(intent["name"], "TestIntent")
        self.assertEqual(len(intent["requirements"]), 1)
        self.assertEqual(len(intent["states"]), 2)

    def test_compile_guard_present(self):
        smir = self._compile(GUARDED_INTENT)
        trans = smir["intents"][0]["states"][0]["transitions"][0]
        self.assertIn("guard", trans)

    def test_compile_transition_requires(self):
        smir = self._compile(TRANSITION_REQUIRE_INTENT)
        trans = smir["intents"][0]["states"][0]["transitions"][0]
        self.assertIn("requires", trans)
        self.assertEqual(len(trans["requires"]), 2)

    def test_compile_constraints(self):
        smir = self._compile(CONSTRAINT_INTENT)
        intent = smir["intents"][0]
        self.assertEqual(len(intent["constraints"]), 2)

    def test_thermodynamic_failure(self):
        tiny_mesh = {"mass": 0, "energy": 0, "entropy": 0, "cycle": 0}
        with self.assertRaises(ThermodynamicConstraintError):
            self._compile(MINIMAL_INTENT, tiny_mesh)

    def test_import_resolution_dag(self):
        """Test that resolve_imports works and detects cycles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file A importing B, B importing A -> cycle
            a_path = os.path.join(tmpdir, "a.logos")
            b_path = os.path.join(tmpdir, "b.logos")

            with open(a_path, "w") as f:
                f.write('import "b.logos";\nintent A { state S {} }')
            with open(b_path, "w") as f:
                f.write('import "a.logos";\nintent B { state S {} }')

            tokens = tokenize(open(a_path).read())
            prog = Parser(tokens).parse()

            with self.assertRaises(LogosSyntaxError) as ctx:
                resolve_imports(prog, a_path)
            self.assertIn("Cyclic import", str(ctx.exception))

    def test_import_resolution_valid(self):
        """Test that valid non-cyclic imports are merged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib_path = os.path.join(tmpdir, "lib.logos")
            main_path = os.path.join(tmpdir, "main.logos")

            with open(lib_path, "w") as f:
                f.write("intent LibIntent { state Lib {} }")
            with open(main_path, "w") as f:
                f.write('import "lib.logos";\nintent MainIntent { state Main {} }')

            tokens = tokenize(open(main_path).read())
            prog = Parser(tokens).parse()
            resolved = resolve_imports(prog, main_path)

            names = [i.name for i in resolved.intents]
            self.assertIn("LibIntent", names)
            self.assertIn("MainIntent", names)
            # Import-first ordering
            self.assertEqual(names.index("LibIntent"), 0)


# ==========================================================================
# 4. VM TESTS
# ==========================================================================

class TestVM(unittest.TestCase):

    def _compile_and_run(self, code: str, mesh: dict | None = None, ctx: dict | None = None):
        base_mesh = {"mass": 1e6, "energy": 1e6, "entropy": 1e6, "cycle": 1e6}
        if mesh:
            base_mesh.update(mesh)
        smir = compile_logos(code, base_mesh)
        vm = LogosVM(smir, base_mesh, ctx)
        return vm

    def test_basic_transition(self):
        vm = self._compile_and_run(MINIMAL_INTENT)
        self.assertEqual(vm.current_state("TestIntent"), "Start")
        result = vm.send_event("TestIntent", "go")
        self.assertEqual(result["status"], "transitioned")
        self.assertEqual(result["to"], "End")

    def test_no_match_event(self):
        vm = self._compile_and_run(MINIMAL_INTENT)
        result = vm.send_event("TestIntent", "nonexistent")
        self.assertEqual(result["status"], "no_match")

    def test_guard_pass(self):
        vm = self._compile_and_run(GUARDED_INTENT, ctx={"priority": 10})
        result = vm.send_event("GuardedIntent", "activate")
        self.assertEqual(result["status"], "transitioned")

    def test_guard_fail(self):
        vm = self._compile_and_run(GUARDED_INTENT, ctx={"priority": 1})
        result = vm.send_event("GuardedIntent", "activate")
        self.assertEqual(result["status"], "no_match")  # guard failed, no match

    def test_atomic_deduction_success(self):
        vm = self._compile_and_run(TRANSITION_REQUIRE_INTENT)
        before_energy = vm.mesh["energy"]
        before_mass = vm.mesh["mass"]

        result = vm.send_event("TransReqIntent", "process")
        self.assertEqual(result["status"], "transitioned")

        # Energy should be deducted by 50 J
        self.assertAlmostEqual(vm.mesh["energy"], before_energy - 50.0)
        # Mass should be deducted by 10 kg
        self.assertAlmostEqual(vm.mesh["mass"], before_mass - 10.0)

    def test_atomic_deduction_failure_no_partial(self):
        """When one resource is insufficient, NO resources should be deducted."""
        code = """
        intent AtomicTest {
            require {
                energy 100 J;
                mass 100 kg;
            }
            state S1 {
                on go -> S2 {
                    require energy 50 J;
                    require mass 200 kg;
                }
            }
            state S2 {}
        }
        """
        # Compile with permissive mesh (transition feasibility check at compile time)
        compile_mesh = {"mass": 1e6, "energy": 1e6, "entropy": 1e6, "cycle": 1e6}
        smir = compile_logos(code, compile_mesh)
        # Run VM with constrained mesh — mass is tight
        run_mesh = {"mass": 100, "energy": 1e6, "entropy": 1e6, "cycle": 1e6}
        vm = LogosVM(smir, run_mesh)

        before_energy = vm.mesh["energy"]
        before_mass = vm.mesh["mass"]

        result = vm.send_event("AtomicTest", "go")
        self.assertEqual(result["status"], "blocked")

        # CRITICAL: no partial deduction — both resources unchanged
        self.assertAlmostEqual(vm.mesh["energy"], before_energy)
        self.assertAlmostEqual(vm.mesh["mass"], before_mass)

    def test_constraint_enforcement_blocks_transition(self):
        """Constraint violation should roll back deductions and block."""
        code = """
        intent ConstrainedTest {
            require {
                energy 100 J;
            }
            constraint {
                energy min 90 J;
            }
            state S1 {
                on go -> S2 {
                    require energy 20 J;
                }
            }
            state S2 {}
        }
        """
        # mesh starts at 100 J. Deducting 20 J -> 80 J, which violates min 90 J
        mesh = {"mass": 1e6, "energy": 100, "entropy": 1e6, "cycle": 1e6}
        vm = self._compile_and_run(code, mesh)

        result = vm.send_event("ConstrainedTest", "go")
        self.assertEqual(result["status"], "blocked")
        # Energy should be rolled back to 100
        self.assertAlmostEqual(vm.mesh["energy"], 100.0)

    def test_event_log(self):
        vm = self._compile_and_run(MINIMAL_INTENT)
        vm.send_event("TestIntent", "go")
        vm.send_event("TestIntent", "nonexistent")
        self.assertEqual(len(vm.event_log), 2)

    def test_unknown_intent_raises(self):
        vm = self._compile_and_run(MINIMAL_INTENT)
        with self.assertRaises(LogosRuntimeError):
            vm.send_event("FakeIntent", "go")

    def test_multiple_transitions_same_state(self):
        code = """
        intent MultiTrans {
            require { energy 10 J; }
            state S {
                on a -> A;
                on b -> B;
            }
            state A {}
            state B {}
        }
        """
        vm = self._compile_and_run(code)
        result = vm.send_event("MultiTrans", "b")
        self.assertEqual(result["status"], "transitioned")
        self.assertEqual(result["to"], "B")


# ==========================================================================
# 5. INTEGRATION TESTS
# ==========================================================================

class TestIntegration(unittest.TestCase):

    def test_compile_logos_public_api(self):
        mesh = {"mass": 1e6, "energy": 1e6, "entropy": 1e6, "cycle": 1e6}
        smir = compile_logos(MINIMAL_INTENT, mesh)
        self.assertIn("logos_version", smir)
        self.assertIn("intents", smir)

    def test_compile_and_execute_full_pipeline(self):
        """Full pipeline: source -> compile -> VM -> event -> transition."""
        code = """
        intent Pipeline {
            steward: "TestSteward";
            require {
                energy 100 J;
                mass 50 kg;
            }
            constraint {
                energy max 1000000 J;
            }
            state Init {
                on start [enabled == 1] -> Running {
                    require energy 10 J;
                }
                on start -> Idle;
            }
            state Running {
                on stop -> Idle;
            }
            state Idle {
            }
        }
        """
        mesh = {"mass": 1e6, "energy": 1e6, "entropy": 1e6, "cycle": 1e6}
        smir = compile_logos(code, mesh)

        # With guard passing
        vm = LogosVM(smir, dict(mesh), {"enabled": 1})
        result = vm.send_event("Pipeline", "start")
        self.assertEqual(result["status"], "transitioned")
        self.assertEqual(result["to"], "Running")

        # With guard failing — should fall through to second transition
        vm2 = LogosVM(smir, dict(mesh), {"enabled": 0})
        result2 = vm2.send_event("Pipeline", "start")
        self.assertEqual(result2["status"], "transitioned")
        self.assertEqual(result2["to"], "Idle")

    def test_water_distribution_example(self):
        """Compile and execute the water_distribution.logos example file."""
        example_path = os.path.join(
            os.path.dirname(__file__), "examples", "water_distribution.logos"
        )
        if not os.path.isfile(example_path):
            self.skipTest("Example file not found")

        with open(example_path, "r") as f:
            code = f.read()

        # Mesh must satisfy: require (energy >= 9MJ, mass >= 5000 kg, entropy >= 100)
        # AND constraints (energy max 36MJ, entropy max 500, mass min 100 kg)
        mesh = {"mass": 10000.0, "energy": 36_000_000.0, "entropy": 500.0, "cycle": 1e9}
        smir = compile_logos(code, mesh, example_path)

        vm = LogosVM(smir, dict(mesh), {"priority": 10})

        # Idle -> Verifying
        r = vm.send_event("WaterDistribution", "request_water")
        self.assertEqual(r["status"], "transitioned")
        self.assertEqual(r["to"], "Verifying")

        # Verifying -> Distributing (guard: priority > 2, context has priority=10)
        r = vm.send_event("WaterDistribution", "approved")
        self.assertEqual(r["status"], "transitioned")
        self.assertEqual(r["to"], "Distributing")

        # Distributing -> Delivered (deducts mass and energy)
        r = vm.send_event("WaterDistribution", "delivery_complete")
        self.assertEqual(r["status"], "transitioned")
        self.assertEqual(r["to"], "Delivered")

        # Delivered -> Idle
        r = vm.send_event("WaterDistribution", "acknowledge")
        self.assertEqual(r["status"], "transitioned")
        self.assertEqual(r["to"], "Idle")


# ==========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
