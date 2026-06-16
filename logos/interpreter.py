import os
import sys
import json
import tempfile
import subprocess
import re
from .exceptions import LogosRuntimeError

class LogosVM:
    def __init__(self, smir_or_bytecode, mesh, runtime_ctx=None):
        self.mesh = dict(mesh)
        self.runtime_ctx = dict(runtime_ctx or {})
        self.event_log = []
        
        # Parse smir_or_bytecode
        if isinstance(smir_or_bytecode, bytes):
            try:
                self.smir = json.loads(smir_or_bytecode.decode('utf-8'))
            except Exception:
                try:
                    from .vsmb import decode_vsmb
                    self.smir = decode_vsmb(smir_or_bytecode)
                except Exception:
                    self.smir = {}
        else:
            self.smir = smir_or_bytecode
            
        self.current_states = {}
        for intent in self.smir.get("intents", []):
            name = intent["name"]
            self.current_states[name] = intent["states"][0]["name"] if intent["states"] else "Idle"
            
        # Compile the SMIR to C code
        from .compiler import Compiler
        compiler = Compiler(self.mesh)
        c_code = compiler.compile_to_c(self.smir)
        
        # Create a temp directory for compiling and running the binary
        self.temp_dir = tempfile.mkdtemp()
        self.c_file = os.path.join(self.temp_dir, "app.c")
        self.exe_file = os.path.join(self.temp_dir, "app.exe")
        
        with open(self.c_file, "w", encoding="utf-8") as f:
            f.write(c_code)
            
        gcc_path = r"C:\Users\voidi\AppData\Local\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.MCF.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin\gcc.exe"
        cmd = [gcc_path, self.c_file, "-O2", "-o", self.exe_file]
        subprocess.run(cmd, check=True, capture_output=True)

    def current_state(self, intent_name: str) -> str:
        return self.current_states.get(intent_name, "Idle")

    def send_event(self, intent_name: str, event_name: str) -> dict:
        if intent_name not in self.current_states:
            raise LogosRuntimeError(f"Intent {intent_name} not found in this model")
            
        from_state = self.current_states[intent_name]
            
        # Create events JSON
        events_data = [{"intent": intent_name, "event": event_name}]
        events_file = os.path.join(self.temp_dir, "events.json")
        with open(events_file, "w") as f:
            json.dump(events_data, f)
            
        # Create mesh JSON
        mesh_file = os.path.join(self.temp_dir, "mesh.json")
        with open(mesh_file, "w") as f:
            json.dump(self.mesh, f)
            
        # Create context JSON (including current states and context variables)
        ctx_data = dict(self.runtime_ctx)
        for name, state in self.current_states.items():
            ctx_data[f"{name.lower()}_state"] = state
            
        context_file = os.path.join(self.temp_dir, "context.json")
        with open(context_file, "w") as f:
            json.dump(ctx_data, f)
            
        # Run the executable
        cmd = [self.exe_file, events_file, "-m", mesh_file, "-c", context_file]
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        # Log event run
        self.event_log.append({
            "intent": intent_name,
            "event": event_name,
            "stdout": res.stdout,
            "stderr": res.stderr
        })
        
        status = "no_match"
        to_state = from_state
        detail = ""
        
        lines = res.stdout.splitlines()
        for idx, line in enumerate(lines):
            match = re.match(r"^\[EVENT \d+\]\s+([+\-?])\s+(\w+)\s+--\((\w+)\)-->\s+(\w+)\s+\[(\w+)\]", line)
            if match:
                icon, from_s, event_s, to_s, status_s = match.groups()
                if event_s == event_name:
                    status = status_s
                    to_state = to_s
                    if status != "transitioned" and idx + 1 < len(lines):
                        detail_line = lines[idx+1]
                        detail_match = re.match(r"^\s+Detail:\s*(.*)", detail_line)
                        if detail_match:
                            detail = detail_match.group(1).strip()
                            
        # Parse final mesh values
        for idx, line in enumerate(lines):
            if "[LOGOS VM] Final mesh:" in line:
                for offset in range(1, 5):
                    if idx + offset < len(lines):
                        m_line = lines[idx+offset]
                        m_match = re.match(r"^\s+(\w+):\s*([\d\.\-]+)", m_line)
                        if m_match:
                            res_name, val_s = m_match.groups()
                            if res_name in self.mesh:
                                self.mesh[res_name] = float(val_s)
                                
        if status == "transitioned":
            self.current_states[intent_name] = to_state
            
        return {
            "status": status,
            "from": from_state,
            "to": to_state,
            "detail": detail or "OK"
        }
