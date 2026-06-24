# VoidOS v0.1 Architecture (Phase-0 Spec)

## Purpose
Define the first complete architecture blueprint for a Void-native operating stack that can run on
today's development hosts and evolve into first-silicon deployment with Void One.

This is a **phase specification**: architecture is locked first, implementation is phased.

## Design Principles
1. **Hard-law in hardware, policy in software**.
2. **Deterministic auditability for all economic-critical paths**.
3. **Capability-first security model** (no ambient authority).
4. **Subnet sovereignty with mesh-wide interoperability**.
5. **Graceful execution under defect/thermal variability**.

## Layered Stack

### L0 — Void One Core (Hardware)
- Tariff/lease/treasury primitives and non-bypass constraints.
- Defect/thermal signals and collapse-guard surfaces.
- Attestation roots and trusted monotonic counters.

### L1 — Void HAL
- Hardware mailbox driver.
- Event-digest stream driver.
- Thermal/defect telemetry adapters.
- Deterministic timestamp/counter adapters.

### L2 — Void Supervisor Kernel
- Capability-based process/task model.
- Subnet isolation domains.
- Priority bands for economic and control services.
- Secure IPC and deterministic event journaling.

### L3 — Core System Services
- Quest Contract Service.
- Currency & Treasury Settlement Service.
- Title + Legacy Graph Service.
- Knowledge Licensing and Access Service.
- Governance/Dispute Service.

### L4 — APIs, SDKs, and Applications
- Partner APIs (enterprise and civic integrations).
- Developer SDK for quest/economy workloads.
- Operator dashboards and telemetry control plane.

## Runtime Execution Domains
- **Domain 0 (Root):** boot, attestation, capability issuance.
- **Domain 1 (Treasury-Critical):** settlement engine and non-bypass verification.
- **Domain 2 (Quest-Economy):** quest assignment, completion proofs, payouts.
- **Domain 3 (Knowledge/Legacy):** title graph and knowledge license operations.
- **Domain 4 (General App):** partner and user applications.

## Scheduler Classes (v0.1)
1. **Treasury-Critical Class** (highest integrity, deterministic latency target).
2. **Quest-Service Class** (bounded jitter, fairness constraints).
3. **Governance/Identity Class** (strict ordering and audit consistency).
4. **General Compute Class** (best-effort with policy quotas).

## Required Kernel Interfaces
- Capability creation/revocation.
- Secure mailbox I/O for treasury and attestation channels.
- Deterministic event append and hash-chaining.
- Thermal/defect interrupt surfaces with policy hooks.

## Observability and Audit
- Every treasury mutation emits an immutable event digest.
- Every quest settlement includes proof artifacts and signer lineage.
- Every title/legacy mutation references source contribution IDs.

## Security Baseline
- Least-privilege capabilities.
- Signed service manifests.
- Mandatory provenance for settlement and title operations.
- Subnet partition guards to prevent cross-domain leakage.

## Phase Delivery Plan

### Phase 0 (spec lock)
- Finalize architecture and interfaces (this document + sister specs).

### Phase 1 (executable skeleton)
- HAL + supervisor runtime on host Linux/Windows tooling.
- Minimal quest lifecycle and settlement integration.

### Phase 2 (production beta)
- Hardened service boundaries, partner APIs, and observability.

### Phase 3 (silicon-aligned runtime)
- First-silicon bring-up alignment and deployment hardening.

## Fabrication Clarification
Defect-aware design improves resilience and yield strategy, but does not remove foundry/cleanroom
requirements for physical manufacturing.
