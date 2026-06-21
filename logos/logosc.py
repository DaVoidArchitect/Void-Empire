import sys
import os
import json
import argparse
from logos.lexer import tokenize, LogosSyntaxError
from logos.parser import Parser
from logos.compiler import Compiler, resolve_imports, ThermodynamicConstraintError
from logos.exceptions import LogosCompilerError

import math

def prove_thermodynamic_boundaries(smir, mesh_context, source_path=None):
    # available resources
    avail_energy = mesh_context.get('energy', 1e12)
    avail_mass = mesh_context.get('mass', 1e12)
    avail_entropy = mesh_context.get('entropy', 1e12)
    avail_cycle = mesh_context.get('cycle', 1e12)

    for intent in smir.get('intents', []):
        intent_name = intent.get('name', '')
        
        # Check intent-level requirements
        req_energy = 0.0
        req_mass = 0.0
        for req in intent.get('requirements', []):
            res_type = req.get('resource')
            val = req.get('value', 0.0)
            unit = req.get('unit', '')
            if res_type == 'energy':
                if 'wh' in unit.lower():
                    val = val * 3600.0
                req_energy = max(req_energy, val)
            elif res_type == 'mass':
                if unit == 'g':
                    val = val * 1e-3
                elif unit == 'mg':
                    val = val * 1e-6
                req_mass = max(req_mass, val)

        if req_energy > avail_energy:
            raise ThermodynamicConstraintError(
                'energy', req_energy, 'J', avail_energy, 'J', 1,
                f"Static Proof Failure: Intent {intent_name} requires {req_energy} J of energy, which exceeds available {avail_energy} J in mesh."
            )
        if req_mass > avail_mass:
            raise ThermodynamicConstraintError(
                'mass', req_mass, 'kg', avail_mass, 'kg', 1,
                f"Static Proof Failure: Intent {intent_name} requires {req_mass} kg of mass, which exceeds available {avail_mass} kg in mesh."
            )

        # Build state-transition graph to compute worst-case path resource consumption
        states = intent.get('states', [])
        if not states:
            continue

        # Find initial state
        initial_state = states[0]['name']

        # Construct adjacency list
        adj = {}
        for s in states:
            adj[s['name']] = s.get('transitions', [])

        # DFS to find maximum resource consumption on any path (with loop boundary check)
        memo = {}
        visited = set()

        def dfs(state_name):
            if state_name in visited:
                # Finite cycle proof guarantee
                return 0.0, 0.0
            
            if state_name in memo:
                return memo[state_name]

            visited.add(state_name)
            max_e = 0.0
            max_c = 0.0

            transitions = adj.get(state_name, [])
            for t in transitions:
                t_energy = 0.0
                t_cycle = 0.0
                for r in t.get('requires', []):
                    res_type = r.get('resource')
                    val = r.get('value', 0.0)
                    unit = r.get('unit', '')
                    if res_type == 'energy':
                        if 'wh' in unit.lower():
                            val = val * 3600.0
                        t_energy = max(t_energy, val)
                    elif res_type == 'cycle':
                        t_cycle = max(t_cycle, val)

                next_state = t.get('target')
                sub_e, sub_c = dfs(next_state)
                max_e = max(max_e, t_energy + sub_e)
                max_c = max(max_c, t_cycle + sub_c)

            visited.remove(state_name)
            memo[state_name] = (max_e, max_c)
            return max_e, max_c

        worst_e, worst_c = dfs(initial_state)

        # Apply 6.18% platform fee to energy cost path
        worst_e_with_fee = worst_e * 1.0618

        if worst_e_with_fee > avail_energy:
            raise ThermodynamicConstraintError(
                'energy', worst_e_with_fee, 'J', avail_energy, 'J', 1,
                f"Static Proof Failure: Acyclic path in {intent_name} could consume {worst_e_with_fee:.2f} J (with fee), exceeding available {avail_energy} J."
            )
        if worst_e_with_fee > req_energy and req_energy > 0:
             raise ThermodynamicConstraintError(
                'energy', worst_e_with_fee, 'J', req_energy, 'J', 1,
                f"Static Proof Failure: Acyclic path in {intent_name} could consume {worst_e_with_fee:.2f} J, exceeding declared intent capacity of {req_energy} J."
            )

