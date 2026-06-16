#!/usr/bin/env python3
import os
import sys
import json
import argparse
import subprocess

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logos.compiler import Compiler, resolve_imports
from logos.parser import Parser
from logos.lexer import tokenize

def main():
    parser = argparse.ArgumentParser(description="Logos AOT Compiler")
    parser.add_argument("source", help="Path to input .logos file")
    parser.add_argument("-m", "--mesh", required=True, help="Path to mesh context JSON")
    parser.add_argument("-o", "--output", help="Path to output binary executable")
    parser.add_argument("-c", "--c-only", action="store_true", help="Only output C source file")
    
    args = parser.parse_args()
    
    # 1. Read source
    if not os.path.isfile(args.source):
        print(f"Error: Source file '{args.source}' not found.", file=sys.stderr)
        sys.exit(1)
        
    with open(args.source, "r", encoding="utf-8") as f:
        code = f.read()
        
    # 2. Read mesh
    if not os.path.isfile(args.mesh):
        print(f"Error: Mesh file '{args.mesh}' not found.", file=sys.stderr)
        sys.exit(1)
        
    with open(args.mesh, "r", encoding="utf-8") as f:
        try:
            mesh_context = json.load(f)
        except Exception as e:
            print(f"Error parsing mesh JSON: {e}", file=sys.stderr)
            sys.exit(1)
        
    # 3. Compile
    try:
        tokens = tokenize(code)
        prog = Parser(tokens).parse()
        prog = resolve_imports(prog, args.source)
        compiler = Compiler(mesh_context)
        c_code = compiler.compile_to_c(prog)
    except Exception as e:
        print(f"Compilation Error: {e}", file=sys.stderr)
        sys.exit(1)
        
    # Determine paths
    source_base = os.path.splitext(args.source)[0]
    
    if args.output:
        if args.output.endswith(".exe"):
            exe_file = args.output
            c_file = args.output[:-4] + ".c"
        elif args.output.endswith(".c"):
            c_file = args.output
            exe_file = args.output[:-2] + ".exe"
        else:
            exe_file = args.output
            c_file = args.output + ".c"
    else:
        c_file = source_base + ".c"
        exe_file = source_base + ".exe"
        
    # Write C source
    with open(c_file, "w", encoding="utf-8") as f:
        f.write(c_code)
    print(f"Generated C source: {c_file}")
    
    if args.c_only:
        return
        
    # Invoke GCC to compile
    gcc_path = r"C:\Users\voidi\AppData\Local\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.MCF.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin\gcc.exe"
    cmd = [gcc_path, c_file, "-O2", "-o", exe_file]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Successfully compiled native executable: {exe_file}")
    except subprocess.CalledProcessError as e:
        print("GCC compilation failed:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
