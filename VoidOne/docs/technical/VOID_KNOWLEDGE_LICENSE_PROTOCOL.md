# VOID Knowledge License Protocol (v0.1)

## Purpose
Define creator-controlled knowledge sharing modes for the Void ecosystem while preserving attribution,
license clarity, and commercialization pathways.

## Knowledge Object Model
Each knowledge object includes:
- `knowledge_id`
- `creator_set`
- `origin_event_id`
- `content_hash_set`
- `license_mode`
- `access_scope`
- `policy_hash`
- `timestamp_chain_ref`

## License Modes
1. **PRIVATE**
   - Visible only to creator and explicit delegates.
2. **RESTRICTED_LICENSE**
   - Access granted by contractual/commercial terms.
3. **OPEN_ATTRIBUTED**
   - Publicly available with mandatory attribution retention.
4. **TIME_LOCKED_RELEASE**
   - Private/restricted now, auto-release at policy-defined trigger.

## Access Scopes
- Individual
- Team
- Subnet
- Partner Consortium
- Global Public

## Mandatory Attribution Rules
- Creator lineage must remain attached through all derivatives.
- Derivative objects must reference upstream `knowledge_id` chain.
- Removal or falsification of attribution is policy violation.

## Commercialization Rights
- Creator ownership remains primary unless transferred by explicit legal instrument.
- Company may hold operational/commercial license per charter policy.
- Revenue splits and royalties are policy-configured and auditable.

## Publication Workflow
1. Register knowledge object metadata.
2. Attach evidence/provenance references.
3. Select license mode and access scope.
4. Sign and commit object to audit chain.
5. Issue access grants or publish endpoints.

## Revocation and Update
- Access grants can be revoked if policy or legal conditions require.
- License updates require append-only versioning and signer proofs.
- Prior published rights remain governed by original legal conditions.

## Compliance and Safety
- Flag sensitive domains (security, dual-use, privacy-regulated data).
- Require elevated review before broad publication in flagged domains.
- Enforce export-control and jurisdiction overlays where applicable.

## Implementation Hooks
- Syscalls: `knowledge_publish`, `knowledge_set_license`, `knowledge_request_access`,
  `knowledge_grant_access`.
- Service integration with legacy graph and treasury settlement for licensed usage flows.
