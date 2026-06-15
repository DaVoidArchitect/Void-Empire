# VOID Titles and Legacy Graph Specification (v0.1)

## Purpose
Define how titles are earned, how lifetime contribution lineage is recorded, and how legacy is passed
or delegated without breaking attribution integrity.

## Core Concepts
- **Title:** a verified capability/reputation marker earned through impact.
- **Legacy Graph:** immutable lineage of contributions across time.
- **Contribution Event:** atomic record linking actor, work, impact, and evidence.

## Title Lifecycle
1. **Proposal**
   - Title candidate is proposed with evidence package.
2. **Verification**
   - Evidence and policy thresholds are validated.
3. **Grant**
   - Title assigned with scope, level, and validity period.
4. **Review**
   - Scheduled/triggered review for continued compliance.
5. **Revoke/Adjust**
   - Revocation or level adjustment based on policy breach or fraud.

## Legacy Graph Node Schema
- `event_id`
- `subject_id`
- `subnet_id`
- `quest_or_work_id`
- `impact_metrics`
- `evidence_hashes`
- `title_delta`
- `timestamp`
- `signer_set`

## Legacy Operations
- `legacy_append_event`
- `legacy_link_contributor`
- `legacy_delegate_mentorship`
- `legacy_issue_inheritance_claim`

## Inheritance and Delegation
- Legacy inheritance is policy-governed and evidence-linked.
- Delegation grants mentorship/governance rights, not unearned title prestige.
- All inheritance/delegation events are graph-appended and auditable.

## Anti-Fraud Controls
- Mandatory evidence hash references.
- Multi-signer requirements for high-tier title grants.
- Revocation pathways for fabricated or manipulated claims.
- Conflict resolution policy for disputed authorship.

## Privacy and Access
- Public view: title class, high-level contribution stats.
- Restricted view: sensitive evidence, private collaboration details.
- Creator policy determines share scope subject to legal/compliance overlays.

## Implementation Mapping
- Service APIs and syscalls map to title and legacy operations.
- Quest settlement events feed title candidacy and graph updates.
- Governance services enforce policy thresholds and appeals.
