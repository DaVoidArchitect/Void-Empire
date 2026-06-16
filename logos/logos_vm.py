#!/usr/bin/env python3
"""
logos-vm — Logos State Machine VM CLI

Loads a compiled SMIR JSON file and processes events from a JSON event
stream file or interactive stdin.

Usage::

    python -m logos.logos_vm <smir.json> -e events.json [-m mesh.json] [-c context.json]
    python -m logos.logos_vm <smir.json> --interactive [-m mesh.json]
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logos.interpreter import LogosVM
from logos.exceptions import LogosRuntimeError


def main():
    parser = argparse.ArgumentParser(
        prog="logos-vm",
        description="Logos Declarative State Machine VM",
    )
    parser.add_argument("smir", help="Path to the compiled SMIR JSON file")
    parser.add_argument("-e", "--events", default=None, help="Path to a JSON events file")
    parser.add_argument("-m", "--mesh", default=None, help="Path to a JSON mesh context file")
    parser.add_argument("-c", "--context", default=None, help="Path to a JSON runtime context file (for guards)")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive REPL mode")

    args = parser.parse_args()

    # Load SMIR
    smir_path = os.path.abspath(args.smir)
    if not os.path.isfile(smir_path):
        print(f"[LOGOS VM ERROR] SMIR file not found: {smir_path}", file=sys.stderr)
        sys.exit(1)

    with open(smir_path, "rb") as f:
        magic_or_data = f.read()

    if magic_or_data.startswith(b"VSMB"):
        smir = magic_or_data
    else:
        smir = json.loads(magic_or_data.decode("utf-8"))

    # Load mesh context
    if args.mesh:
        with open(os.path.abspath(args.mesh), "r", encoding="utf-8") as f:
            mesh_context = json.load(f)
    else:
        mesh_context = {
            "mass": 1e12,
            "energy": 1e12,
            "entropy": 1e12,
            "cycle": 1e12,
        }

    # Load runtime context
    runtime_ctx = {}
    if args.context:
        with open(os.path.abspath(args.context), "r", encoding="utf-8") as f:
            runtime_ctx = json.load(f)

    # Initialise VM
    vm = LogosVM(smir, mesh_context, runtime_ctx)

    if args.interactive:
        _run_interactive(vm)
    elif args.events:
        _run_batch(vm, args.events)
    else:
        print("[LOGOS VM] No events file or --interactive flag. Nothing to execute.")
        sys.exit(0)


def _run_batch(vm: LogosVM, events_path: str):
    """Execute a batch of events from a JSON file."""
    abs_path = os.path.abspath(events_path)
    if not os.path.isfile(abs_path):
        print(f"[LOGOS VM ERROR] Events file not found: {abs_path}", file=sys.stderr)
        sys.exit(1)

    with open(abs_path, "r", encoding="utf-8") as f:
        events = json.load(f)

    if not isinstance(events, list):
        print("[LOGOS VM ERROR] Events file must contain a JSON array.", file=sys.stderr)
        sys.exit(1)

    for i, evt in enumerate(events):
        intent = evt.get("intent", "")
        event = evt.get("event", "")
        # Optionally update runtime context per-event
        if "context" in evt:
            vm.runtime_ctx.update(evt["context"])

        try:
            result = vm.send_event(intent, event)
        except LogosRuntimeError as e:
            print(f"[EVENT {i}] ERROR: {e}", file=sys.stderr)
            continue

        status = result["status"]
        icon = "+" if status == "transitioned" else "-" if status == "blocked" else "?"
        print(f"[EVENT {i}] {icon} {result['from']} --({event})--> {result['to']} [{status}]")
        if status != "transitioned":
            print(f"          Detail: {result['detail']}")

    # Summary
    print("\n[LOGOS VM] Execution complete.")
    print(f"[LOGOS VM] Final mesh: {json.dumps(vm.mesh, indent=2)}")


def _run_interactive(vm: LogosVM):
    """Run an interactive REPL for sending events."""
    print("================================================================================")
    print("                      LOGOS VM — INTERACTIVE EXECUTION")
    print("================================================================================")
    print("Commands: <intent> <event>   |   :state <intent>   |   :mesh   |   :quit")
    print("================================================================================")

    while True:
        try:
            line = input("\n[LOGOS VM] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[LOGOS VM] Session terminated.")
            break

        if not line:
            continue

        if line == ":quit" or line == ":exit":
            print("[LOGOS VM] Session terminated.")
            break
        elif line == ":mesh":
            print(json.dumps(vm.mesh, indent=2))
            continue
        elif line.startswith(":state "):
            intent = line.split(" ", 1)[1].strip()
            print(f"[LOGOS VM] {intent} -> {vm.current_state(intent)}")
            continue

        parts = line.split(None, 1)
        if len(parts) != 2:
            print("[LOGOS VM] Usage: <intent> <event>")
            continue

        intent, event = parts

        try:
            result = vm.send_event(intent, event)
        except LogosRuntimeError as e:
            print(f"[LOGOS VM] ERROR: {e}")
            continue

        status = result["status"]
        icon = "+" if status == "transitioned" else "-" if status == "blocked" else "?"
        print(f"  {icon} {result['from']} --({event})--> {result['to']} [{status}]")
        if status != "transitioned":
            print(f"     Detail: {result['detail']}")


if __name__ == "__main__":
    main()
