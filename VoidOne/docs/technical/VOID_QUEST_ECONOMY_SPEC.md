# VOID Quest Economy Specification (v0.1)

## Purpose
Define a non-game, quest-based civil economy model where work is executed as verifiable contracts,
settled through mesh-native value rails, and recorded into contributor legacy.

## Core Thesis
- Replace static 9-5 labor blocks with mission and quest contracts.
- Reward verified impact instead of time-presence.
- Preserve contribution lineage for lifetime legacy.

## Entities
- **Citizen Node:** individual participant in the mesh economy.
- **Subnet:** policy and execution domain.
- **Quest Issuer:** entity that creates funded work contracts.
- **Quest Executor:** individual/team that claims and completes quests.
- **Verifier:** service or authority that validates completion proofs.

## Quest Lifecycle
1. **Create**
   - Issuer defines scope, proof criteria, payout rules, and deadline.
2. **Claim**
   - Executor claims quest based on capability and subnet permissions.
3. **Execute**
   - Work outputs are produced with provenance evidence.
4. **Submit Proof**
   - Completion artifacts and metrics are attached.
5. **Verify**
   - Automated/manual verification policy evaluates submission.
6. **Settle**
   - Currency payout and title/legacy updates are applied.
7. **Archive**
   - Immutable record added to legacy graph and audit chain.

## Reward and Settlement
- Gross quest value is distributed according to policy profile.
- Inter-subnet settlement events apply treasury tariff constraints.
- Intra-subnet execution can apply localized lease logic.
- Reward payout must only occur after proof verification and audit commit.

## Quest Classes
- **Civic Ops:** infrastructure and continuity tasks.
- **Research:** breakthrough and knowledge generation tasks.
- **Security & Resilience:** hardening and response tasks.
- **Builder Ops:** software/hardware execution tasks.
- **Mentorship:** title/legacy transfer and capability uplift tasks.

## Reputation and Titles
- Quest outcomes feed title eligibility.
- Failed or malicious submissions reduce trust score.
- Exceptional sustained impact unlocks sovereign title classes.

## Anti-Abuse Baseline
- No self-verification on critical payouts.
- Multi-signer verification for high-value quests.
- Cooldown and fraud controls for repetitive exploit patterns.
- Full audit trail requirement for every settlement mutation.

## Governance Hooks
- Subnet policies can modify acceptable quest classes.
- Treasury policy can tune incentive routing bands.
- Dispute protocols can suspend settlement pending review.

## Metrics
- Quest completion rate.
- Time-to-settlement.
- Fraud/dispute incidence.
- Value created per subnet.
- Cross-subnet collaboration index.

## Implementation Mapping
- Syscall surfaces: `quest_create`, `quest_claim`, `quest_submit_proof`, `quest_settle`.
- Settlement path: treasury/lease hard-law logic with audit digest coupling.
- Legacy integration: append quest impact to title and lineage graph.
