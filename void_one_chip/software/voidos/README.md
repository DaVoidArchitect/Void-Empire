# VoidOS Scaffold

This directory contains the initial phased scaffold for VoidOS implementation.

## Structure
- `kernel/` - Supervisor kernel and domain scheduler components.
- `hal/` - Hardware abstraction layer for mailbox, telemetry, and attestation bridges.
- `services/` - Core economy/governance services (quest, treasury, titles, knowledge).
- `apis/` - Partner/developer API surfaces and SDK contracts.
- `docs/` - Implementation notes and phase execution logs.

## Phase Strategy
1. **Phase-0:** Architecture/spec lock (completed in `docs/technical/`).
2. **Phase-1:** Executable skeleton on host runtime.
3. **Phase-2:** Production-oriented hardening.
4. **Phase-3:** Silicon-aligned deployment runtime.

## Note
Defect-aware system architecture does not remove cleanroom/foundry requirements for physical chip
manufacturing.