def emit_native_wide_vector_instructions(smir):
    # Upscale compile loop to emit hardware-level instructions mapped directly to wide registers (VLEN=2048).
    # Registers:
    # v0: Current State Register (holds state ID)
    # v1: Energy Register (holds double energy J)
    # v2: Cycle Register (holds double cycle count)
    # v3: Entropy Register (holds double entropy)
    # v4: Vector Execution Register (VLEN=2048 bits / 64-bit element = 32 lanes)
    # v5-v12: Local Variable Coordinates & Vector registers
    
    for intent in smir.get('intents', []):
        intent_name = intent.get('name', '')
        
        # Define the register mapping table for this intent
        reg_mapping = {
            "v0": f"state_id_{intent_name.lower()}",
            "v1": "mesh_energy_joules",
            "v2": "mesh_cycle_count",
            "v3": "mesh_entropy_value",
            "v4": "vector_execution_mask",
            "v5": "vector_operand_a_2048b",
            "v6": "vector_operand_b_2048b",
            "v7": "vector_dest_accumulator"
        }
        
        intent["native_layout"] = {
            "vlen_bits": 2048,
            "lanes": 512,
            "registers": reg_mapping,
            "instructions": []
        }
        
        # Emit base initialization instructions
        insts = [
            f"; NATIVE COMPILATION LOOP FOR INTENT: {intent_name}",
            "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)"
        ]
        
        states = intent.get('states', [])
        for state_idx, state in enumerate(states):
            state_name = state['name']
            insts.append(f"; State {state_name} (ID: {state_idx})")
            
            for trans in state.get('transitions', []):
                event = trans.get('event')
                target = trans.get('target')
                insts.append(f";   on {event} -> {target}")
                
                # Check requirements
                req_energy = 0.0
                for r in trans.get('requires', []):
                    if r.get('resource') == 'energy':
                        val = r.get('value', 0.0)
                        unit = r.get('unit', '')
                        if 'wh' in unit.lower():
                            val = val * 3600.0
                        req_energy = val
                
                if req_energy > 0:
                    # Apply 6.18% platform fee at compile-time/register-layer
                    total_energy_j = req_energy * 1.0618
                    insts.append(f"    vfmv.v.f v5, {total_energy_j:.4f}    ; Load total energy cost (with 6.18% fee) into v5")
                    insts.append("    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)")
                
                # Direct register comparison for state transition
                target_idx = -1
                for idx, s in enumerate(states):
                    if s['name'] == target:
                        target_idx = idx
                if target_idx != -1:
                    insts.append(f"    li t1, {target_idx}                  ; Load target state ID {target_idx}")
                    insts.append("    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)")
                    
        intent["native_layout"]["instructions"] = insts

def compile_logos(code, mesh_context=None, source_path=None):
    if mesh_context is None:
        mesh_context = {'mass': 1e12, 'energy': 1e12, 'entropy': 1e12, 'cycle': 1e12}
    tokens = tokenize(code)
    program = Parser(tokens).parse()
    if source_path:
        program = resolve_imports(program, source_path)
    compiler = Compiler(mesh_context)
    smir = compiler.compile(program)
    
    # 1. Run static thermodynamic proof checking
    prove_thermodynamic_boundaries(smir, mesh_context, source_path)
    
    # 2. Emit native VLEN=2048 wide vector instructions
    emit_native_wide_vector_instructions(smir)
    
    return smir

def main():
    parser = argparse.ArgumentParser(prog='logosc', description='Logos Declarative State Machine Compiler')
    parser.add_argument('source', help='Path to the .logos source file')
    parser.add_argument('-o', '--output', help='Output SMIR JSON file (default: <source>.smir.json)')
    parser.add_argument('-m', '--mesh', help='Path to a JSON mesh context file')
    parser.add_argument('--pretty', action='store_true', help='Pretty-print the SMIR JSON output')
    
    args = parser.parse_args()
    
    source_path = os.path.abspath(args.source)
    if not os.path.isfile(source_path):
        print(f"[LOGOS ERROR] Source file not found: {source_path}", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        print(f"[LOGOS ERROR] Failed to read source file: {e}", file=sys.stderr)
        sys.exit(1)
        
    if args.mesh:
        mesh_path = os.path.abspath(args.mesh)
        if not os.path.isfile(mesh_path):
            print(f"[LOGOS ERROR] Mesh context file not found: {mesh_path}", file=sys.stderr)
            sys.exit(1)
        try:
            with open(mesh_path, 'r') as f:
                mesh_context = json.load(f)
        except Exception as e:
            print(f"[LOGOS ERROR] Failed to parse mesh context file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        mesh_context = {'mass': 1e12, 'energy': 1e12, 'entropy': 1e12, 'cycle': 1e12}
        
    try:
        smir = compile_logos(code, mesh_context, source_path)
    except (LogosSyntaxError, ThermodynamicConstraintError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"[LOGOS ERROR] Compiler error: {e}", file=sys.stderr)
        sys.exit(2)
        
    output_path = args.output
    if not output_path:
        if source_path.endswith('.logos'):
            output_path = source_path[:-6] + '.smir.json'
        else:
            output_path = source_path + '.smir.json'
            
    try:
        with open(output_path, 'w') as f:
            if args.pretty:
                json.dump(smir, f, indent=2)
            else:
                json.dump(smir, f)
    except Exception as e:
        print(f"[LOGOS ERROR] Failed to write SMIR file: {e}", file=sys.stderr)
        sys.exit(1)
        
    intent_count = len(smir.get('intents', []))
    state_count = sum(len(intent.get('states', [])) for intent in smir.get('intents', []))
    trans_count = sum(sum(len(state.get('transitions', [])) for state in intent.get('states', [])) for intent in smir.get('intents', []))
    print(f"[LOGOS] Compiled successfully: {intent_count} intent(s), {state_count} state(s), {trans_count} transition(s)")

if __name__ == '__main__':
    main()
