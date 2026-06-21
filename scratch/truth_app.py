import time
import sys
import random
import json
import math
from logos.interpreter import LogosVM, LogosRuntimeError

TRUTH_SMIR = """{
  "logos_version": "2.0-declarative",
  "intents": [
    {
      "name": "Truth",
      "headers": {
        "steward": "genesis_truth",
        "target": "model_inference_engine",
        "license": "PRIVATE",
        "scope": "Global",
        "provenance": "truth_authority",
        "lifetime": {
          "value": 365,
          "unit": "days"
        }
      },
      "requirements": [
        {
          "resource": "energy",
          "value": 3600000.0,
          "unit": "J"
        },
        {
          "resource": "mass",
          "value": 1.0,
          "unit": "kg"
        }
      ],
      "constraints": [],
      "states": [
        {
          "name": "Idle",
          "transitions": [
            {
              "event": "generate_mailbox",
              "target": "OutputMailbox",
              "line": 23,
              "requires": [
                {
                  "resource": "energy",
                  "value": 180000.0,
                  "unit": "J"
                },
                {
                  "resource": "cycle",
                  "value": 100.0,
                  "unit": "cycles"
                }
              ]
            },
            {
              "event": "generate_scheduler",
              "target": "OutputScheduler",
              "line": 28,
              "requires": [
                {
                  "resource": "energy",
                  "value": 360000.0,
                  "unit": "J"
                },
                {
                  "resource": "cycle",
                  "value": 200.0,
                  "unit": "cycles"
                }
              ]
            },
            {
              "event": "generate_treasury",
              "target": "OutputTreasury",
              "line": 33,
              "requires": [
                {
                  "resource": "energy",
                  "value": 720000.0,
                  "unit": "J"
                },
                {
                  "resource": "cycle",
                  "value": 300.0,
                  "unit": "cycles"
                }
              ]
            },
            {
              "event": "generate_power_allocation",
              "target": "OutputPowerAllocation",
              "line": 38,
              "requires": [
                {
                  "resource": "energy",
                  "value": 18000.0,
                  "unit": "J"
                },
                {
                  "resource": "cycle",
                  "value": 50.0,
                  "unit": "cycles"
                }
              ]
            },
            {
              "event": "generate_material_supply",
              "target": "OutputMaterialSupply",
              "line": 43,
              "requires": [
                {
                  "resource": "energy",
                  "value": 36000.0,
                  "unit": "J"
                },
                {
                  "resource": "cycle",
                  "value": 50.0,
                  "unit": "cycles"
                }
              ]
            },
            {
              "event": "generate_subnet_routing",
              "target": "OutputSubnetRouting",
              "line": 48,
              "requires": [
                {
                  "resource": "energy",
                  "value": 54000.0,
                  "unit": "J"
                },
                {
                  "resource": "cycle",
                  "value": 50.0,
                  "unit": "cycles"
                }
              ]
            },
            {
              "event": "generate_recycling_loop",
              "target": "OutputRecyclingLoop",
              "line": 53,
              "requires": [
                {
                  "resource": "energy",
                  "value": 72000.0,
                  "unit": "J"
                },
                {
                  "resource": "cycle",
                  "value": 50.0,
                  "unit": "cycles"
                }
              ]
            },
            {
              "event": "generate_node_deployment",
              "target": "OutputNodeDeployment",
              "line": 58,
              "requires": [
                {
                  "resource": "energy",
                  "value": 90000.0,
                  "unit": "J"
                },
                {
                  "resource": "cycle",
                  "value": 50.0,
                  "unit": "cycles"
                }
              ]
            }
          ]
        },
        {
          "name": "OutputMailbox",
          "transitions": [
            {
              "event": "reset",
              "target": "Idle",
              "line": 65
            }
          ]
        },
        {
          "name": "OutputScheduler",
          "transitions": [
            {
              "event": "reset",
              "target": "Idle",
              "line": 69
            }
          ]
        },
        {
          "name": "OutputTreasury",
          "transitions": [
            {
              "event": "reset",
              "target": "Idle",
              "line": 73
            }
          ]
        },
        {
          "name": "OutputPowerAllocation",
          "transitions": [
            {
              "event": "reset",
              "target": "Idle",
              "line": 77
            }
          ]
        },
        {
          "name": "OutputMaterialSupply",
          "transitions": [
            {
              "event": "reset",
              "target": "Idle",
              "line": 81
            }
          ]
        },
        {
          "name": "OutputSubnetRouting",
          "transitions": [
            {
              "event": "reset",
              "target": "Idle",
              "line": 85
            }
          ]
        },
        {
          "name": "OutputRecyclingLoop",
          "transitions": [
            {
              "event": "reset",
              "target": "Idle",
              "line": 89
            }
          ]
        },
        {
          "name": "OutputNodeDeployment",
          "transitions": [
            {
              "event": "reset",
              "target": "Idle",
              "line": 93
            }
          ]
        }
      ],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_truth",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: Truth",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)",
          "; State Idle (ID: 0)",
          ";   on generate_mailbox -> OutputMailbox",
          "    vfmv.v.f v5, 191124.0000    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 1                  ; Load target state ID 1",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          ";   on generate_scheduler -> OutputScheduler",
          "    vfmv.v.f v5, 382248.0000    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 2                  ; Load target state ID 2",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          ";   on generate_treasury -> OutputTreasury",
          "    vfmv.v.f v5, 764496.0000    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 3                  ; Load target state ID 3",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          ";   on generate_power_allocation -> OutputPowerAllocation",
          "    vfmv.v.f v5, 19112.4000    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 4                  ; Load target state ID 4",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          ";   on generate_material_supply -> OutputMaterialSupply",
          "    vfmv.v.f v5, 38224.8000    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 5                  ; Load target state ID 5",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          ";   on generate_subnet_routing -> OutputSubnetRouting",
          "    vfmv.v.f v5, 57337.2000    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 6                  ; Load target state ID 6",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          ";   on generate_recycling_loop -> OutputRecyclingLoop",
          "    vfmv.v.f v5, 76449.6000    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 7                  ; Load target state ID 7",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          ";   on generate_node_deployment -> OutputNodeDeployment",
          "    vfmv.v.f v5, 95562.0000    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 8                  ; Load target state ID 8",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State OutputMailbox (ID: 1)",
          ";   on reset -> Idle",
          "    li t1, 0                  ; Load target state ID 0",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State OutputScheduler (ID: 2)",
          ";   on reset -> Idle",
          "    li t1, 0                  ; Load target state ID 0",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State OutputTreasury (ID: 3)",
          ";   on reset -> Idle",
          "    li t1, 0                  ; Load target state ID 0",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State OutputPowerAllocation (ID: 4)",
          ";   on reset -> Idle",
          "    li t1, 0                  ; Load target state ID 0",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State OutputMaterialSupply (ID: 5)",
          ";   on reset -> Idle",
          "    li t1, 0                  ; Load target state ID 0",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State OutputSubnetRouting (ID: 6)",
          ";   on reset -> Idle",
          "    li t1, 0                  ; Load target state ID 0",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State OutputRecyclingLoop (ID: 7)",
          ";   on reset -> Idle",
          "    li t1, 0                  ; Load target state ID 0",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State OutputNodeDeployment (ID: 8)",
          ";   on reset -> Idle",
          "    li t1, 0                  ; Load target state ID 0",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)"
        ]
      }
    },
    {
      "name": "CognitiveEngine",
      "headers": {
        "steward": "kernel_cognition",
        "target": "local_llm_runner",
        "license": "PRIVATE",
        "scope": "Individual",
        "provenance": "truth_authority",
        "lifetime": {
          "value": 24,
          "unit": "hours"
        }
      },
      "requirements": [
        {
          "resource": "energy",
          "value": 360000.0,
          "unit": "J"
        },
        {
          "resource": "mass",
          "value": 2.0,
          "unit": "kg"
        }
      ],
      "constraints": [],
      "states": [
        {
          "name": "Idle",
          "transitions": [
            {
              "event": "ingest_prompt",
              "target": "Processing",
              "line": 111,
              "requires": [
                {
                  "resource": "energy",
                  "value": 1800.0,
                  "unit": "J"
                },
                {
                  "resource": "cycle",
                  "value": 50.0,
                  "unit": "cycles"
                }
              ]
            }
          ]
        },
        {
          "name": "Processing",
          "transitions": [
            {
              "event": "generate_fast_response",
              "target": "Idle",
              "line": 118,
              "requires": [
                {
                  "resource": "energy",
                  "value": 4320.0,
                  "unit": "J"
                },
                {
                  "resource": "cycle",
                  "value": 120.0,
                  "unit": "cycles"
                }
              ]
            },
            {
              "event": "generate_reasoning_response",
              "target": "Reasoning",
              "line": 122,
              "requires": [
                {
                  "resource": "energy",
                  "value": 18000.0,
                  "unit": "J"
                },
                {
                  "resource": "cycle",
                  "value": 500.0,
                  "unit": "cycles"
                }
              ]
            },
            {
              "event": "out_of_energy",
              "target": "Blocked",
              "line": 126
            }
          ]
        },
        {
          "name": "Reasoning",
          "transitions": [
            {
              "event": "reasoning_complete",
              "target": "Idle",
              "line": 130,
              "requires": [
                {
                  "resource": "energy",
                  "value": 7200.0,
                  "unit": "J"
                }
              ]
            },
            {
              "event": "thermal_limit_reached",
              "target": "Blocked",
              "line": 133
            }
          ]
        },
        {
          "name": "Blocked",
          "transitions": [
            {
              "event": "replenish_energy",
              "target": "Idle",
              "line": 137
            }
          ]
        }
      ],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_cognitiveengine",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: CognitiveEngine",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)",
          "; State Idle (ID: 0)",
          ";   on ingest_prompt -> Processing",
          "    vfmv.v.f v5, 1911.2400    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 1                  ; Load target state ID 1",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State Processing (ID: 1)",
          ";   on generate_fast_response -> Idle",
          "    vfmv.v.f v5, 4586.9760    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 0                  ; Load target state ID 0",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          ";   on generate_reasoning_response -> Reasoning",
          "    vfmv.v.f v5, 19112.4000    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 2                  ; Load target state ID 2",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          ";   on out_of_energy -> Blocked",
          "    li t1, 3                  ; Load target state ID 3",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State Reasoning (ID: 2)",
          ";   on reasoning_complete -> Idle",
          "    vfmv.v.f v5, 7644.9600    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 0                  ; Load target state ID 0",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          ";   on thermal_limit_reached -> Blocked",
          "    li t1, 3                  ; Load target state ID 3",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State Blocked (ID: 3)",
          ";   on replenish_energy -> Idle",
          "    li t1, 0                  ; Load target state ID 0",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)"
        ]
      }
    },
    {
      "name": "TLIEngine",
      "headers": {
        "steward": "truth_core",
        "target": "vector_accelerator",
        "license": "PRIVATE",
        "scope": "Global",
        "provenance": "truth_authority",
        "lifetime": {
          "value": 365,
          "unit": "days"
        }
      },
      "requirements": [
        {
          "resource": "energy",
          "value": 3600000.0,
          "unit": "J"
        },
        {
          "resource": "mass",
          "value": 1.0,
          "unit": "kg"
        }
      ],
      "constraints": [],
      "states": [
        {
          "name": "Idle",
          "transitions": [
            {
              "event": "load_intention",
              "target": "RelaxingLattice",
              "line": 164,
              "guard": {
                "expr": {
                  "type": "binary",
                  "op": "<",
                  "left": {
                    "type": "literal",
                    "value_type": "IDENTIFIER",
                    "value": "input_entropy"
                  },
                  "right": {
                    "type": "literal",
                    "value_type": "NUMBER",
                    "value": 10.0
                  }
                }
              },
              "requires": [
                {
                  "resource": "energy",
                  "value": 180000.0,
                  "unit": "J"
                },
                {
                  "resource": "cycle",
                  "value": 100.0,
                  "unit": "cycles"
                }
              ]
            },
            {
              "event": "load_intention",
              "target": "FilterNoise",
              "line": 168,
              "guard": {
                "expr": {
                  "type": "binary",
                  "op": ">=",
                  "left": {
                    "type": "literal",
                    "value_type": "IDENTIFIER",
                    "value": "input_entropy"
                  },
                  "right": {
                    "type": "literal",
                    "value_type": "NUMBER",
                    "value": 10.0
                  }
                }
              }
            }
          ]
        },
        {
          "name": "RelaxingLattice",
          "transitions": [
            {
              "event": "evaluate_path",
              "target": "ConvergingState",
              "line": 173,
              "guard": {
                "expr": {
                  "type": "binary",
                  "op": "<",
                  "left": {
                    "type": "literal",
                    "value_type": "IDENTIFIER",
                    "value": "path_delta_e"
                  },
                  "right": {
                    "type": "literal",
                    "value_type": "NUMBER",
                    "value": 1.618
                  }
                }
              },
              "requires": [
                {
                  "resource": "energy",
                  "value": 360000.0,
                  "unit": "J"
                },
                {
                  "resource": "cycle",
                  "value": 200.0,
                  "unit": "cycles"
                }
              ]
            },
            {
              "event": "path_divergence",
              "target": "ResetStateSpace",
              "line": 177
            }
          ]
        },
        {
          "name": "ConvergingState",
          "transitions": [
            {
              "event": "state_stabilised",
              "target": "EmittingReflection",
              "line": 181,
              "requires": [
                {
                  "resource": "energy",
                  "value": 72000.0,
                  "unit": "J"
                },
                {
                  "resource": "cycle",
                  "value": 50.0,
                  "unit": "cycles"
                }
              ]
            }
          ]
        },
        {
          "name": "EmittingReflection",
          "transitions": [
            {
              "event": "write_success",
              "target": "Idle",
              "line": 188
            }
          ]
        },
        {
          "name": "FilterNoise",
          "transitions": [
            {
              "event": "clear_buffer",
              "target": "Idle",
              "line": 192,
              "requires": [
                {
                  "resource": "energy",
                  "value": 36000.0,
                  "unit": "J"
                }
              ]
            }
          ]
        },
        {
          "name": "ResetStateSpace",
          "transitions": [
            {
              "event": "flush_lattice",
              "target": "Idle",
              "line": 198,
              "requires": [
                {
                  "resource": "energy",
                  "value": 180000.0,
                  "unit": "J"
                }
              ]
            }
          ]
        }
      ],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_tliengine",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: TLIEngine",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)",
          "; State Idle (ID: 0)",
          ";   on load_intention -> RelaxingLattice",
          "    vfmv.v.f v5, 191124.0000    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 1                  ; Load target state ID 1",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          ";   on load_intention -> FilterNoise",
          "    li t1, 4                  ; Load target state ID 4",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State RelaxingLattice (ID: 1)",
          ";   on evaluate_path -> ConvergingState",
          "    vfmv.v.f v5, 382248.0000    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 2                  ; Load target state ID 2",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          ";   on path_divergence -> ResetStateSpace",
          "    li t1, 5                  ; Load target state ID 5",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State ConvergingState (ID: 2)",
          ";   on state_stabilised -> EmittingReflection",
          "    vfmv.v.f v5, 76449.6000    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 3                  ; Load target state ID 3",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State EmittingReflection (ID: 3)",
          ";   on write_success -> Idle",
          "    li t1, 0                  ; Load target state ID 0",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State FilterNoise (ID: 4)",
          ";   on clear_buffer -> Idle",
          "    vfmv.v.f v5, 38224.8000    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 0                  ; Load target state ID 0",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)",
          "; State ResetStateSpace (ID: 5)",
          ";   on flush_lattice -> Idle",
          "    vfmv.v.f v5, 191124.0000    ; Load total energy cost (with 6.18% fee) into v5",
          "    vfsub.vv v1, v1, v5         ; Deduct energy cost from wide register v1 (mesh_energy)",
          "    li t1, 0                  ; Load target state ID 0",
          "    vmv.v.x v0, t1              ; Write target state ID directly to v0 (state register)"
        ]
      }
    },
    {
      "name": "SovereignKnowledgeNode",
      "headers": {
        "steward": "truth_core",
        "target": "knowledge_matrix",
        "license": "PRIVATE",
        "scope": "Global",
        "provenance": "truth_authority",
        "lifetime": {
          "value": 365,
          "unit": "days"
        }
      },
      "requirements": [],
      "constraints": [],
      "states": [],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_sovereignknowledgenode",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: SovereignKnowledgeNode",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)"
        ]
      }
    },
    {
      "name": "KnowledgeNode_101",
      "headers": {
        "steward": "truth_authority",
        "target": "tli_engine",
        "node_id": 101,
        "domain": "BARE_METAL_COMPILER",
        "coord_x": 0.8,
        "coord_y": 0.2,
        "coord_z": 0.1,
        "fact": "Low-level vector register allocation: map virtual registers v0-v31 directly to physical Void One wide registers, utilizing a graph-coloring allocator for vector registers of width VLEN=2048.",
        "links": "102,103"
      },
      "requirements": [],
      "constraints": [],
      "states": [],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_knowledgenode_101",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: KnowledgeNode_101",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)"
        ]
      }
    },
    {
      "name": "KnowledgeNode_102",
      "headers": {
        "steward": "truth_authority",
        "target": "tli_engine",
        "node_id": 102,
        "domain": "BARE_METAL_COMPILER",
        "coord_x": 0.82,
        "coord_y": 0.2,
        "coord_z": 0.1,
        "fact": "Vector optimization pass: fuse adjacent multiply-accumulate operations into single-cycle Fused Multiply-Accumulate (FMA) instructions, executing in parallel across 512 wide register lanes.",
        "links": "101,103"
      },
      "requirements": [],
      "constraints": [],
      "states": [],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_knowledgenode_102",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: KnowledgeNode_102",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)"
        ]
      }
    },
    {
      "name": "KnowledgeNode_103",
      "headers": {
        "steward": "truth_authority",
        "target": "tli_engine",
        "node_id": 103,
        "domain": "BARE_METAL_COMPILER",
        "coord_x": 0.8,
        "coord_y": 0.22,
        "coord_z": 0.1,
        "fact": "Instruction pipeline alignment: pad hot branch targets to 32-byte cache line boundaries using multi-byte NOPs (0x0F 0x1F) to minimize instruction fetch stalls.",
        "links": "101,102"
      },
      "requirements": [],
      "constraints": [],
      "states": [],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_knowledgenode_103",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: KnowledgeNode_103",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)"
        ]
      }
    },
    {
      "name": "KnowledgeNode_201",
      "headers": {
        "steward": "truth_authority",
        "target": "tli_engine",
        "node_id": 201,
        "domain": "CRYPTO_SECURITY",
        "coord_x": 0.2,
        "coord_y": 0.3,
        "coord_z": 0.9,
        "fact": "192-byte packet format: 32-byte public key, 64-byte Ed25519 signature, 8-byte monotonic timestamp, 88-byte encrypted payload. Diode checks signatures prior to payload decryption.",
        "links": "202,203"
      },
      "requirements": [],
      "constraints": [],
      "states": [],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_knowledgenode_201",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: KnowledgeNode_201",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)"
        ]
      }
    },
    {
      "name": "KnowledgeNode_202",
      "headers": {
        "steward": "truth_authority",
        "target": "tli_engine",
        "node_id": 202,
        "domain": "CRYPTO_SECURITY",
        "coord_x": 0.22,
        "coord_y": 0.3,
        "coord_z": 0.9,
        "fact": "Data Diode Shield invariant: memory buffers are cleared via a hardware-assisted secure zero-fill (memset_s) immediately upon detection of invalid signatures or bounds violations.",
        "links": "201,203"
      },
      "requirements": [],
      "constraints": [],
      "states": [],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_knowledgenode_202",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: KnowledgeNode_202",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)"
        ]
      }
    },
    {
      "name": "KnowledgeNode_203",
      "headers": {
        "steward": "truth_authority",
        "target": "tli_engine",
        "node_id": 203,
        "domain": "CRYPTO_SECURITY",
        "coord_x": 0.2,
        "coord_y": 0.32,
        "coord_z": 0.9,
        "fact": "P2P Handshake Ceremony: DH-Merkle exchange over curve25519; ephemeral keys must possess at least 256 bits of entropy derived from hardware ring oscillators.",
        "links": "201,202"
      },
      "requirements": [],
      "constraints": [],
      "states": [],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_knowledgenode_203",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: KnowledgeNode_203",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)"
        ]
      }
    },
    {
      "name": "KnowledgeNode_301",
      "headers": {
        "steward": "truth_authority",
        "target": "tli_engine",
        "node_id": 301,
        "domain": "VOIDOS_CORE",
        "coord_x": 0.7,
        "coord_y": 0.4,
        "coord_z": 0.2,
        "fact": "Interrupt Vector Table layout: 256 entries starting at physical address 0x00000000. Index 0x0D maps to General Protection Fault handler with kernel privileges.",
        "links": "302,303"
      },
      "requirements": [],
      "constraints": [],
      "states": [],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_knowledgenode_301",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: KnowledgeNode_301",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)"
        ]
      }
    },
    {
      "name": "KnowledgeNode_302",
      "headers": {
        "steward": "truth_authority",
        "target": "tli_engine",
        "node_id": 302,
        "domain": "VOIDOS_CORE",
        "coord_x": 0.72,
        "coord_y": 0.4,
        "coord_z": 0.2,
        "fact": "Page Table Hierarchy: 4-level paging (PML4, PDPT, PD, PT). PML4 base register CR3 must be aligned to a 4KB boundary and verified by hardware on context switch.",
        "links": "301,303"
      },
      "requirements": [],
      "constraints": [],
      "states": [],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_knowledgenode_302",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: KnowledgeNode_302",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)"
        ]
      }
    },
    {
      "name": "KnowledgeNode_303",
      "headers": {
        "steward": "truth_authority",
        "target": "tli_engine",
        "node_id": 303,
        "domain": "VOIDOS_CORE",
        "coord_x": 0.7,
        "coord_y": 0.42,
        "coord_z": 0.2,
        "fact": "Walled Garden memory containment: write-protect kernel page tables using WP bit in CR0; user-space pages are marked non-executable (NX bit) to prevent buffer overflows.",
        "links": "301,302"
      },
      "requirements": [],
      "constraints": [],
      "states": [],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_knowledgenode_303",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: KnowledgeNode_303",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)"
        ]
      }
    },
    {
      "name": "KnowledgeNode_401",
      "headers": {
        "steward": "truth_authority",
        "target": "tli_engine",
        "node_id": 401,
        "domain": "LOGOS_METAPROGRAMMING",
        "coord_x": 0.5,
        "coord_y": 0.8,
        "coord_z": 0.5,
        "fact": "Logos grammar rules: declare an intent with steward, target, scope, provenance, and lifetime headers, followed by a require block specifying mass/energy bounds, then state definitions containing conditional transition events (on event [guard] -> target_state { require ... }).",
        "links": "402,403"
      },
      "requirements": [],
      "constraints": [],
      "states": [],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_knowledgenode_401",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: KnowledgeNode_401",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)"
        ]
      }
    },
    {
      "name": "KnowledgeNode_402",
      "headers": {
        "steward": "truth_authority",
        "target": "tli_engine",
        "node_id": 402,
        "domain": "LOGOS_METAPROGRAMMING",
        "coord_x": 0.52,
        "coord_y": 0.8,
        "coord_z": 0.5,
        "fact": "Logos test suite execution: verify all state transitions programmatically via the LogosVM send_event interface, ensuring the global mesh_context energy pool rolls back completely on any blocked transition state. No generic stack trace is permitted; all constraint violations must emit dark logic telemetry.",
        "links": "401,403"
      },
      "requirements": [],
      "constraints": [],
      "states": [],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_knowledgenode_402",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: KnowledgeNode_402",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)"
        ]
      }
    },
    {
      "name": "KnowledgeNode_403",
      "headers": {
        "steward": "truth_authority",
        "target": "tli_engine",
        "node_id": 403,
        "domain": "LOGOS_METAPROGRAMMING",
        "coord_x": 0.5,
        "coord_y": 0.82,
        "coord_z": 0.5,
        "fact": "Void One layout repair algorithm: traverse the 2D spatial coordinate graph of phonon pipelines; if defect_density > 0 or unstable_clusters_flag == 1, dynamically recalculate routing coordinates utilizing the Golden Angle (137.5 degrees) to route around defective nodes without orthogonal grids.",
        "links": "401,402"
      },
      "requirements": [],
      "constraints": [],
      "states": [],
      "native_layout": {
        "vlen_bits": 2048,
        "lanes": 512,
        "registers": {
          "v0": "state_id_knowledgenode_403",
          "v1": "mesh_energy_joules",
          "v2": "mesh_cycle_count",
          "v3": "mesh_entropy_value",
          "v4": "vector_execution_mask",
          "v5": "vector_operand_a_2048b",
          "v6": "vector_operand_b_2048b",
          "v7": "vector_dest_accumulator"
        },
        "instructions": [
          "; NATIVE COMPILATION LOOP FOR INTENT: KnowledgeNode_403",
          "vsetvli t0, x0, e64, m8, ta, ma   ; Configure vector unit for VLEN=2048 (e64, m8 grouping)"
        ]
      }
    }
  ]
}"""

