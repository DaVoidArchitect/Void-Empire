# VoidOS Phase-1 Execution Backlog (Executable Skeleton)

## Goal
Deliver an executable Phase-1 runtime skeleton that honors Void clockless/deterministic doctrine
and can run minimal treasury + quest flows on host environment.

## Epic 1 — HAL Bring-Up

### HAL-001 Mailbox Driver Skeleton
- **Description:** Implement mailbox adapter for pulse-intent submission and result receipts.
- **Acceptance:** Can submit intent envelopes and receive deterministic ACK/ERR results.
- **Evidence:** Unit test with replayed envelopes.

### HAL-002 Telemetry Adapter
- **Description:** Bridge thermal/defect signals into runtime policy surfaces.
- **Acceptance:** Scheduler consumes telemetry snapshots with stable schema.
- **Evidence:** Integration test with synthetic telemetry feeds.

### HAL-003 Deterministic Counter Adapter
- **Description:** Provide monotonic counter source for event ordering tuple.
- **Acceptance:** Counter strictly monotonic per `(domain_id, subnet_scope)` stream.
- **Evidence:** Concurrency stress test shows no duplicates/regressions.

## Epic 2 — Supervisor Kernel Skeleton

### KRN-001 Domain Scheduler
- **Description:** Implement domain classes (Root/Treasury/Quest/Legacy/General) with priority policy.
- **Acceptance:** Treasury-critical class has deterministic precedence.
- **Evidence:** Scheduling trace verification test.

### KRN-002 Capability Guard Middleware
- **Description:** Enforce capability checks before all privileged operations.
- **Acceptance:** Invalid/expired/scope-violating caps are blocked with deterministic errors.
- **Evidence:** Negative-path security tests.

### KRN-003 Event Journal + Digest Append
- **Description:** Add event append path with hash-chaining and audit coupling.
- **Acceptance:** State mutations finalize only after digest append success.
- **Evidence:** Rollback-on-audit-fail integration test.

## Epic 3 — Core Service Skeletons

### SVC-001 Treasury Minimal Flow
- **Description:** Implement `treasury_transfer` + inter/intra subnet route plumbing.
- **Acceptance:** Routes and tariffs match hard-law outcomes.
- **Evidence:** Golden-path integration tests aligned with RTL semantics.

### SVC-002 Quest Lifecycle Minimal Flow
- **Description:** Implement create/claim/submit_proof/settle happy path.
- **Acceptance:** Payout requires proof + audit commit.
- **Evidence:** End-to-end quest settlement test.

### SVC-003 Legacy Append Skeleton
- **Description:** Implement append-only contribution event write path.
- **Acceptance:** Every settled quest writes provenance-linked legacy event.
- **Evidence:** Query + chain verification test.

## Epic 4 — API Contracts

### API-001 Syscall Contract Stubs
- **Description:** Implement syscall namespace stubs from model spec.
- **Acceptance:** Contract tests pass for request/response/error shape.
- **Evidence:** API schema conformance report.

### API-002 Signed Intent Envelope
- **Description:** Define and validate signed intent format for runtime submission.
- **Acceptance:** Unsigned/tampered/replayed intents rejected deterministically.
- **Evidence:** Security + replay rejection tests.

## Phase-1 Exit Criteria
Phase-1 is complete when:
1. HAL/scheduler/capability/journal skeletons are executable.
2. Treasury + quest minimal end-to-end flows pass in deterministic replay tests.
3. All critical tests are automated and included in CI gate set.
