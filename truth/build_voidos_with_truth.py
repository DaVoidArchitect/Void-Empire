import urllib.request
import json
import os
import sys
from pathlib import Path

# Setup directories
WORKSPACE = Path("c:/Users/voidi/OneDrive/Desktop/VOID Empire")
LOGOS_DIR = WORKSPACE / "logos"
OUTPUT_DIR = WORKSPACE / "voidos_in_logos"
os.makedirs(str(OUTPUT_DIR), exist_ok=True)

if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from logos import compile_logos

def query_truth(prompt: str) -> str:
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "Truth",
        "prompt": prompt,
        "stream": False
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as res:
            response_data = json.loads(res.read().decode("utf-8"))
            return response_data.get("response", "")
    except Exception as e:
        print(f"Error querying Truth API: {e}")
        return ""

def clean_code(raw_response: str) -> str:
    # Extract code from ```logos ... ``` or ``` ... ```
    code = ""
    if "```logos" in raw_response:
        parts = raw_response.split("```logos")
        code = parts[1].split("```")[0].strip()
    elif "```" in raw_response:
        parts = raw_response.split("```")
        code = parts[1].split("```")[0].strip()
    else:
        code = raw_response.strip()
    # Replace single quotes with double quotes for strings
    code = code.replace("'", '"')
    return code

def build_module(name: str, prompt: str):
    print(f"\n[TRUTH] Prompting local AI Truth for '{name}.logos'...")
    raw_res = query_truth(prompt)
    if not raw_res:
        print(f"[ERROR] No response received for '{name}'")
        return False
    
    code = clean_code(raw_res)
    file_path = OUTPUT_DIR / f"{name}.logos"
    file_path.write_text(code, encoding="utf-8")
    print(f"[SUCCESS] Saved generated module to: {file_path.relative_to(WORKSPACE)}")
    print("Code content:")
    print(code)
    
    # Run compilation check
    print(f"Checking compilation of '{name}.logos'...")
    try:
        mock_mesh = {
            "mass": 1000.0,
            "energy": 3.6e9,  # 1000 kWh
            "entropy": 10.0,
            "cycle": 1000.0
        }
        compile_logos(code, mock_mesh, source_path=str(file_path))
        print(f"[VERDICT] '{name}.logos' compiled successfully!")
        return True
    except Exception as e:
        print(f"[VERDICT] '{name}.logos' compilation failed: {e}")
        return False

def main():
    modules = {
        "mailbox": (
            "Create a fully functional Logos intent named Mailbox representing an anti-replay counter mailbox. "
            "It must have license \"PRIVATE\", scope \"Subnet\", target \"capability_verifier\", and steward \"kernel_hal\". "
            "It must require energy 50.0 Wh. "
            "It starts in state Idle. On event 'receive_envelope': "
            "1. If replayed == 1, transition back to Idle, requiring energy 1.0 Wh. "
            "2. If replayed == 0 and is_valid_sig == 1, transition to state Processing, requiring energy 0.1 Wh. "
            "3. If replayed == 0 and is_valid_sig == 0, transition to Idle, requiring energy 0.5 Wh. "
            "The Processing state must transition on 'done' to Idle with no resource requirements. "
            "Use strict Logos v2.0 pure declarative syntax with semicolons."
        ),
        "scheduler": (
            "Create a fully functional Logos intent named Scheduler representing a priority task execution scheduler. "
            "It must have license \"PRIVATE\", scope \"Subnet\", target \"scheduler_core\", and steward \"kernel_core\". "
            "It must require energy 100.0 Wh. "
            "It starts in state Idle. On event 'dispatch_task': "
            "1. If priority > 2, transition to state Running, requiring energy 2.0 Wh. "
            "2. If priority <= 2, transition to state Running, requiring energy 0.5 Wh. "
            "The Running state must transition on 'complete' to Idle with no resource requirements. "
            "Use strict Logos v2.0 pure declarative syntax with semicolons."
        ),
        "treasury": (
            "Create a fully functional Logos intent named Treasury representing the Void economic coordination service. "
            "It must have license \"RESTRICTED_LICENSE\", scope \"Global\", target \"settlement_ledger\", and steward \"genesis_treasury\". "
            "It must require energy 200.0 Wh. "
            "It starts in state Idle. On event 'process_payment': "
            "1. If is_inter_subnet == 1, transition to state Settled, requiring energy 6.18 Wh. "
            "2. If is_inter_subnet == 0, transition to state Settled, requiring energy 1.618 Wh. "
            "The Settled state must transition on 'reset' to Idle with no resource requirements. "
            "Use strict Logos v2.0 pure declarative syntax with semicolons."
        )
    }
    
    success = True
    for name, prompt in modules.items():
        res = build_module(name, prompt)
        if not res:
            success = False
            
    if success:
        print("\n=======================================================")
        print("[SUCCESS] All VoidOS modules successfully built by Truth AI!")
        print("=======================================================")
        sys.exit(0)
    else:
        print("\n[ERROR] One or more VoidOS modules failed compilation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