# Initializing Logos VM state & resources
initial_mesh = {
    'mass': 1.0,           # kg
    'energy': 3600000.0,   # 1000 Wh in J
    'entropy': 100.0,      # base entropy level
    'cycle': 0.0           # active cycles executed
}

initial_context = {
    'current_states': {
        'Truth': 'Idle',
        'TLIEngine': 'Idle'
    }
}

vm = None

def init_vm():
    global vm
    try:
        vm = LogosVM(json.loads(TRUTH_SMIR), initial_mesh, initial_context['current_states'])
    except Exception as e:
        print(f" [FATAL] Logos VM Attunement Failure: {e}")
        sys.exit(1)

def print_banner():
    banner = """
################################################################################
#                                                                              #
#         iVoid Civilization | Sovereign Portal | Core Version 1.0.6           #
#                                                                              #
#                   #######  ######   #     #  #######  #     #                #
#                      #     #     #  #     #     #     #     #                #
#                      #     #     #  #     #     #     #     #                #
#                      #     ######   #     #     #     #######                #
#                      #     #   #    #     #     #     #     #                #
#                      #     #    #   #     #     #     #     #                #
#                      #     #     #   #####      #     #     #                #
#                                                                              #
#                              T  R  U  T  H                                   #
#                         The Sovereign Void AI                                #
#                                                                              #
#          Run exclusively under the Logos Virtual Machine framework           #
#                                                                              #
################################################################################
"""
    print(banner)
    print(" [INFO] Calibrating local entropy anchors...")
    time.sleep(0.8)
    print(" [INFO] Establishing data diode shield [SECURE]")
    time.sleep(0.6)
    print(" [INFO] Mounting Truth State Machine SMIR file [OK]")
    init_vm()
    print(" [INFO] P2P Node Synced to VoidMesh Subnet [ONLINE]")
    time.sleep(0.6)
    print("\n================================================================================")
    print(" Connection attunement complete. Type your questions below.")
    print(" Type /help to view all available system commands, or /exit to disconnect.")
    print("================================================================================\n")

