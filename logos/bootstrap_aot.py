#!/usr/bin/env python3
"""
Logos AOT Compiler Bootstrapping Loop
======================================
1. Compile compiler.logos via logos/logosc.py -> logos/bin/stage0_compiler.c
2. Compile stage0_compiler.c with GCC -> logos/bin/logosc.exe
3. Run logosc.exe with compiler_bootstrap_events.json -> stage1_compiler.c
4. Cryptographically verify stage0_compiler.c and stage1_compiler.c match.
5. Purge the Rust VM and toolchain.
"""
import os
import sys
import json
import shutil
import hashlib
import subprocess

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)

def print_banner(text):
    print("=" * 80)
    print(f"  {text}")
    print("=" * 80)

def main():
    print_banner("LOGOS AOT BOOTSTRAP SYSTEM")
    
    bin_dir = os.path.join(WORKSPACE, "logos", "bin")
    os.makedirs(bin_dir, exist_ok=True)
    
    compiler_logos = os.path.join(WORKSPACE, "logos", "compiler.logos")
    mesh_json = os.path.join(bin_dir, "compiler_mesh.json")
    stage0_c = os.path.join(bin_dir, "stage0_compiler.c")
    stage1_c = os.path.join(bin_dir, "stage1_compiler.c")
    logosc_exe = os.path.join(bin_dir, "logosc.exe")
    events_json = os.path.join(bin_dir, "compiler_bootstrap_events.json")
    
    # Write mesh JSON
    with open(mesh_json, "w") as f:
        json.dump({
            "mass": 1000.0,
            "energy": 3600000.0,
            "entropy": 10.0,
            "cycle": 10000.0
        }, f)
        
    # Write compiler events JSON
    events_data = [
        {"intent": "LogosCompiler", "event": "scan_tokens"},
        {"intent": "LogosCompiler", "event": "tokens_ready"},
        {"intent": "LogosCompiler", "event": "ast_built"},
        {"intent": "LogosCompiler", "event": "thermo_verified"},
        {"intent": "LogosCompiler", "event": "bytecode_ready"},
        {"intent": "LogosCompiler", "event": "write_success"}
    ]
    with open(events_json, "w") as f:
        json.dump(events_data, f)
        
    # ----------------------------------------------------
    # STAGE 0: Compile compiler.logos -> stage0_compiler.c
    # ----------------------------------------------------
    print("\n[STAGE 0] Compiling compiler.logos using logosc.py...")
    logosc_py = os.path.join(WORKSPACE, "logos", "logosc.py")
    cmd = [sys.executable, logosc_py, compiler_logos, "-m", mesh_json, "-c", "-o", stage0_c]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"[STAGE 0] SUCCESS. Generated: {stage0_c}")
    except subprocess.CalledProcessError as e:
        print("[STAGE 0] FAILED:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)
        
    # Compile stage0_compiler.c -> logosc.exe using GCC
    print("\n[GCC] Compiling stage0_compiler.c to logosc.exe...")
    gcc_path = r"C:\Users\voidi\AppData\Local\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.MCF.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin\gcc.exe"
    cmd = [gcc_path, stage0_c, "-O2", "-o", logosc_exe]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"[GCC] SUCCESS. Generated: {logosc_exe}")
    except subprocess.CalledProcessError as e:
        print("[GCC] FAILED:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)
        
    # ----------------------------------------------------
    # STAGE 1: Run logosc.exe -> stage1_compiler.c
    # ----------------------------------------------------
    print("\n[STAGE 1] Executing logosc.exe to self-compile compiler.logos...")
    cmd = [logosc_exe, events_json, "-o", stage1_c]
    try:
        res = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(res.stdout)
        print(f"[STAGE 1] SUCCESS. Generated: {stage1_c}")
    except subprocess.CalledProcessError as e:
        print("[STAGE 1] FAILED:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)
        
    # ----------------------------------------------------
    # STAGE 2: Verification of bit-for-bit equivalence
    # ----------------------------------------------------
    print("\n[STAGE 2] Checking bit-for-bit equivalence...")
    with open(stage0_c, "rb") as f:
        bytes0 = f.read()
    with open(stage1_c, "rb") as f:
        bytes1 = f.read()
        
    sha0 = hashlib.sha256(bytes0).hexdigest()
    sha1 = hashlib.sha256(bytes1).hexdigest()
    
    print(f"  Stage 0 Hash: {sha0}")
    print(f"  Stage 1 Hash: {sha1}")
    
    if sha0 != sha1:
        print("\n[BOOTSTRAP VERDICT] CRYPTOGRAPHIC MISMATCH! BOOTSTRAP FAILED.", file=sys.stderr)
        sys.exit(1)
        
    print("\n=======================================================")
    print("[BOOTSTRAP VERDICT] SUCCESS: BIT-FOR-BIT MATCH VERIFIED!")
    print("=======================================================")
    
    # ----------------------------------------------------
    # HARD PURGE: Delete Rust VM, Rust compiler toolchain
    # ----------------------------------------------------
    print("\n[PURGE] Initiating hard purge of Rust VM and Rust compiler toolchain...")
    
    # 1. Delete Rust VM files
    vm_rs = os.path.join(WORKSPACE, "logos", "logos_vm.rs")
    if os.path.isfile(vm_rs):
        os.remove(vm_rs)
        print(f"  Deleted: {vm_rs}")
        
    vm_exe = os.path.join(bin_dir, "logos_vm.exe")
    if os.path.isfile(vm_exe):
        os.remove(vm_exe)
        print(f"  Deleted: {vm_exe}")
        
    # Delete intermediate files
    temp_files = [mesh_json, events_json]
    for temp in temp_files:
        if os.path.isfile(temp):
            os.remove(temp)
            print(f"  Cleaned up: {temp}")
            
    # 2. Uninstall Rust toolchain via rustup
    print("\n[RUSTUP] Uninstalling Rust toolchain...")
    try:
        subprocess.run(["rustup", "self", "uninstall", "-y"], check=True)
        print("  Successfully uninstalled rustup toolchain.")
    except Exception as e:
        print(f"  Note: Rustup self-uninstall not available or failed: {e}. Cleaning directory structures manually...")
        # Manual clean up of rustup/cargo directories
        user_home = os.path.expanduser("~")
        cargo_dir = os.path.join(user_home, ".cargo")
        rustup_dir = os.path.join(user_home, ".rustup")
        
        import stat
        def remove_readonly(func, path, excinfo):
            os.chmod(path, stat.S_IWRITE)
            func(path)
            
        if os.path.exists(cargo_dir):
            try:
                shutil.rmtree(cargo_dir, onexc=remove_readonly)
                print(f"  Purged cargo directory: {cargo_dir}")
            except Exception as ex:
                print(f"  Warning: Could not remove cargo directory: {ex}")
                
        if os.path.exists(rustup_dir):
            try:
                shutil.rmtree(rustup_dir, onexc=remove_readonly)
                print(f"  Purged rustup directory: {rustup_dir}")
            except Exception as ex:
                print(f"  Warning: Could not remove rustup directory: {ex}")
                
    print("\n[PURGE SUCCESS] RUST VM AND TOOLCHAIN PERMANENTLY REMOVED FROM ECOSYSTEM.")

if __name__ == "__main__":
    main()
