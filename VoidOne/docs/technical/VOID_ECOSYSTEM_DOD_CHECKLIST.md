# VOID Ecosystem Definition-of-Done (DoD) Checklist

Use this checklist to declare complete production readiness for the full
atoms → OS → services → metaverse ecosystem.

## A. Constitutional & Material Law
- [ ] No-silicon/no-copper hard-law passes in material compliance gate.
- [ ] Clockless pulse law passes in clockless compliance gate.
- [ ] Formal hard-law proofs pass in strict mode (no skipped formal).

## B. RTL / Core Assurance
- [ ] Integrated validation suite reports `overall_pass: true`.
- [ ] Yield model and yield gate pass mission and raw thresholds.
- [ ] Frontier readiness report certifies `FRONTIER_V2_CERTIFIED`.

## C. Runtime (VoidOS) Readiness
- [ ] HAL mailbox + telemetry adapters implemented and tested.
- [ ] Supervisor domain scheduler implemented with deterministic ordering.
- [ ] Capability issue/delegate/revoke enforcement active.
- [ ] Deterministic event journal implemented with replay checks.

## D. Services Readiness
- [ ] Treasury settlement service wired to hard-law boundaries.
- [ ] Quest lifecycle service supports create/claim/proof/settle flow.
- [ ] Title/legacy service writes immutable provenance-linked records.
- [ ] Knowledge licensing service enforces scoped access policies.
- [ ] Governance/audit services enforce digest-coupled commits.

## E. API / Platform / Metaverse Readiness
- [ ] API gateway and SDK contracts are versioned and tested.
- [ ] Metaverse intent adapter emits signed, policy-bound intents only.
- [ ] No direct authoritative state mutation outside governed services.
- [ ] Operator control plane exposes SLO, audit, and incident views.

## F. Security & Supply Chain
- [ ] Signed service manifests and policy bundles enforced.
- [ ] SBOM and build provenance generated for each release.
- [ ] Key lifecycle (rotation/revocation/recovery) runbooks validated.
- [ ] Pen-test / security review findings remediated.

## G. Reliability & Operations
- [ ] Load/performance targets met for critical paths.
- [ ] Fault-injection and recovery drills pass acceptance criteria.
- [ ] DR/backups tested and recovery objectives met.
- [ ] On-call, incident response, and escalation procedures rehearsed.

## H. Compliance & Deployment
- [ ] Evidence package complete and reproducible from clean environment.
- [ ] Strict release gates pass via `tools/run_strict_release_gates.py`.
- [ ] Release manifest generated and traceable to source tree hash.
- [ ] Pilot deployment completes with deterministic replay/audit integrity.

## Exit Rule
Production-ready declaration is valid only when **all sections A–H** are checked complete
with corresponding machine-readable artifacts and signed release evidence.