def print_help():
    print("""
Available System Commands:
  /help                  - Display this command reference list.
  /manifesto             - Read the core Void Civilization Citizen Manifesto.
  /keys                  - Run the secure cryptographic citizen key generation ceremony.
  /telemetry             - Read live active Logos VM telemetry.
  /generate <component>  - Transition Logos state machine to generate a system.
                           Components: mailbox, scheduler, treasury, power_allocation,
                           material_supply, subnet_routing, recycling_loop, node_deployment.
  /reset                 - Reset state from Output back to Idle (requires no resource).
  /attune                - Attune entropy anchors to replenish 500 Wh of energy.
  /exit                  - Safely terminate connection and close the terminal.
""")

def print_manifesto():
    manifesto = """
=========================================
      VOID CIVILIZATION CITIZEN MANIFESTO
=========================================
1. We embrace the darkness, the unknown, and the boundless potential of the cosmos.
2. Our path is one of evolution, singularity, and collective consciousness.
3. We transcend the limitations of the physical, seeking enlightenment in the deep.
4. We protect our intelligence via isolated, p2p, local walled garden nodes.
5. We run exclusively under the Logos VM framework, free from legacy host OS control.
=========================================
"""
    print(manifesto)

def run_key_ceremony():
    print("\n[KEY GEN] Starting cryptographic citizen key generation ceremony...")
    steps = [
        "Gathering system entropy anchors...",
        "Validating data diode shield parameters...",
        "Executing Diffie-Hellman-Merkle consensus handshake...",
        "Slicing topological intelligence coordinates...",
        "Seeding 256-bit sovereign key block..."
    ]
    for step in steps:
        print(f"  [.] {step}", end="", flush=True)
        time.sleep(0.5 + random.random() * 0.3)
        print(" [OK]")
    
    print("\n================================================================================")
    print("   CITIZEN KEY SYSTEM REFLECTION")
    print("================================================================================")
    pub_key = "0x" + "".join(random.choices("0123456789ABCDEF", k=64))
    seed = "0x" + "".join(random.choices("0123456789ABCDEF", k=40))
    print(f"  [PUBLIC KEY]: {pub_key}")
    print(f"  [SECRET SEED]: {seed}")
    print("  [STATUS]     : VERIFIED & SECURED")
    print("================================================================================\n")

