import os
import sys
import json
import shutil

# Dynamic path linkage for namespace package loading
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)

import logos
logos_path = os.path.join(WORKSPACE, "scratch", "void_archive_temp")
if os.path.exists(logos_path):
    logos.__path__.append(logos_path)

from logos.logosc import compile_logos
from logos.interpreter import LogosVM
from logos.exceptions import ThermodynamicConstraintError

def run_test(name, func):
    print(f"Running test: {name}...")
    try:
        func()
        print(f"  --> PASS")
        return True
    except Exception as e:
        print(f"  --> FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("================================================================================")
    print("                    LOGOS TOOLCHAIN USER VALIDATION SUITE")
    print("================================================================================")
    
    results = {}
    
    # 1. Pipeline check on simple_intent
    def test_simple_pipeline():
        with open("logos/examples/simple_intent.logos", "r") as f:
            code = f.read()
        smir = compile_logos(code)
        assert smir.get("logos_version") == "2.0-declarative", "Version mismatch"
        assert len(smir.get("intents", [])) == 1, "Expected 1 intent"
        intent = smir["intents"][0]
        assert intent["name"] == "SimpleIntent", "Name mismatch"
        
        # Run VM
        mesh = {'mass': 1e6, 'energy': 1e6, 'entropy': 1e6, 'cycle': 1e6}
        vm = LogosVM(smir, mesh)
        assert vm.current_state("SimpleIntent") == "Start", "Initial state mismatch"
        
        res = vm.send_event("SimpleIntent", "self_loop")
        assert res["status"] == "transitioned", f"Expected transitioned status, got {res}"
        assert vm.current_state("SimpleIntent") == "Start", "State should be Start"
        
    results["Simple Pipeline & State Loop"] = run_test("Simple Pipeline & State Loop", test_simple_pipeline)

    # 2. Guard Pass/Fail scenarios on complex_guard
    def test_guard_scenarios():
        with open("logos/examples/complex_guard.logos", "r") as f:
            code = f.read()
        smir = compile_logos(code)
        
        # Test Guard Pass
        mesh = {'mass': 1e6, 'energy': 1e6, 'entropy': 1e6, 'cycle': 1e6}
        vm_pass = LogosVM(smir, mesh, runtime_ctx={"val": 15, "status": 1, "active": 0})
        res_pass = vm_pass.send_event("ComplexGuardIntent", "check_data")
        assert res_pass["status"] == "transitioned", f"Expected transitioned, got {res_pass}"
        assert vm_pass.current_state("ComplexGuardIntent") == "High", f"Expected High state, got {vm_pass.current_state('ComplexGuardIntent')}"
        
        # Test Guard Fail
        vm_fail = LogosVM(smir, mesh, runtime_ctx={"val": 15, "status": 2, "active": 0})
        res_fail = vm_fail.send_event("ComplexGuardIntent", "check_data")
        assert res_fail["status"] == "no_match", f"Expected no_match, got {res_fail}"
        assert vm_fail.current_state("ComplexGuardIntent") == "Start", f"Expected Start state, got {vm_fail.current_state('ComplexGuardIntent')}"

    results["Guard Pass/Fail Scenarios"] = run_test("Guard Pass/Fail Scenarios", test_guard_scenarios)

    # 3. Transition-level resource deduction & 6.18% platform fee
    def test_resource_deduction():
        with open("logos/examples/transition_resources.logos", "r") as f:
            code = f.read()
        smir = compile_logos(code)
        
        mesh = {'mass': 1e6, 'energy': 1000.0, 'entropy': 1e6, 'cycle': 1e6}
        vm = LogosVM(smir, mesh)
        before_energy = vm.mesh['energy']
        
        res = vm.send_event("TransitionResourcesIntent", "activate")
        assert res["status"] == "transitioned", f"Expected transitioned, got {res}"
        
        # Platform fee applies 6.18%: 20 J * 1.0618 = 21.236 J deduction
        expected_deduction = 20.0 * 1.0618
        after_energy = vm.mesh['energy']
        actual_deduction = before_energy - after_energy
        
        assert abs(actual_deduction - expected_deduction) < 1e-3, f"Expected {expected_deduction} deduction, got {actual_deduction}"

    results["Resource Deduction & Platform Fee"] = run_test("Resource Deduction & Platform Fee", test_resource_deduction)

    # 4. Import Behaviors
    def test_imports():
        # Compile import_behavior.logos using CLI/public API
        with open("logos/examples/import_behavior.logos", "r") as f:
            code = f.read()
        smir = compile_logos(code, source_path="logos/examples/import_behavior.logos")
        
        intents = [i["name"] for i in smir.get("intents", [])]
        assert "LibIntent" in intents, "LibIntent missing from compiled SMIR"
        assert "MainIntent" in intents, "MainIntent missing from compiled SMIR"
        assert intents.index("LibIntent") < intents.index("MainIntent"), "LibIntent should precede MainIntent"

    results["Import Behaviors"] = run_test("Import Behaviors", test_imports)

    # 5. Constraint Enforcement
    def test_constraint_enforcement():
        # Code with constraint
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
        smir = compile_logos(code)
        # Mesh energy starting exactly at 100
        mesh = {'mass': 1e6, 'energy': 100.0, 'entropy': 1e6, 'cycle': 1e6}
        vm = LogosVM(smir, mesh)
        
        res = vm.send_event("ConstrainedTest", "go")
        # Should be blocked because 100 - (20 * 1.0618) = 78.764 J which is < 90 J
        assert res["status"] == "blocked", f"Expected blocked, got {res}"
        # Deductions must be rolled back on block
        assert vm.mesh['energy'] == 100.0, f"Deduction did not roll back, current energy: {vm.mesh['energy']}"

    results["Constraint Enforcement"] = run_test("Constraint Enforcement", test_constraint_enforcement)

    # 6. Polymorphic Agent Modulations
    def test_polymorphic_agent():
        with open("voidos/agent.logos", "r", encoding="utf-8") as f:
            code = f.read()
        smir = compile_logos(code)
        
        # Verify the structure of compiled SMIR
        assert smir.get("logos_version") == "2.0-declarative", "Version mismatch"
        assert len(smir.get("intents", [])) == 1, "Expected 1 intent"
        intent = smir["intents"][0]
        assert intent["name"] == "UniversalAgent", "Name mismatch"
        
        # Verify states are present
        states = [s["name"] for s in intent.get("states", [])]
        expected_states = ["Initialize", "ConversationalMode", "MediaGenerationMode", "SimulationEngineMode"]
        for s in expected_states:
            assert s in states, f"State {s} not found in compiled agent core"
            
        # Verify VLEN=2048 and lanes are present in layout
        native_layout = intent.get("native_layout", {})
        assert native_layout.get("vlen_bits") == 2048, "VLEN bits mismatch"
        assert native_layout.get("lanes") == 512, "Lanes count mismatch"
        
        # Verify register mappings
        registers = native_layout.get("registers", {})
        assert registers.get("v4") == "vector_execution_mask", "v4 mapping mismatch"
        assert registers.get("v5") == "vector_operand_a_2048b", "v5 mapping mismatch"
        
        # Setup VM with compliant energy and mass parameters (within UniversalAgent constraints)
        mesh = {'mass': 1.0, 'energy': 4000.0 * 3600.0, 'entropy': 1e12, 'cycle': 1e12}
        vm = LogosVM(smir, mesh)
        
        # Initial State Check
        assert vm.current_state("UniversalAgent") == "Initialize", "Initial state must be Initialize"
        
        # Step 1: Ingest stream -> ConversationalMode
        res = vm.send_event("UniversalAgent", "ingest_intent_stream")
        assert res["status"] == "transitioned", f"Transition ingest_intent_stream failed: {res}"
        assert vm.current_state("UniversalAgent") == "ConversationalMode"
        
        # Step 2: Process conversation token (self-loop)
        # Note: requires energy 5.0 Wh, which is 18000 J
        # Deducts 18000 * 1.0618 = 19112.4 J from mesh
        energy_before = vm.mesh['energy']
        res = vm.send_event("UniversalAgent", "process_conversation_token")
        assert res["status"] == "transitioned"
        assert vm.current_state("UniversalAgent") == "ConversationalMode"
        energy_after = vm.mesh['energy']
        assert abs((energy_before - energy_after) - 19112.4) < 1e-3, f"Energy deduction mismatch: {energy_before - energy_after}"
        
        # Step 3: Shift execution profile directly to extreme systems engineering simulations
        res = vm.send_event("UniversalAgent", "shift_to_simulation")
        assert res["status"] == "transitioned"
        assert vm.current_state("UniversalAgent") == "SimulationEngineMode"
        
        # Step 4: Run physics calculations
        res = vm.send_event("UniversalAgent", "solve_physics_lattice")
        assert res["status"] == "transitioned"
        assert vm.current_state("UniversalAgent") == "SimulationEngineMode"
        
        # Step 5: Shift back to conversation
        res = vm.send_event("UniversalAgent", "shift_to_conversation")
        assert res["status"] == "transitioned"
        assert vm.current_state("UniversalAgent") == "ConversationalMode"
        
        # Step 6: Shift to media generation
        res = vm.send_event("UniversalAgent", "shift_to_media")
        assert res["status"] == "transitioned"
        assert vm.current_state("UniversalAgent") == "MediaGenerationMode"
        
        # Step 7: Render media frame (self-loop)
        res = vm.send_event("UniversalAgent", "render_canvas_frame")
        assert res["status"] == "transitioned"
        assert vm.current_state("UniversalAgent") == "MediaGenerationMode"
        
        # Step 8: Shift back to conversation
        res = vm.send_event("UniversalAgent", "shift_to_conversation")
        assert res["status"] == "transitioned"
        assert vm.current_state("UniversalAgent") == "ConversationalMode"

    results["Polymorphic Agent Modulations"] = run_test("Polymorphic Agent Modulations", test_polymorphic_agent)

    print("================================================================================")
    print("                                TEST SUMMARY")
    print("================================================================================")
    all_passed = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{name:<45} : {status}")
        if not passed:
            all_passed = False
            
    print("================================================================================")
    if all_passed:
        print("FINAL RESULT: PASS")
        sys.exit(0)
    else:
        print("FINAL RESULT: FAIL")
        sys.exit(1)

if __name__ == "__main__":
    main()
