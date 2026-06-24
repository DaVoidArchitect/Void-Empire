# VOID Event Ordering and Deterministic Replay Spec (v0.1)

## Purpose
Define deterministic event ordering and replay behavior for VoidOS services and HAL integration,
aligned with the clockless pulse contract.

## Scope
Applies to:
- syscall-to-pulse translation,
- service-side state transitions,
- audit digest chaining,
- recovery/replay after restart/failure.

## Deterministic Ordering Model
Authoritative ordering is established by a monotonic event tuple:

`(domain_id, subnet_scope, monotonic_counter, pulse_id)`

### Ordering Rules
1. `monotonic_counter` must strictly increase per `(domain_id, subnet_scope)` stream.
2. Equal counters are invalid and must be rejected.
3. Events with missing predecessor (counter gap) enter quarantine queue until reconciled.
4. Cross-domain causality is represented via `parent_event_id` references.

## Event Record (Minimum)
- `event_id`
- `domain_id`
- `subnet_scope`
- `subject_id`
- `capability_id`
- `policy_hash`
- `monotonic_counter`
- `pulse_type`
- `intent_hash`
- `state_delta_hash`
- `digest_prev`
- `digest_curr`
- `issuer_signature`

## Commit Protocol (Two-Phase)
1. **Prepare:** validate capability, policy, anti-replay, and ordering.
2. **Apply:** stage deterministic state delta.
3. **Digest Append:** commit digest chain record.
4. **Finalize:** mark event committed and emit receipt.

If any step fails, the event is rejected and staged deltas are rolled back.

## Replay Semantics
Given identical:
- genesis state,
- ordered event stream,
- policy hashes,

the system must produce identical:
- terminal state root,
- digest chain head,
- per-event receipts.

## Recovery Behavior
On restart:
1. Load latest committed digest head and counter checkpoints.
2. Rehydrate service state from snapshot + replay log.
3. Re-run replay verification to confirm state/digest equality.
4. Resume only when replay check passes.

## Error Outcomes (Deterministic)
- `E_ORDER_GAP`
- `E_COUNTER_REPLAY`
- `E_PARENT_MISSING`
- `E_AUDIT_COMMIT_FAILED`
- `E_STATE_HASH_MISMATCH`

## Testing Requirements
1. **Idempotence test:** duplicate event rejected without mutation.
2. **Replay test:** N-run replay yields identical final hashes.
3. **Gap test:** missing-counter event quarantined and not committed.
4. **Rollback test:** forced digest append failure reverts staged state.

## Mapping to Existing Specs
- Syscall/capability surfaces: `docs/technical/VOID_SYSCALL_AND_CAPABILITY_MODEL.md`
- Architecture layering: `docs/technical/VOID_OS_V0_1_ARCHITECTURE.md`
- Pulse doctrine: `docs/technical/VOID_CLOCKLESS_PULSE_CONTRACT.md`