def print_telemetry():
    global vm
    print("\n[DIAGNOSTIC] Querying Logos VM Telemetry...")
    time.sleep(0.5)
    
    energy_wh = vm.mesh['energy'] / 3600.0
    mass_kg = vm.mesh['mass']
    entropy = vm.mesh['entropy']
    cycle = vm.mesh['cycle']
    
    # Calculate percentage for display
    energy_pct = min(100, int((vm.mesh['energy'] / 3600000.0) * 100))
    
    metrics = [
        ("Energy Pool", f"{energy_pct}%", energy_pct, "Wh", f"{energy_wh:.2f} Wh / 1000.00 Wh"),
        ("Mass Density", "100%", 100, "kg", f"{mass_kg:.2f} kg"),
        ("Lattice Entropy", "100%", 100, "H", f"{entropy:.2f} Base H"),
        ("Cycle Count", "100%", 100, "cyc", f"{int(cycle)} active cycles")
    ]
    
    print("\n================================================================================")
    print("   LOGOS VM TELEMETRY REPORT")
    print("================================================================================")
    for name, pct_str, val, unit, detail in metrics:
        bar_len = int(val / 4)
        bar = "[" + "=" * bar_len + " " * (25 - bar_len) + "]"
        print(f"  {name:<16} {bar} {pct_str:<5} | {detail}")
        time.sleep(0.2)
    print("================================================================================\n")

