# VoidOS Core & Deployment Software

This directory houses the initial phased scaffolds and implementation log files for **VoidOS**—the sovereign, declarative, pointer-free operating system of the Void Ecosystem.

## Migration to Pure Logos (`/voidos/`)

The active, compile-verified implementation of VoidOS has been successfully ported from the legacy Python scaffold to pure Logos (`.logos`) source files located in the root **[voidos/](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidos/)** directory. 

The mapping from the initial scaffold architecture to the active Logos codebase is as follows:

- **Supervisor Kernel & Scheduler** (historically `kernel/`):
  - **[system.logos](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidos/system.logos)**: Sovereign kernel top-level state machine.
  - **[scheduler.logos](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidos/scheduler.logos)**: Domain execution prioritization and slot allocations.
  - **[memory_manager.logos](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidos/memory_manager.logos)**: Physical memory page allocation and CR3 register write-protection.
- **Hardware Abstraction Layer** (historically `hal/`):
  - **[mailbox.logos](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidos/mailbox.logos)**: Monotonic pulse-intent packet exchange.
  - **[data_diode.logos](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidos/data_diode.logos)**: 192-byte data diode and hardware buffer management.
  - **[hermetic_gateway.logos](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidos/hermetic_gateway.logos)**: Cryptographic signature checks and isolated zero-copy parsing.
- **Core Subsystems & Services** (historically `services/`):
  - **[treasury.logos](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidos/treasury.logos)**: Declarative value splits and resource allocation gates.
  - **[tli_engine.logos](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidos/tli_engine.logos)**: Topological Latticed Intelligence offline oracle knowledge database.
  - **[voidmesh.logos](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidos/voidmesh.logos)**: Peer weight-slice synchronization consensus interface.
- **Developer API & Attestation Surfaces** (historically `apis/`):
  - **[session.logos](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidos/session.logos)**: Intent payload validation and secure developer sessions.

## Phased Strategy & Status

1. **Phase-0: Architecture & Spec Lock** (Completed)
   - Specs locked and cross-verified against post-silicon physics invariants.
2. **Phase-1: Host Runtime Executable Skeleton** (Completed)
   - Implemented in `/voidos/` and compiled natively using the self-hosted toolchain.
   - For execution logs and backlog items, see **[PHASE1_EXECUTION_BACKLOG.md](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/void_one_chip/software/voidos/docs/PHASE1_EXECUTION_BACKLOG.md)**.
3. **Phase-2: Hardening & Local Walled Garden** (Completed & Verified)
   - Tested and validated: unidirectional signature checking, automatic memory zeroing upon error state, and VoidMesh local synchronization.
4. **Phase-3: Silicon-Aligned Deployment Runtime** (Completed & Spec-Locked)
   - Integrated with RISC-V Vector Accelerator registers $v0$–$v31$ outlined in **[logos_hdl_spec.logos](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidos/logos_hdl_spec.logos)**.

## Note
Defect-aware system architecture does not remove cleanroom/foundry requirements for physical chip fabrication.
