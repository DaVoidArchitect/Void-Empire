"""
Logos Adversarial Chaos Validation Suite
========================================
Attempts to break the Logos compiler and VM using malformed syntax, cyclic imports,
resource deficits, operating constraint violations, and weird guard edge cases.
"""

import os
import sys
import tempfile
import json
import traceback

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logos import compile_logos, LogosVM
from logos.exceptions import LogosCompilerError, LogosRuntimeError, LogosSyntaxError, ThermodynamicConstraintError

def print_banner(text):
    print("=" * 80)
    print(f"  {text}")
    print("=" * 80)

def main():
    print_banner("LOGOS ADVERSARIAL CHAOS TESTING")
    
    pass_count = 0
    fail_count = 0

    def assert_test(name, condition):
        nonlocal pass_count, fail_count
        if condition:
            print(f"  [PASS] {name}")
            pass_count += 1
        else:
            print(f"  [FAIL] {name}")
            fail_count += 1

    # ----------------------------------------------------
    # SCENARIO 1: Malformed Syntax
    # ----------------------------------------------------
    print("\n--- Scenario 1: Malformed/Invalid Syntax ---")
    bad_syntax_code = """
    intent Broken {
        steward: "Hydro Council" # Missing semicolon
        state Idle {
            on event -> ; # Missing target state
        }
    }
    """
    try:
        compile_logos(bad_syntax_code, {"mass": 100, "energy": 100, "entropy": 100, "cycle": 100})
        assert_test("Malformed syntax compile failure", False)
    except LogosSyntaxError as e:
        assert_test("Malformed syntax compile failure (raises LogosSyntaxError)", True)
        print(f"    Caught expected exception: {e.message}")
    except Exception as e:
        assert_test("Malformed syntax compile failure (raises LogosSyntaxError)", False)
        print(f"    Unexpected exception: {type(e).__name__}: {e}")

    # ----------------------------------------------------
    # SCENARIO 2: Cyclic Imports
    # ----------------------------------------------------
    print("\n--- Scenario 2: Cyclic Import Detection ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        a_path = os.path.normpath(os.path.join(tmpdir, "a.logos"))
        b_path = os.path.normpath(os.path.join(tmpdir, "b.logos"))
        
        with open(a_path, "w", encoding="utf-8") as f:
            f.write('import "b.logos";\nintent A { state Idle {} }')
        with open(b_path, "w", encoding="utf-8") as f:
            f.write('import "a.logos";\nintent B { state Idle {} }')
            
        try:
            with open(a_path, "r", encoding="utf-8") as f:
                code = f.read()
            compile_logos(code, {"mass": 100, "energy": 100, "entropy": 100, "cycle": 100}, source_path=a_path)
            assert_test("Cyclic import compile failure", False)
        except LogosSyntaxError as e:
            assert_test("Cyclic import compile failure (raises LogosSyntaxError)", True)
            print(f"    Caught expected exception: {e.message}")
        except Exception as e:
            assert_test("Cyclic import compile failure (raises LogosSyntaxError)", False)
            print(f"    Unexpected exception: {type(e).__name__}: {e}")

    # ----------------------------------------------------
    # SCENARIO 3: Thermodynamic Deficit at Compile Time
    # ----------------------------------------------------
    print("\n--- Scenario 3: Thermodynamic Deficit at Compile Time ---")
    demanding_code = """
    intent HeavyIntent {
        steward: "Heavy";
        target: "Target";
        license: "CC0-1.0";
        scope: "global";
        provenance: "heavy";
        lifetime: 1 days;
        require {
            mass 1000.0 kg;
        }
        state S {}
    }
    """
    tiny_mesh = {"mass": 500.0, "energy": 100, "entropy": 100, "cycle": 100}
    try:
        compile_logos(demanding_code, tiny_mesh)
        assert_test("Thermodynamic deficit compile failure", False)
    except ThermodynamicConstraintError as e:
        assert_test("Thermodynamic deficit compile failure (raises ThermodynamicConstraintError)", True)
        print(f"    Caught expected exception (mass deficit): Required {e.required_value} kg, available {e.available_value} kg")
    except Exception as e:
        assert_test("Thermodynamic deficit compile failure", False)
        print(f"    Unexpected exception: {type(e).__name__}: {e}")

    # ----------------------------------------------------
    # SCENARIO 4: Transition Resource Deficit at Runtime
    # ----------------------------------------------------
    print("\n--- Scenario 4: Runtime Transition Resource Deficit ---")
    valid_compile_code = """
    intent TransDeficit {
        steward: "Test";
        target: "Test";
        license: "MIT";
        scope: "local";
        provenance: "test";
        lifetime: 1 days;
        require {
            energy 10.0 J;
        }
        state Init {
            on go -> Done {
                require energy 100.0 J;
            }
        }
        state Done {}
    }
    """
    # Enough energy to compile (100 J total in mesh, requires 10 J for intent definition)
    mesh = {"mass": 1000, "energy": 100.0, "entropy": 1000, "cycle": 1000}
    smir = compile_logos(valid_compile_code, mesh)
    
    # Run VM with energy = 50.0 J (insufficient for transition requirement of 100.0 J)
    vm_mesh = {"mass": 1000, "energy": 50.0, "entropy": 1000, "cycle": 1000}
    vm = LogosVM(smir, vm_mesh)
    
    res = vm.send_event("TransDeficit", "go")
    assert_test("Transition blocked status returned", res["status"] == "blocked")
    assert_test("State remains Init", vm.current_state("TransDeficit") == "Init")
    assert_test("Mesh resources not deducted (atomic rollback)", vm.mesh["energy"] == 50.0)
    print(f"    Transition status: {res['status']} | Detail: {res['detail']}")

    # ----------------------------------------------------
    # SCENARIO 5: Runtime Constraint Violations
    # ----------------------------------------------------
    print("\n--- Scenario 5: Runtime Operating Constraint Violation ---")
    constraint_code = """
    intent ConstraintViolator {
        steward: "Test";
        target: "Test";
        license: "MIT";
        scope: "local";
        provenance: "test";
        lifetime: 1 days;
        require {
            energy 10.0 J;
        }
        constraint {
            energy min 40.0 J;
        }
        state Init {
            on go -> Done {
                require energy 20.0 J;
            }
        }
        state Done {}
    }
    """
    mesh = {"mass": 1000, "energy": 100.0, "entropy": 1000, "cycle": 1000}
    smir = compile_logos(constraint_code, mesh)
    
    # Available energy = 50 J. Transition requires 20 J.
    # Remaining energy would be 30 J, which violates "energy min 40.0 J".
    vm_mesh = {"mass": 1000, "energy": 50.0, "entropy": 1000, "cycle": 1000}
    vm = LogosVM(smir, vm_mesh)
    
    res = vm.send_event("ConstraintViolator", "go")
    assert_test("Constraint violation blocked transition", res["status"] == "blocked")
    assert_test("State remains Init", vm.current_state("ConstraintViolator") == "Init")
    assert_test("Mesh resources not deducted (atomic rollback)", vm.mesh["energy"] == 50.0)
    print(f"    Transition status: {res['status']} | Detail: {res['detail']}")

    # ----------------------------------------------------
    # SCENARIO 6: Guard Resiliency & Edge Cases
    # ----------------------------------------------------
    print("\n--- Scenario 6: Guard Resiliency ---")
    guard_code = """
    intent GuardTest {
        steward: "Test";
        target: "Test";
        license: "MIT";
        scope: "local";
        provenance: "test";
        lifetime: 1 days;
        require {
            energy 1.0 J;
        }
        state Init {
            on go [is_active == 1 and 10 / divisor > 2] -> Doneing;
        }
        state Doneing {}
    }
    """
    mesh = {"mass": 1000, "energy": 10.0, "entropy": 1000, "cycle": 1000}
    smir = compile_logos(guard_code, mesh)
    
    # Sub-case A: Missing variable (is_active, divisor not in context)
    # VM evaluates identifier references not in context as 0.
    # 10 / 0 yields 0 (safe zero-division protection).
    # Guard becomes: 0 == 1 and 0 > 2 -> False.
    vm = LogosVM(smir, dict(mesh))
    res = vm.send_event("GuardTest", "go")
    assert_test("Missing variables guard evaluated to False safely", res["status"] == "no_match")
    assert_test("State remains Init", vm.current_state("GuardTest") == "Init")
    
    # Sub-case B: Divisor is 0 in context
    # Context: is_active = 1, divisor = 0
    # Guard: 1 == 1 and 10 / 0 > 2 -> True and 0 > 2 -> False.
    vm = LogosVM(smir, dict(mesh), {"is_active": 1, "divisor": 0})
    res = vm.send_event("GuardTest", "go")
    assert_test("Division by zero in guard evaluated safely to 0", res["status"] == "no_match")
    assert_test("State remains Init", vm.current_state("GuardTest") == "Init")
    
    # Sub-case C: Division by zero in guard that should pass if divisor > 0
    # Context: is_active = 1, divisor = 2
    # Guard: 1 == 1 and 10 / 2 > 2 -> True and 5 > 2 -> True.
    vm = LogosVM(smir, dict(mesh), {"is_active": 1, "divisor": 2})
    res = vm.send_event("GuardTest", "go")
    assert_test("Transition passes when guard expression is fully satisfied", res["status"] == "transitioned")
    assert_test("State transitioned to Doneing", vm.current_state("GuardTest") == "Doneing")

    print_banner(f"CHAOS VALIDATION COMPLETE: {pass_count} PASSED, {fail_count} FAILED")
    if fail_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