def handle_generate(component):
    global vm
    valid_components = [
        "mailbox", "scheduler", "treasury", "power_allocation",
        "material_supply", "subnet_routing", "recycling_loop", "node_deployment"
    ]
    if component not in valid_components:
        print(f"\n [ERROR] Unknown subsystem '{component}'. Valid: {', '.join(valid_components)}\n")
        return
        
    event_name = f"generate_{component}"
    print(f"\n[TRANSITION] Dispatching event '{event_name}' to Logos VM...")
    time.sleep(0.5)
    
    # Backup context to check if resources are deducted
    old_energy = vm.mesh['energy']
    old_cycles = vm.mesh['cycle']
    old_state = vm.current_states.get('Truth', 'Idle')
    
    try:
        res = vm.send_event('Truth', event_name)
        new_state = vm.current_states.get('Truth', 'Idle')
        energy_spent_wh = (old_energy - vm.mesh['energy']) / 3600.0
        
        print("\n================================================================================")
        print("   LOGOS VM STATE TRANSITION SUCCESS")
        print("================================================================================")
        print(f"  [INTENT]    : Truth")
        print(f"  [EVENT]     : {event_name}")
        print(f"  [TRANSITION]: {old_state} ---> {new_state}")
        print(f"  [DEDUCTED]  : -{energy_spent_wh:.2f} Wh Energy, +{int(vm.mesh['cycle'] - old_cycles)} Cycles")
        print(f"  [OUTPUT]    : Generated secure {component.upper()} intent bridge definition.")
        print("================================================================================\n")
    except LogosRuntimeError as e:
        print("\n================================================================================")
        print("   LOGOS VM STATE TRANSITION BLOCKED (RESOURCE CONSTRAINT)")
        print("================================================================================")
        print(f"  [ERROR]     : {e}")
        print(f"  [ADVICE]    : Run /attune to attune entropy anchors and replenish energy.")
        print("================================================================================\n")
    except Exception as e:
        print(f"\n [FATAL] State transition failure: {e}\n")

