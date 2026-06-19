import sys
import os
import json
import argparse
from logos.interpreter import LogosVM, LogosRuntimeError

def main():
    parser = argparse.ArgumentParser(prog='logos_vm', description='Logos State Machine Virtual Machine')
    parser.add_argument('smir', help='Path to the SMIR JSON file or bytecode')
    parser.add_argument('-m', '--mesh', help='Path to a JSON mesh context file')
    parser.add_argument('-c', '--context', help='Path to a JSON runtime context file (initial states)')
    parser.add_argument('-e', '--events', help='Path to a JSON events file to execute')
    parser.add_argument('-o', '--output', help='Output JSON file to write final context and mesh')
    
    args = parser.parse_args()
    
    smir_path = os.path.abspath(args.smir)
    if not os.path.isfile(smir_path):
        print(f"[LOGOS VM ERROR] SMIR file not found: {smir_path}", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(smir_path, 'r', encoding='utf-8') as f:
            smir_content = f.read()
    except Exception as e:
        print(f"[LOGOS VM ERROR] Failed to read SMIR file: {e}", file=sys.stderr)
        sys.exit(1)
        
    if args.mesh:
        mesh_path = os.path.abspath(args.mesh)
        if not os.path.isfile(mesh_path):
            print(f"[LOGOS VM ERROR] Mesh file not found: {mesh_path}", file=sys.stderr)
            sys.exit(1)
        try:
            with open(mesh_path, 'r') as f:
                mesh = json.load(f)
        except Exception as e:
            print(f"[LOGOS VM ERROR] Failed to parse mesh file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        mesh = {'mass': 1e12, 'energy': 1e12, 'entropy': 1e12, 'cycle': 1e12}
        
    if args.context:
        context_path = os.path.abspath(args.context)
        if not os.path.isfile(context_path):
            print(f"[LOGOS VM ERROR] Context file not found: {context_path}", file=sys.stderr)
            sys.exit(1)
        try:
            with open(context_path, 'r') as f:
                runtime_ctx = json.load(f)
        except Exception as e:
            print(f"[LOGOS VM ERROR] Failed to parse context file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        runtime_ctx = {}
        
    try:
        vm = LogosVM(smir_content, mesh, runtime_ctx)
    except Exception as e:
        print(f"[LOGOS VM ERROR] Initialization failed: {e}", file=sys.stderr)
        sys.exit(2)
        
    results = []
    if args.events:
        events_path = os.path.abspath(args.events)
        if not os.path.isfile(events_path):
            print(f"[LOGOS VM ERROR] Events file not found: {events_path}", file=sys.stderr)
            sys.exit(1)
        try:
            with open(events_path, 'r') as f:
                events = json.load(f)
        except Exception as e:
            print(f"[LOGOS VM ERROR] Failed to parse events file: {e}", file=sys.stderr)
            sys.exit(1)
            
        if not isinstance(events, list):
            print("[LOGOS VM ERROR] Events file must contain a JSON list of event objects", file=sys.stderr)
            sys.exit(1)
            
        for i, ev_obj in enumerate(events):
            intent = ev_obj.get('intent')
            event = ev_obj.get('event')
            if not intent or not event:
                print(f"[LOGOS VM ERROR] Event at index {i} must specify 'intent' and 'event'", file=sys.stderr)
                sys.exit(1)
            try:
                res = vm.send_event(intent, event)
                results.append(res)
            except LogosRuntimeError as e:
                print(f"[LOGOS VM ERROR] Runtime error executing event '{event}' on intent '{intent}': {e}", file=sys.stderr)
                sys.exit(3)
            except Exception as e:
                print(f"[LOGOS VM ERROR] Unexpected error: {e}", file=sys.stderr)
                sys.exit(3)
                
    output_data = {
        'current_states': vm.current_states,
        'mesh': vm.mesh,
        'results': results
    }
    
    if args.output:
        try:
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
        except Exception as e:
            print(f"[LOGOS VM ERROR] Failed to write output file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("[LOGOS VM] Execution complete.")
        print("[LOGOS VM] Final mesh:")
        for k, v in vm.mesh.items():
            print(f"  {k}: {v:.4f}")

if __name__ == '__main__':
    main()
