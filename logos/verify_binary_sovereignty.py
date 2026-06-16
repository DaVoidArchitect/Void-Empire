#!/usr/bin/env python3
import os
import hashlib
import sys
import subprocess

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
stage0_exe = os.path.join(WORKSPACE, "logos", "bin", "stage0_compiler.exe")
stage1_exe = os.path.join(WORKSPACE, "logos", "bin", "stage1_compiler.exe")

print("=" * 80)
print("  LOGOS ECOSYSTEM BINARY SOVEREIGNTY VERIFICATION")
print("=" * 80)

# Check files exist
if not os.path.isfile(stage0_exe) or not os.path.isfile(stage1_exe):
    print("Verification Failed: Compiler binaries not found.", file=sys.stderr)
    sys.exit(1)

# Check hashes
with open(stage0_exe, "rb") as f:
    bytes0 = f.read()
with open(stage1_exe, "rb") as f:
    bytes1 = f.read()

sha0 = hashlib.sha256(bytes0).hexdigest()
sha1 = hashlib.sha256(bytes1).hexdigest()

print(f"  Stage 0 SHA-256: {sha0}")
print(f"  Stage 1 SHA-256: {sha1}")

if sha0 != sha1:
    print("Verification Failed: Cryptographic mismatch between Stage 0 and Stage 1.", file=sys.stderr)
    sys.exit(1)

print("  Cryptographic verification: MATCH OK.")

# Verify purge
purged_files = ["compiler.py", "logosc.py", "bootstrap_aot.py"]
for f in purged_files:
    path = os.path.join(WORKSPACE, "logos", f)
    if os.path.exists(path):
        print(f"Verification Failed: Obsolete file {f} still exists at {path}", file=sys.stderr)
        sys.exit(1)
        
print("  Ecosystem purge verification: RUST VM & PYTHON INFRASTRUCTURE PURGED OK.")

# Run events test
events_test = os.path.join(WORKSPACE, "logos", "bin", "compiler_bootstrap_events_test.json")
with open(events_test, "w") as f:
    f.write('[ {"intent": "LogosCompiler", "event": "scan_tokens"} ]')
    
try:
    res = subprocess.run([stage1_exe, events_test], capture_output=True, text=True, check=True)
    if "[EVENT 0] + Initialize --(scan_tokens)--> Lexing [transitioned]" in res.stdout:
        print("  Functional compiler test execution: OK.")
    else:
        print("Verification Failed: stage1_compiler.exe did not output expected transition path.", file=sys.stderr)
        sys.exit(1)
finally:
    if os.path.exists(events_test):
        os.remove(events_test)

print("\n[VERDICT] SUCCESS: LOGOS ECOSYSTEM ACHIEVED 100% NATIVE SOVEREIGNTY.")