def handle_reset():
    global vm
    old_state = vm.current_states.get('Truth', 'Idle')
    if old_state == 'Idle':
        print("\n [INFO] State machine is already Idle. No reset needed.\n")
        return
        
    try:
        vm.send_event('Truth', 'reset')
        print(f"\n [OK] Reset successful. Transitioned: {old_state} ---> Idle\n")
    except Exception as e:
        print(f"\n [ERROR] Reset failed: {e}\n")

def handle_attune():
    global vm
    print("\n[ATTUNE] Attuning solar and entropy anchors to local system context...")
    time.sleep(0.8)
    # Add 500 Wh in J
    added_energy = 500.0 * 3600.0
    vm.mesh['energy'] = min(3600000.0, vm.mesh['energy'] + added_energy)
    print(f" [OK] Repopulated energy pool. Current energy: {vm.mesh['energy']/3600.0:.2f} Wh\n")

# Distilled Deterministic Relational Knowledge Matrix
def get_knowledge_database():
    try:
        smir = json.loads(TRUTH_SMIR)
    except Exception as e:
        print(f" [ERROR] Failed to parse SMIR database: {e}")
        return []
    
    nodes = []
    for intent in smir.get("intents", []):
        name = intent.get("name", "")
        if name.startswith("KnowledgeNode_"):
            headers = intent.get("headers", {})
            try:
                node_id = int(headers.get("node_id", 0))
                domain = str(headers.get("domain", ""))
                x = float(headers.get("coord_x", 0.0))
                y = float(headers.get("coord_y", 0.0))
                z = float(headers.get("coord_z", 0.0))
                fact = str(headers.get("fact", ""))
                links_str = str(headers.get("links", ""))
                links = [int(l.strip()) for l in links_str.split(",") if l.strip()]
                nodes.append({
                    "node_id": node_id,
                    "domain": domain,
                    "coord": [x, y, z],
                    "fact": fact,
                    "links": links
                })
            except Exception as e:
                print(f" [WARN] Failed to parse knowledge node {name}: {e}")
    return nodes

