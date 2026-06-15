# Void Empire

The complete, sovereign ecosystem for Project Void. Built entirely on the intent-driven, thermodynamically-constrained **Logos** programming language.

```
Void Empire/
├── logos/          # Logos compiler, VM, interpreter, and validation suites (Python & Standalone)
├── truth/          # Truth AI model parameters, dataset generators, and training scripts
├── voidos/         # Void OS core kernel/subsystems (Logos) and web app simulation
└── void_one_chip/  # Void One V2 post-silicon diamond and superatomic PDK specification
```

---

## 1. Logos Language (`logos/`)
**Logos** is a pure declarative compiler and runtime for physical reality. Procedural constructs are stripped. Logic is modeled as state machine transitions constrained by the laws of thermodynamics:
* **2-Phase Atomic Rollover**: Resource requirements (`mass`, `energy`, `entropy`, `cycle`) are evaluated in a read-only phase. If all pass, deductions commit atomically. If any fail, the transition is frozen and zero resources are deducted.
* **Post-Deduction Constraints**: Verifies operating bounds (e.g. `energy max 10 kWh`) post-transition. Violations immediately rollback allocations.
* **CLI / Execution Tools**:
  - Compiled compiler binary `logos/bin/logosc.exe` (compiles `.logos` code into JSON-based State Machine Intermediate Representation, SMIR).
  - Compiled VM CLI binary `logos/bin/logos_vm.exe` (handles interactive REPL or batch JSON event execution against compiled SMIR).
  - Python scripts `logosc.py` and `logos_vm.py` serve as reference source implementations.

## 2. Truth AI (`truth/`)
**Truth** is a local sovereign AI model served via Ollama (built from `qwen2.5-coder:1.5b`).
* Configured in `Modelfile` to directly output strict Logos v2.0 declarative code.
* Prompt-aligned to convert natural language OS capabilities into state machine transitions, guards, and transition-level resource requirements.
* Contains the training dataset generator (`generate_dataset.py`) and training set (`logos_intent_dataset.jsonl`) aligned with v2.0 specifications.

## 3. Void OS (`voidos/`)
The software layer of the Void Empire, written **entirely in Logos** (`.logos` files) and run on the Logos Virtual Machine:
* `mailbox.logos`: Secure counter mailbox implementing signature verification and anti-replay guards.
* `scheduler.logos`: Task scheduler allocating execution slots based on priority.
* `treasury.logos`: Economic resource settlement engine distributing UBI splits.
* `system.logos`: Combines all decoupled subsystem intents into a unified execution graph.
* `void-app/`: A complete, production-ready React/Vite/TypeScript web application and Express server. The backend runs transaction validations, task dispatches, and economic ledger flows by executing the compiled `logos_vm.exe` in real-time, providing true thermodynamic resource validation (`mass`, `energy`, `entropy`, `cycle`) on a sleek dark-logic telemetry dashboard.

## 4. Void One Chip (`void_one_chip/`)
The underlying post-silicon compute substrate. Built under the **VoidAlchemy** architecture v2 specification:
* **Hard Law Constitutional Constraints**: No Silicon, No Copper, Zero Clock, and No Orthogonal Geometry.
* **Stack Layers and Materials**:
  * **L0**: C60 / Aerogel Composite (outer thermal barrier + transient damping).
  * **L1**: Isotopic 12C Diamond (primary thermal steering and containment).
  * **L2**: Beryllium Aluminate Coupling (mechanical and phase continuity).
  * **L3**: Re6Se8Cl2 Superatomic Logic (topological compute + treasury-hard-law transforms).
  * **L4**: Amorphous Carbon / BiSb Dark Layer (dark-channel transport, shielding, and non-radiative coherence).
  * **L5**: Multi-Doped Graphene Interconnects (coherent interconnect spine).
* **Formal Verification**: Verified using formal properties (`validation/formal_properties.sv`) and topological checks to guarantee non-bypassable hardware enforcement of inter-subnet economic tariffs (6.18% inter-subnet tariff BPS).
