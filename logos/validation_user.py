"""
Logos Golden Path End-to-End Validation Suite
=============================================
Compiles custom declarative Logos programs with imports and evaluates them
using the Logos VM under complex scenarios.
"""

import os
import sys
import tempfile
import json
import traceback

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logos import compile_logos, LogosVM
from logos.exceptions import LogosCompilerError, LogosRuntimeError

def print_banner(text):
    print("=" * 80)
    print(f"  {text}")
    print("=" * 80)

def main():
    print_banner("LOGOS GOLDEN PATH VALIDATION")
    
    # 1. Setup multi-file scenario
    with tempfile.TemporaryDirectory() as tmpdir:
        common_path = os.path.join(tmpdir, "common_resources.logos")
        sensor_path = os.path.join(tmpdir, "custom_sensor.logos")
        
        common_code = """
        # Common library defining standard resources or a base intent
        intent BaseIntent {
            steward: "System steward";
            target: "Base Node";
            license: "CC0-1.0";
            scope: "global";
            provenance: "base";
            lifetime: 10 days;
            require {
                cycle 1 cycles;
            }
            state Init {
                on ping -> Active;
            }
            state Active {
                on reset -> Init;
            }
        }
        """
        
        sensor_code = """
        import "common_resources.logos";

        intent CustomSensor {
            steward: "Steward Grid";
            target: "Sensor Unit 42";
            license: "MIT";
            scope: "local";
            provenance: "sensor_stream";
            lifetime: 2 days;

            require {
                mass 10.0 kg;
                energy 100.0 Wh;
                entropy 5.0;
                cycle 100 cycles;
            }

            constraint {
                energy max 10.0 kWh;
                entropy max 50.0;
                mass min 1.0 kg;
            }

            state Booting {
                on power_on [voltage_ok == 1] -> Idle {
                    require energy 10.0 Wh;
                }
            }

            state Idle {
                on trigger_reading -> Measuring {
                    require energy 5.0 Wh;
                }
                on shutdown -> PoweredOff;
            }

            state Measuring {
                on read_success [temp < 100.0] -> Idle {
                    require energy 2.0 Wh;
                }
                on read_high [temp >= 100.0] -> Alarm {
                    require energy 10.0 Wh;
                }
                on read_error -> Idle;
            }

            state Alarm {
                on reset_alarm -> Idle;
            }

            state PoweredOff {
            }
        }
        """
        
        with open(common_path, "w", encoding="utf-8") as f:
            f.write(common_code)
        with open(sensor_path, "w", encoding="utf-8") as f:
            f.write(sensor_code)
            
        print(f"Created temporary Logos files:\n - {common_path}\n - {sensor_path}\n")

        # 2. Compile custom_sensor.logos
        mesh_context = {
            "mass": 1000.0,      # kg
            "energy": 3600000.0,  # J (1 kWh)
            "entropy": 10.0,      # J/K
            "cycle": 1000.0       # cycles
        }
        
        print("Compiling program with mesh context:")
        print(json.dumps(mesh_context, indent=2))
        
        try:
            smir = compile_logos(sensor_code, mesh_context, source_path=sensor_path)
            print("\nCompilation SUCCESSFUL! SMIR generated.")
            print(f"Intents compiled: {[i['name'] for i in smir['intents']]}")
        except LogosCompilerError as e:
            print(f"\nCompilation FAILED: {e}", file=sys.stderr)
            traceback.print_exc()
            sys.exit(1)
            
        # 3. Instantiate LogosVM
        # Let's clone mesh to verify modifications
        vm_mesh = dict(mesh_context)
        runtime_context = {"voltage_ok": 1, "temp": 25.0}
        vm = LogosVM(smir, vm_mesh, runtime_context)
        
        # 4. Simulation of BaseIntent
        print_banner("SIMULATING BaseIntent")
        print(f"Initial state: {vm.current_state('BaseIntent')}")
        
        res = vm.send_event("BaseIntent", "ping")
        print(f"Event 'ping': {res['from']} -> {res['to']} [{res['status']}]")
        assert res['status'] == 'transitioned'
        assert res['to'] == 'Active'
        
        res = vm.send_event("BaseIntent", "reset")
        print(f"Event 'reset': {res['from']} -> {res['to']} [{res['status']}]")
        assert res['status'] == 'transitioned'
        assert res['to'] == 'Init'
        
        # 5. Simulation of CustomSensor
        print_banner("SIMULATING CustomSensor")
        print(f"Initial state: {vm.current_state('CustomSensor')}")
        assert vm.current_state('CustomSensor') == 'Booting'
        
        # Power on (requires energy 10 Wh = 36,000 J)
        # 3,600,000 J available -> 3,564,000 J remaining
        res = vm.send_event("CustomSensor", "power_on")
        print(f"Event 'power_on' [voltage_ok=1]: {res['from']} -> {res['to']} [{res['status']}]")
        assert res['status'] == 'transitioned'
        assert res['to'] == 'Idle'
        assert vm.mesh['energy'] == 3600000.0 - 36000.0
        
        # Trigger reading (requires energy 5 Wh = 18,000 J)
        # 3,564,000 J available -> 3,546,000 J remaining
        res = vm.send_event("CustomSensor", "trigger_reading")
        print(f"Event 'trigger_reading': {res['from']} -> {res['to']} [{res['status']}]")
        assert res['status'] == 'transitioned'
        assert res['to'] == 'Measuring'
        assert vm.mesh['energy'] == 3564000.0 - 18000.0
        
        # High reading (requires energy 10 Wh = 36,000 J, temp >= 100)
        # Change context first
        vm.runtime_ctx['temp'] = 105.0
        res = vm.send_event("CustomSensor", "read_high")
        print(f"Event 'read_high' [temp=105.0]: {res['from']} -> {res['to']} [{res['status']}]")
        assert res['status'] == 'transitioned'
        assert res['to'] == 'Alarm'
        assert vm.mesh['energy'] == 3546000.0 - 36000.0
        
        # Reset alarm (requires nothing)
        res = vm.send_event("CustomSensor", "reset_alarm")
        print(f"Event 'reset_alarm': {res['from']} -> {res['to']} [{res['status']}]")
        assert res['status'] == 'transitioned'
        assert res['to'] == 'Idle'
        
        # Shutdown
        res = vm.send_event("CustomSensor", "shutdown")
        print(f"Event 'shutdown': {res['from']} -> {res['to']} [{res['status']}]")
        assert res['status'] == 'transitioned'
        assert res['to'] == 'PoweredOff'
        
        print("\nAll CustomSensor transitions verified successfully.")
        print(f"Final Mesh Resource Levels: {vm.mesh}")
        
    print_banner("GOLDEN PATH VALIDATION: ALL PASSED")

if __name__ == "__main__":
    main()
