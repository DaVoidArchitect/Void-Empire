# VOID Currency and Treasury Protocol Specification (v0.1)

## Purpose
Define the mesh-native currency flow, treasury controls, and settlement invariants for Void economy
operations tied to Void One hard-law primitives.

## Protocol Goals
1. Deterministic settlement for mission-critical value transfers.
2. Transparent treasury routing for inter-subnet value movement.
3. Policy-tunable incentives at software layer without violating hardware hard-law.
4. Audit-first accounting for every value mutation.

## Currency Model
- Currency is represented as a protocol accounting unit in settlement services.
- Unit naming, denominations, and monetary policy are governance-configured at software layer.
- Treasury-critical routing paths must respect hardware non-bypass constraints.

## Settlement Modes

### Inter-Subnet Settlement
- Trigger condition: source and destination subnets differ.
- Treasury tariff pathway is applied per hard-law profile.
- Tariff destination and accounting receipts are immutable once committed.

### Intra-Subnet Settlement
- Trigger condition: source and destination subnets match.
- Lease/local policy basis applies where configured.
- Internal volume and local treasury signals update per policy profile.

## Treasury Roles
- **Genesis Treasury:** constitutional reserve and continuity anchor.
- **Subnet Treasury:** local execution reserve and incentive allocator.
- **Quest Reward Pool:** payout source for verified contract completion.
- **Stability Pool:** governance-controlled risk and emergency reserve.

## Invariants
1. No settlement commit without audit digest append.
2. No treasury bypass for inter-subnet transfers.
3. No negative balance transitions.
4. No unauthorized mint-like operation outside policy-approved pathways.

## Policy Surface (software-managed)
- Tariff distribution split (global/subnet/civic pools).
- Reward disbursement weights by quest class.
- Treasury reserve targets and replenishment rules.
- Risk flags and temporary settlement throttles.

## Observability
- Settlement event ID
- Subnet source/destination
- Gross value, tariff/lease values, net payout
- Policy hash and signer lineage
- Digest-chain reference

## Abuse Resistance
- Rate limits per subject and subnet scope.
- Multi-party approval for high-value disbursements.
- Anomaly triggers that route events into dispute workflow.

## Hardware/Software Boundary
- Hardware enforces hard-law pathways and deterministic constraints.
- Software defines adaptive economic policy and distribution logic.

## Foundry/Fabrication Clarification
Economic protocol and defect-aware operation do not remove foundry process requirements for physical
manufacturing; cleanroom-capable fabrication remains mandatory for wafer production.
