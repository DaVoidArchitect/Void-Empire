# Void Empire

The complete, sovereign ecosystem for Project Void. Built entirely on the intent-driven, thermodynamically-constrained **Logos** programming language.

```
Void Empire/
├── logos/          # Logos self-hosting direct-to-binary AOT compiler, VTP edge bridge, and verification suites
├── truth/          # Truth AI model parameters, dataset generators, and training scripts
├── voidos/         # Void OS core kernel/subsystems (Logos) and web app simulation
└── void_one_chip/  # Void One V2 post-silicon diamond and superatomic PDK specification
```

---

## 1. Logos Language & Sovereignty Compiler (`logos/`)
**Logos** is a pure declarative language and compilation pipeline for physical reality. Procedural constructs are stripped; logic is modeled as state machine transitions constrained by the laws of thermodynamics:
* **2-Phase Atomic Rollover**: Resource requirements (`mass`, `energy`, `entropy`, `cycle`) are evaluated in a read-only phase. If all pass, deductions commit atomically. If any fail, a hardware-level register rollback is triggered (using x86_64 registers `r12`–`r15`), costing zero execution resources.
* **Sovereign Tax Integration**: A 6.18% platform routing fee is structurally hardcoded into node paths using fixed-point math executed directly in the binary layout, requiring zero runtime software logic.
* **Direct-to-Binary AOT Compiler**:
  - The Python seed compiler (`compiler.py`, `logosc.py`, `bootstrap_aot.py`) and VM runtime (`logos_vm.exe`) have been permanently purged.
  - The compiler runs as a freestanding native binary (`logos/bin/stage1_compiler.exe` / `logosc.exe`).
  - An in-memory Byte-Buffer Emission Pipeline builds PE execution blocks byte-by-byte before streaming to disk, bypassing intermediate text files or external linkers.
  - Compiles directly to the custom **Void Matrix Format (.vmf)** if the output target ends with `.vmf`.
* **Void Matrix Format (.vmf) Specifications**:
  - **Offset 0x00**: System Entropy Anchor (4 Bytes - Hardcoded cryptographic initialization vector: `0xF00DBABE`).
  - **Offset 0x04**: Platform Fee Geometry (8 Bytes - Spatial routing map coefficient set to exactly `1.0618`).
  - **Offset 0x0C**: Quantum Bounds Register (16 Bytes - Allocating upper limit thresholds of `1e12` for Mass, Energy, Entropy, and Cycles).
  - **Offset 0x1C**: Node Coordinate Index (`.node` - Packed multi-dimensional matrix coordinate arrays).
  - **Offset 0x50+**: Transition Lattices (`.matrix` - Raw hexadecimal opcode vectors defining spatial state shifts starting with `0x49 0x89 0xC6` for register backups).
* **Self-Hosting Bootstrap Loop**:
  - Stage 0 (`stage0_compiler.exe`) compiles `compiler.logos` into Stage 1 (`stage1_compiler.exe`).
  - A cryptographic SHA-256 hash comparison verifies a 100% bit-for-bit identical match (`fdfc39b1bc65acc59f162677fdb58d550e40081c4fb1e7be2f18d35278a8cd2a`).
  - Audited using `verify_binary_sovereignty.py`.

## 2. Decentralized Edge Bridge (`logos/` & VTP)
A zero-dependency secure bridge connecting legacy systems (Windows/Linux) to the sovereign inner garden:
* **Void Tunnel Protocol (VTP)**: A rigid, cryptographic binary transport stream.
* **VTP Edge Client** (`logos/bin/vtp_client.exe` / `vtp_client.c`): A completely hollow client with no local ecosystem logic or filesystem/memory privileges. It packages user inputs into fixed 64-byte "Intent Packets" and transmits them.
* **VTP Server** (`logos/bin/vtp_server.exe` / `vtp_server.c`): Receives Intent Packets, processes transactions within `/voidos/` limits, extracts the 6.18% platform fee, and streams back a read-only 128-byte cryptographic "State Reflection Packet" delta.
* **Isolation Guarantee**: Malware compromise on legacy host automatically drops the reflection sync vector, entirely insulating the inner `/voidos/` domain.

## 3. Truth AI (`truth/`)
**Truth** is a 100% sovereign, self-contained AI model engine running natively (`truth/truth.py`). We reject all external dependencies on Ollama, parameter wrappers, or third-party inference runners.
* Trains a **Naive Bayes Classifier** from absolute scratch on `logos_intent_dataset.jsonl` to categorize prompts into target intent classes.
* Employs a regex-based slot parser and semantic template filler to dynamically generate strict, syntactically-valid Logos v2.0 declarative code.
* Listens as a local HTTP microservice at `http://localhost:11434/api/generate` mimicking Ollama's API signature for seamless drop-in integration with the OS build scripts (`build_voidos_with_truth.py`).
* Contains the training dataset generator (`generate_dataset.py`) and training set (`logos_intent_dataset.jsonl`) aligned with v2.0 specifications.

## 4. Void OS (`voidos/`)
The software layer of the Void Empire, written **entirely in Logos** (`.logos` files) and run on the Logos native execution pipeline:
* `mailbox.logos`: Secure counter mailbox implementing signature verification and anti-replay guards.
* `scheduler.logos`: Task scheduler allocating execution slots based on priority.
* `treasury.logos`: Economic resource settlement engine distributing UBI splits.
* `system.logos`: Combines all decoupled subsystem intents into a unified execution graph.
* `void-app/`: A complete, production-ready React/Vite/TypeScript web application and Express server. The backend runs transaction validations, task dispatches, and economic ledger flows on a sleek dark-logic telemetry dashboard.

## 5. Void One Chip (`void_one_chip/`)
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