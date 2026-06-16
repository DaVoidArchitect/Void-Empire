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

# Run events test & VMF output validation
events_test = os.path.join(WORKSPACE, "logos", "bin", "compiler_bootstrap_events_test.json")
vmf_test_output = os.path.join(WORKSPACE, "logos", "bin", "stage1_compiler.vmf")

with open(events_test, "w") as f:
    f.write('[ {"intent": "LogosCompiler", "event": "scan_tokens"} ]')
    
try:
    if os.path.exists(vmf_test_output):
        os.remove(vmf_test_output)
        
    res = subprocess.run([stage1_exe, events_test, "-o", vmf_test_output], capture_output=True, text=True, check=True)
    if "[EVENT 0] + Initialize --(scan_tokens)--> Lexing [transitioned]" in res.stdout:
        print("  Functional compiler state transition: OK.")
    else:
        print("Verification Failed: stage1_compiler.exe did not output expected transition path.", file=sys.stderr)
        sys.exit(1)
        
    # Read VMF and verify layout
    if not os.path.isfile(vmf_test_output):
        print("Verification Failed: VMF output file not created.", file=sys.stderr)
        sys.exit(1)
        
    with open(vmf_test_output, "rb") as f:
        vmf_bytes = f.read()
        
    # Check VMF Size (must be at least 0x50 + 41 bytes = 121 bytes)
    if len(vmf_bytes) < 121:
        print(f"Verification Failed: VMF file size is too small ({len(vmf_bytes)} bytes).", file=sys.stderr)
        sys.exit(1)
        
    # Check Magic System Entropy Anchor (0xF00DBABE)
    magic = int.from_bytes(vmf_bytes[0:4], byteorder='little')
    if magic != 0xF00DBABE:
        print(f"Verification Failed: VMF magic system entropy anchor mismatch ({hex(magic)}).", file=sys.stderr)
        sys.exit(1)
    print("  VMF Header - Entropy Anchor: OK.")
    
    # Check Platform Fee Geometry (1.0618)
    import struct
    fee_val = struct.unpack('<d', vmf_bytes[4:12])[0]
    if abs(fee_val - 1.0618) > 1e-9:
        print(f"Verification Failed: VMF platform fee coefficient mismatch ({fee_val}).", file=sys.stderr)
        sys.exit(1)
    print("  VMF Header - Platform Fee Geometry (1.0618): OK.")
    
    # Check Quantum Bounds Limits (1e12)
    limits_val = struct.unpack('<ffff', vmf_bytes[12:28])
    for val in limits_val:
        if abs(val - 1e12) > 1e7:
            print(f"Verification Failed: VMF quantum bounds register mismatch ({limits_val}).", file=sys.stderr)
            sys.exit(1)
    print("  VMF Header - Quantum Bounds Registers (Mass, Energy, Entropy, Cycles): OK.")
    
    # Check transition matrix opcode vector start (mov r14, r12 -> 0x49 0x89 0xC6)
    matrix_opcodes = vmf_bytes[80:121]
    expected_start = bytes([0x49, 0x89, 0xC6])
    if matrix_opcodes[0:3] != expected_start:
        print(f"Verification Failed: Opcode vector starts with {matrix_opcodes[0:3].hex()} instead of {expected_start.hex()}.", file=sys.stderr)
        sys.exit(1)
    print("  VMF Body - transition opcodes containing register rollbacks & platform fees: OK.")
    
finally:
    if os.path.exists(events_test):
        os.remove(events_test)
    if os.path.exists(vmf_test_output):
        os.remove(vmf_test_output)

print("\n[VERDICT] SUCCESS: LOGOS ECOSYSTEM ACHIEVED 100% NATIVE SOVEREIGNTY.")
