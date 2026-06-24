# VoidOS Syscall and Capability Model (v0.1)

## Objective
Define a stable syscall and authority model that can support Void One hard-law economics,
quest-based labor coordination, and sovereign subnet governance.

## Design Requirements
1. No ambient authority.
2. Deterministic treasury-critical behavior.
3. Explicit provenance for any state mutation that affects value, titles, or legacy.
4. Subnet-scoped isolation with controlled inter-subnet rights.

## Capability Token Structure
Each runtime capability contains:
- `cap_id`
- `subject_id` (process/service identity)
- `object_id` (resource or namespace)
- `rights_mask`
- `subnet_scope`
- `issued_at` / `expires_at`
- `policy_hash`
- `issuer_signature`

Capabilities are:
- least-privilege by default,
- delegable only when `DELEGATE` bit is present,
- revocable by root governance and authorized domain controllers.

## Syscall Namespaces

### Process and Isolation
- `proc_spawn`
- `proc_terminate`
- `proc_pause`
- `domain_attach`
- `domain_detach`

### Capability Control
- `cap_issue`
- `cap_delegate`
- `cap_revoke`
- `cap_introspect`

### Quest Economy
- `quest_create`
- `quest_claim`
- `quest_submit_proof`
- `quest_settle`
- `quest_cancel`

### Treasury and Currency
- `treasury_transfer`
- `treasury_route_inter_subnet`
- `treasury_apply_lease`
- `treasury_disburse_reward`
- `treasury_get_balance`

### Titles and Legacy
- `title_propose`
- `title_grant`
- `title_revoke`
- `legacy_append_event`
- `legacy_link_contributor`

### Knowledge Sovereignty
- `knowledge_publish`
- `knowledge_set_license`
- `knowledge_request_access`
- `knowledge_grant_access`

### Governance and Audit
- `gov_submit_policy_update`
- `gov_vote`
- `audit_append_digest`
- `audit_verify_chain`

## Determinism Rules
- Treasury and settlement syscalls must execute in deterministic priority class.
- Syscall side effects are committed only after audit digest append succeeds.
- Any failure to append digest forces transaction rollback.

## Error Model (baseline)
- `E_CAP_INVALID`
- `E_CAP_EXPIRED`
- `E_SCOPE_VIOLATION`
- `E_POLICY_BLOCKED`
- `E_PROOF_INVALID`
- `E_LEDGER_CONFLICT`
- `E_AUDIT_COMMIT_FAILED`

## Mapping to Void One Hardware
- Inter-subnet tariff and treasury path are anchored to `transaction_routing_alu.sv` hard-law behavior.
- Subnet issuance/revocation semantics align with `subnet_charter_reg.sv`.
- Thermal and defect guard signals are exposed to scheduler and service policies through HAL telemetry.

## Implementation Notes
Phase-1 runtime should implement this syscall table as API contracts first, then tighten enforcement with
kernel-native privilege boundaries in production hardening.
