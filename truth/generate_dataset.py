import json
import random

# Seed for deterministic generation of 110 items
random.seed(42)

stewards = [
    # Humans
    "human_operator", "citizen_john", "operator_alice", "steward_bob", "prime_mover",
    # AIs
    "ai_node_alpha", "synth_agent_42", "oracle_core", "neural_grid_0", "autonomous_mesh",
    # Machines
    "digger_bot_9", "power_grid_controller", "dronenet_core", "assembler_3", "harvest_drone_7",
    # Organizations
    "consortium_core", "guild_logistics", "sovereign_assembly", "district_9_coop", "void_foundation"
]

targets = [
    "subnet_origin", "research_subnet", "sector_7_node", "agricultural_grid", "nexus_core",
    "outer_ring", "mesh_terminal", "logistics_depot", "void_core", "reactor_block"
]

licenses = ["PRIVATE", "RESTRICTED_LICENSE", "OPEN_ATTRIBUTED", "TIME_LOCKED_RELEASE"]
scopes = ["Individual", "Team", "Subnet", "Consortium", "Global"]

provenances = [
    "prov_001", "knowledge_12345", "lineage_node_7", "void_registry_88", "hash_9a3f2b",
    "ancestor_block_0", "provenance_sig_99"
]

lifetimes = [
    "12 hours", "24 hours", "30 minutes", "5 days", "50 cycles",
    "1000 seconds", "48 hours", "30 minutes", "600 seconds", "7 days", "120 cycles"
]

energy_units = ["J", "kJ", "Wh", "kWh"]
mass_units = ["mg", "g", "kg", "t"]

dataset = []

for i in range(110):
    steward = random.choice(stewards)
    target = random.choice(targets)
    license_type = random.choice(licenses)
    scope = random.choice(scopes)
    prov = random.choice(provenances)
    lifetime = random.choice(lifetimes)
    
    template_type = i % 5
    
    if template_type == 0:
        val = random.randint(10, 500)
        unit = random.choice(energy_units)
        instruction = f"Allocate {val} {unit} of power to target '{target}' for steward '{steward}' with {license_type} license, scope {scope}, provenance {prov}, and lifetime of {lifetime}."
        output = f"""intent PowerAllocation_{i} {{
    steward: "{steward}";
    target: "{target}";
    license: "{license_type}";
    scope: "{scope}";
    provenance: "{prov}";
    lifetime: {lifetime};

    require {{
        energy {val}.0 {unit};
    }}

    state Idle {{
        on request -> Active;
    }}
    state Active {{
        on complete -> Idle;
    }}
}}"""

    elif template_type == 1:
        val = random.randint(1, 1000)
        unit = random.choice(mass_units)
        instruction = f"Request routing of {val} {unit} of material supply to target '{target}' under stewardship of '{steward}' (provenance {prov}, license {license_type}, scope {scope}, lifetime {lifetime})."
        output = f"""intent MaterialSupply_{i} {{
    steward: "{steward}";
    target: "{target}";
    license: "{license_type}";
    scope: "{scope}";
    provenance: "{prov}";
    lifetime: {lifetime};

    require {{
        mass {val}.0 {unit};
    }}

    state Pending {{
        on verify -> Processing;
        on fail -> Aborted;
    }}
    state Processing {{
        on complete -> Delivered;
    }}
    state Delivered {{
    }}
    state Aborted {{
    }}
}}"""

    elif template_type == 2:
        entropy_val = random.randint(1, 10)
        instruction = f"Initialize an entropy-constrained subnet routing quest to '{target}' for steward '{steward}' with maximum wear limit {entropy_val}%, license {license_type}, scope {scope}, provenance {prov}, and lifetime {lifetime}."
        output = f"""intent SubnetRouting_{i} {{
    steward: "{steward}";
    target: "{target}";
    license: "{license_type}";
    scope: "{scope}";
    provenance: "{prov}";
    lifetime: {lifetime};

    require {{
        energy 10.0 Wh;
    }}

    constraint {{
        entropy max {entropy_val}.0;
    }}

    state Init {{
        on ping -> Synced;
    }}
    state Synced {{
        on loss -> Init;
    }}
}}"""

    elif template_type == 3:
        cycle_val = random.randint(80, 99)
        instruction = f"Deploy recycling loop at '{target}' under steward '{steward}' requiring at least {cycle_val}% efficiency, license {license_type}, scope {scope}, provenance {prov}, and lifetime {lifetime}."
        output = f"""intent RecyclingLoop_{i} {{
    steward: "{steward}";
    target: "{target}";
    license: "{license_type}";
    scope: "{scope}";
    provenance: "{prov}";
    lifetime: {lifetime};

    require {{
        mass 5.0 kg;
    }}

    constraint {{
        cycle min {cycle_val}.0 cycles;
    }}

    state Collecting {{
        on process -> Processing;
    }}
    state Processing {{
        on success -> Collecting;
        on error -> Terminated;
    }}
    state Terminated {{
    }}
}}"""

    else:
        mass_val = random.randint(5, 50)
        mass_unit = random.choice(mass_units)
        energy_val = random.randint(100, 1000)
        energy_unit = random.choice(energy_units)
        instruction = f"Provision node deployment at '{target}' for steward '{steward}' requiring {mass_val} {mass_unit} mass and {energy_val} {energy_unit} energy. Set license {license_type}, scope {scope}, provenance {prov}, and lifetime {lifetime}."
        output = f"""intent NodeDeployment_{i} {{
    steward: "{steward}";
    target: "{target}";
    license: "{license_type}";
    scope: "{scope}";
    provenance: "{prov}";
    lifetime: {lifetime};

    require {{
        mass {mass_val}.0 {mass_unit};
        energy {energy_val}.0 {energy_unit};
    }}

    state Off {{
        on boot [voltage_ok == 1] -> Booting {{
            require energy 10.0 Wh;
        }}
    }}
    state Booting {{
        on success -> Running;
        on error -> Off;
    }}
    state Running {{
        on shutdown -> Off;
    }}
}}"""

    dataset.append({
        "instruction": instruction,
        "output": output
    })

# Write jsonl dataset file
dataset_path = "logos/logos_intent_dataset.jsonl"
with open(dataset_path, "w", encoding="utf-8") as f:
    for item in dataset:
        f.write(json.dumps(item) + "\n")

print(f"Successfully generated {len(dataset)} intent prompting dataset entries in '{dataset_path}' using Logos v2.0 syntax.")
