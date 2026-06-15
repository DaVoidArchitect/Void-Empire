# Void Empire

The complete, sovereign ecosystem for Project Void. Built entirely on the intent-driven, thermodynamically-constrained **Logos** programming language.

```
Void Empire/
├── logos/          # Logos compiler, VM, interpreter, and validation suites (Python)
├── truth/          # Truth AI model parameters, dataset generators, and training scripts
├── voidos/         # Void OS core kernel/subsystems (Logos) and Closed Beta simulation
└── void_one_chip/  # Void One 11-Stack Photonic SoC silicon architecture and RTL core
```

---

## 1. Logos Language (`logos/`)
**Logos** is a pure declarative compiler and runtime for physical reality. Procedural constructs are stripped. Logic is modeled as state machine transitions constrained by the laws of thermodynamics:
* **2-Phase Atomic Rollover**: Resource requirements (`mass`, `energy`, `entropy`, `cycle`) are evaluated in a read-only phase. If all pass, deductions commit atomically. If any fail, the transition is frozen and zero resources are deducted.
* **Post-Deduction Constraints**: Verifies operating bounds (e.g. `energy max 10 kWh`) post-transition. Violations immediately rollback allocations.
* **CLI Tools**: Standalone compiler (`logosc.py`) and VM CLI/REPL (`logos_vm.py`).

## 2. Truth AI (`truth/`)
**Truth** is a local sovereign AI model served via Ollama (built from `qwen2.5-coder:1.5b`).
* Configured in `Modelfile` to directly output strict Logos v2.0 declarative code.
* Prompt-aligned to convert natural language OS capabilities into state machine transitions, guards, and transition-level resource requirements.
* Contains the training dataset generator (`generate_dataset.py`) and training set (`logos_intent_dataset.jsonl`) aligned with v2.0 specifications.

## 3. Void OS (`voidos/`)
The software layer of the Void Empire, written **entirely in Logos** (`.logos` files):
* `mailbox.logos`: Secure counter mailbox implementing signature verification and anti-replay guards.
* `scheduler.logos`: Task scheduler allocating execution slots based on priority.
* `treasury.logos`: Economic resource settlement engine distributing UBI splits.
* `system.logos`: Combines all decoupled subsystem intents into a unified execution graph.
* `closed_beta.py`: The production-ready simulator processing concurrent event streams for **250 active beta citizens** against the unified state machine, verifying stable thermodynamic resource management.

## 4. Void One Chip (`void_one_chip/`)
The underlying silicon layer. An 11-stack fractal photonic SoC architecture including:
* **Fractal Photonic Clock Tree** and **Photonic Arithmetic Unit** Verilog cores.
* **Stack 02 (Hardlaw)**: Hardware-level enforcement of compiler bounds.
* **Stack 03 (Biolatch)** and **Stack 06 (Mesh)** silicon designs.
