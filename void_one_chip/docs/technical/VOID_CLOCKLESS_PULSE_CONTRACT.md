# VOID Clockless Pulse Contract (v0.1)

## Purpose
Define the stack-wide execution contract for a **clockless Void architecture** where state transitions are
driven only by explicit, authenticated pulses.

This specification is a constitutional extension of Void One RTL behavior and applies to:
- `src/*.sv` (hardware hard-law and pulse-driven state progression)
- `software/voidos/*` (HAL, supervisor, services)
- `validation/*` (formal/determinism/replay evidence)

## Constitutional Invariants
1. **No global clock domain:** no free-running `clk/clock` signal is allowed.
2. **Pulse-only mutation:** all authoritative state mutation must be bound to explicit domain pulses.
3. **Deterministic ordering:** mutation order is defined by pulse ordering, not wall-clock time.
4. **Audit-coupled commit:** economic/governance/title mutations commit only after digest append success.
5. **Replay safety:** pulses are nonce/counter-protected and deduplicated.

## Canonical Pulse Types
- `geometry_commit_i` — geometry and topology commits.
- `routing_pulse_i` — transaction routing/settlement transitions.
- `ledger_pulse_i` — charter/identity/lease transitions.
- `update_pulse_i` — adaptive connectome/plasticity/immune transitions.

`state_reset_i` remains a dedicated reset surface and is not treated as a business-domain pulse.

## Pulse Envelope (Cross-Layer)
Every pulse emitted above hardware should carry (directly or derivably):
- `pulse_id`
- `domain_id`
- `subject_id`
- `capability_id` / `rights_mask`
- `policy_hash`
- `nonce_or_counter`
- `parent_event_id` (optional but recommended)
- `issuer_signature`

## Runtime Semantics
1. Intent arrives (`syscall/API`).
2. Capability + policy + anti-replay checks pass.
3. HAL emits exactly one domain pulse.
4. Domain state machine evaluates pulse deterministically.
5. Mutation is staged.
6. Digest append succeeds.
7. Mutation becomes authoritative; receipt/proof is emitted.

If step 6 fails, mutation must rollback and return a deterministic error outcome.

## Security Requirements
- No ambient authority.
- Pulse emission must be capability-gated.
- Replayed pulse IDs must be rejected deterministically.
- High-value actions require multi-signer policy when configured.

## Verification Anchors
- RTL/formal properties: no-bypass + constitutional hard-law assertions.
- Validation gate: `validation/clockless_gate.py` (no global clock identifiers, pulse-only `always_ff` edges).
- Integration tests: deterministic replay across identical pulse streams.

## Non-Goals
- This document does not define economic policy tuning weights.
- This document does not replace material/fabrication constraints.