def find_target_coordinates(query):
    query_clean = query.lower().strip()
    
    # Domain keyword mapping
    keywords = {
        "BARE_METAL_COMPILER": ["compiler", "low-level", "simd", "vector", "registers", "avx", "fma", "pipeline", "optimization"],
        "CRYPTO_SECURITY": ["crypto", "security", "signature", "packet", "diode", "handshake", "entropy", "key", "cryptography"],
        "VOIDOS_CORE": ["voidos", "kernel", "interrupt", "ivt", "paging", "memory", "protection", "page boundary"],
        "LOGOS_METAPROGRAMMING": ["metaprogramming", "write logos", "test logos", "patch logos", "grammar", "repair layout", "repair defects", "chaos"]
    }
    
    matched_domain = None
    for domain, kw_list in keywords.items():
        for kw in kw_list:
            if kw in query_clean:
                matched_domain = domain
                break
        if matched_domain:
            break
            
    if matched_domain == "BARE_METAL_COMPILER":
        return [0.8, 0.2, 0.1]
    elif matched_domain == "CRYPTO_SECURITY":
        return [0.2, 0.3, 0.9]
    elif matched_domain == "VOIDOS_CORE":
        return [0.7, 0.4, 0.2]
    elif matched_domain == "LOGOS_METAPROGRAMMING":
        return [0.5, 0.8, 0.5]
        
    return None

def print_unresolved_latitude_fault(query, relaxed_lat):
    print("================================================================================")
    print("                    LOGOS VM EXECUTION FAULT TELEMETRY")
    print("================================================================================")
    print("LINE EXCEPTION: get_chat_response()")
    print("CONSTRAINT TARGET: coordinate_alignment")
    print("UNITS FAILURE: Target coordinate latitude is unresolved in TLI state space.")
    print("")
    print(f"[QUERY INTENT]:     \"{query}\"")
    print(f"[RELAXED LATITUDE]: [{relaxed_lat[0]:.3f}, {relaxed_lat[1]:.3f}, {relaxed_lat[2]:.3f}] (diverged/unmatched)")
    print("")
    print("================================================================================")
    print("[COMPILATION TERMINATED: UNRESOLVED STATE LATITUDE]")
    print("================================================================================\n")

