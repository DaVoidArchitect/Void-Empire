import sys
import os
import json
import argparse
from logos.lexer import tokenize, LogosSyntaxError
from logos.parser import Parser
from logos.compiler import Compiler, resolve_imports, ThermodynamicConstraintError
from logos.exceptions import LogosCompilerError

def compile_logos(code, mesh_context=None, source_path=None):
    if mesh_context is None:
        mesh_context = {'mass': 1e12, 'energy': 1e12, 'entropy': 1e12, 'cycle': 1e12}
    tokens = tokenize(code)
    program = Parser(tokens).parse()
    if source_path:
        program = resolve_imports(program, source_path)
    compiler = Compiler(mesh_context)
    return compiler.compile(program)

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
