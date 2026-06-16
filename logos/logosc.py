#!/usr/bin/env python3
"""
logosc — Logos Compiler CLI

Compiles a .logos source file into a JSON State Machine IR (SMIR) file.

Usage::

    python -m logos.logosc <source.logos> [-o output.json] [-m mesh.json]
"""

import argparse
import json
import sys
import os

# Ensure the package root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logos import compile_logos
from logos.exceptions import LogosCompilerError


def main():
    parser = argparse.ArgumentParser(
        prog="logosc",
        description="Logos Declarative State Machine Compiler",
    )
    parser.add_argument("source", help="Path to the .logos source file")
    parser.add_argument("-b", "--binary", action="store_true", help="Output dense binary VSMB bytecode instead of JSON SMIR")
    parser.add_argument("-o", "--output", default=None, help="Output file (default: <source>.smir.json or <source>.vsmb)")
    parser.add_argument("-m", "--mesh", default=None, help="Path to a JSON mesh context file")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print the SMIR JSON output")

    args = parser.parse_args()

    # Load source
    source_path = os.path.abspath(args.source)
    if not os.path.isfile(source_path):
        print(f"[LOGOS ERROR] Source file not found: {source_path}", file=sys.stderr)
        sys.exit(1)

    with open(source_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Load or synthesise mesh context
    if args.mesh:
        mesh_path = os.path.abspath(args.mesh)
        if not os.path.isfile(mesh_path):
            print(f"[LOGOS ERROR] Mesh context file not found: {mesh_path}", file=sys.stderr)
            sys.exit(1)
        with open(mesh_path, "r", encoding="utf-8") as f:
            mesh_context = json.load(f)
    else:
        # Default permissive mesh for compilation-only verification
        mesh_context = {
            "mass": 1e12,
            "energy": 1e12,
            "entropy": 1e12,
            "cycle": 1e12,
        }

    # Compile
    try:
        smir = compile_logos(code, mesh_context, source_path)
    except LogosCompilerError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)

    # Determine output path
    is_binary = args.binary or (args.output and args.output.endswith(".vsmb"))
    default_ext = ".vsmb" if is_binary else ".smir.json"
    output_path = args.output or source_path.replace(".logos", default_ext)

    if is_binary:
        from logos.vsmb import encode_vsmb
        binary_data = encode_vsmb(smir)
        with open(output_path, "wb") as f:
            f.write(binary_data)
    else:
        indent = 2 if args.pretty else None
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(smir, f, indent=indent)

    print(f"[LOGOS] Compiled successfully: {output_path}")
    intent_count = len(smir.get("intents", []))
    state_count = sum(len(i.get("states", [])) for i in smir.get("intents", []))
    trans_count = sum(
        len(s.get("transitions", []))
        for i in smir.get("intents", [])
        for s in i.get("states", [])
    )
    print(f"[LOGOS] {intent_count} intent(s), {state_count} state(s), {trans_count} transition(s)")


if __name__ == "__main__":
    main()