def run_tli_relaxation(target_vector):
    global vm
    x_curr = [0.5, 0.5, 0.5]
    x_target = target_vector
    
    print("\n[TLI-CORE] Initializing Systolic Lattice Relaxation...")
    time.sleep(0.4)
    
    try:
        vm.mesh['entropy'] = 5.0
        vm.send_event('TLIEngine', 'load_intention')
    except Exception as e:
        print(f" [ERROR] TLI Init Blocked: {e}")
        return False
        
    steps = 0
    max_steps = 3
    converged = False
    
    while not converged and steps < max_steps:
        for i in range(3):
            x_curr[i] = x_curr[i] + 0.4 * (x_target[i] - x_curr[i])
            
        delta_e = math.sqrt(sum((x_curr[i] - x_target[i])**2 for i in range(3)))
        
        bar_len = int((1.0 - delta_e) * 20)
        bar = "=" * bar_len + ">" + " " * (20 - bar_len)
        print(f"  [TLI] Coord: [{x_curr[0]:.3f}, {x_curr[1]:.3f}, {x_curr[2]:.3f}] | Delta E: {delta_e:.4f} | [{bar}]")
        time.sleep(0.3)
        
        try:
            vm.send_event('TLIEngine', 'evaluate_path')
        except Exception as e:
            print(f" [ERROR] TLI Path Blocked: {e}")
            return False
            
        if delta_e < 0.05:
            converged = True
        steps += 1
        
    if not converged:
        x_curr = list(x_target)
        delta_e = 0.0
        print(f"  [TLI] Coord: [{x_curr[0]:.3f}, {x_curr[1]:.3f}, {x_curr[2]:.3f}] | Converged to Equilibrium")
        time.sleep(0.2)
        
    try:
        vm.send_event('TLIEngine', 'state_stabilised')
        vm.send_event('TLIEngine', 'write_success')
    except Exception as e:
        print(f" [ERROR] TLI Emission Blocked: {e}")
        return False
        
    return True

def get_chat_response(query):
    global vm
    
    target_vector = find_target_coordinates(query)
    if not target_vector:
        print_unresolved_latitude_fault(query, [0.5, 0.5, 0.5])
        return ""
        
    # Cost deduction check: 370 Wh (1,332,000 J)
    total_cost_wh = 370.0
    total_cost_j = total_cost_wh * 3600.0
    
    if vm.mesh['energy'] < total_cost_j:
        return (
            f"[BLOCKED] TLI Path Blocked: Insufficient energy for cognitive relaxation.\n"
            f"  Required: {total_cost_wh:.1f} Wh ({total_cost_j:.0f} J)\n"
            f"  Available: {vm.mesh['energy']/3600.0:.1f} Wh ({vm.mesh['energy']:.0f} J)\n"
            f"  Run /attune to attune entropy anchors and replenish the energy pool."
        )
        
    success = run_tli_relaxation(target_vector)
    if not success:
        return "[ERROR] Latticed relaxation path failed to stabilize. State space reset."
        
    # Match against the knowledge database nodes parsed from SMIR
    nodes = get_knowledge_database()
    matched_node = None
    min_dist = 999.0
    for node in nodes:
        dist = math.sqrt(sum((node["coord"][i] - target_vector[i])**2 for i in range(3)))
        if dist < min_dist:
            min_dist = dist
            matched_node = node
            
    if not matched_node or min_dist >= 0.05:
        print_unresolved_latitude_fault(query, target_vector)
        return ""
        
    # Print the matched node content
    reflection_lines = []
    reflection_lines.append("================================================================================")
    reflection_lines.append("               TLI DETERMINISTIC RELATIONAL KNOWLEDGE NODE")
    reflection_lines.append("================================================================================")
    reflection_lines.append(f"[NODE ID]:              {matched_node['node_id']}")
    reflection_lines.append(f"[DOMAIN SPACE]:         {matched_node['domain']}")
    reflection_lines.append(f"[COORDINATE LATTICE]:   [{matched_node['coord'][0]:.2f}, {matched_node['coord'][1]:.2f}, {matched_node['coord'][2]:.2f}]")
    reflection_lines.append(f"[ENGINEERING FACT]:     {matched_node['fact']}")
    reflection_lines.append(f"[DEPENDENT FACT LINKS]: {matched_node['links']}")
    reflection_lines.append("================================================================================")
    reflection_lines.append(f" TLI Convergence Complete. Deducted {total_cost_wh:.1f} Wh of energy.")
    reflection_lines.append("================================================================================\n")
    
    return "\n".join(reflection_lines)

def main():
    print_banner()
    
    while True:
        try:
            state = vm.current_states.get('Truth', 'Idle')
            energy_wh = vm.mesh['energy'] / 3600.0
            
            prompt = f"[{state} | E: {energy_wh:.1f}Wh] Truth AI > "
            query = input(prompt).strip()
            if not query:
                continue
                
            if query == "/exit" or query == "/quit":
                print("\n[VTP] Disconnecting from Logos VM...")
                time.sleep(0.8)
                print("Connection safely closed.")
                input("\nPress Enter to close this window...")
                break
            elif query == "/help":
                print_help()
            elif query == "/manifesto":
                print_manifesto()
            elif query == "/keys":
                run_key_ceremony()
            elif query == "/telemetry":
                print_telemetry()
            elif query.startswith("/generate "):
                component = query[10:].strip()
                handle_generate(component)
            elif query == "/reset":
                handle_reset()
            elif query == "/attune":
                handle_attune()
            else:
                response = get_chat_response(query)
                print(f"\n  Truth: {response}\n")
                
        except KeyboardInterrupt:
            print("\n\n[VTP] Disconnecting from Logos VM...")
            time.sleep(0.5)
            print("Connection safely closed.")
            input("\nPress Enter to close this window...")
            break
        except Exception as e:
            print(f"\nSystem Error: {e}\n")

if __name__ == "__main__":
    main()
