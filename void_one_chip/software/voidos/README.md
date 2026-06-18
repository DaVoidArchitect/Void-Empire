# VoidOS Scaffold

This directory contains the initial phased scaffold for VoidOS implementation.

## Structure
- `kernel/` - Supervisor kernel and domain scheduler components.
- `hal/` - Hardware abstraction layer for mailbox, telemetry, and attestation bridges.
- `services/` - Core economy/governance services (quest, treasury, titles, knowledge).
- `apis/` - Partner/developer API surfaces and SDK contracts.
- `docs/` - Implementation notes and phase execution logs.

## Phased Strategy & Status
1. **Phase-0:** Architecture/spec lock (completed in `docs/technical/`).
2. **Phase-1:** Executable skeleton on host runtime (completed natively in `/voidos/` running on the direct-to-binary compiled Logos VM).
3. **Phase-2:** Production-oriented hardening & Local Walled Garden (successfully simulated and validated: verifying unidirectional 192-byte data diode, memory auto-wiping, and `VoidMesh` peer consensus).
4. **Phase-3:** Silicon-aligned deployment runtime (integrating with RISC-V Vector Accelerator registers $v0$–$v31$ specified in Logos-HDL).

## Note
Defect-aware system architecture does not remove cleanroom/foundry requirements for physical chip
manufacturing.
