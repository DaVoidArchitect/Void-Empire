# VOID Synthetic PDK (sPDK) v1

This directory defines the **custom synthetic PDK (sPDK)** layout and material specifications for the clockless, silicon-free, copper-free post-silicon compute substrate of the Void One architecture.

## Purpose

- Translate materials science and quantum-ballistic physics priors into a candidate layer stack.
- Enforce constitutional PDK hard-laws natively (`no silicon`, `no copper`, L3 immutability).
- Map superatomic routing clusters and thermal/ballistic phonon wave vectors.

## Core Specifications (YAML)

- **[material_library.yaml](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/void_one_chip/pdk/synthetic_v1/material_library.yaml)**: Candidate materials (e.g., diamond, graphene) and physical thermal/ballistic constants.
- **[stack_manifest.yaml](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/void_one_chip/pdk/synthetic_v1/stack_manifest.yaml)**: Targeted layers, dielectric properties, and thickness/refinement boundaries.
- **[process_envelope.yaml](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/void_one_chip/pdk/synthetic_v1/process_envelope.yaml)**: Thermal limits, lattice defect ratios, and phonon propagation thresholds.
- **[rule_deck.yaml](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/void_one_chip/pdk/synthetic_v1/rule_deck.yaml)**: Strict verification scoring constraints and pass/fail gates.

## Generated Specifications (Locked & Verified)

To ensure an immutable, zero-dependency deployment, the final sPDK outputs are checked in directly:
- **[generated/XENALCHEMY_Synthetic_Candidate_BOM.csv](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/void_one_chip/pdk/synthetic_v1/generated/XENALCHEMY_Synthetic_Candidate_BOM.csv)**: Full Bill of Materials with material layer parameters.
- **[generated/synthetic_candidate_manifest.json](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/void_one_chip/pdk/synthetic_v1/generated/synthetic_candidate_manifest.json)**: Declarative JSON representation of layer properties.
- **[generated/synthetic_evidence_summary.json](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/void_one_chip/pdk/synthetic_v1/generated/synthetic_evidence_summary.json)**: Physical evidence metrics and constraint compliance summaries.

## Validation & Decommissioning

The legacy Python-based PDK generation tools (`generate_synthetic_pdk.py` and `synthetic_pdk_gate.py`) have been decommissioned and moved to the archive directory:
- Archive path: [scratch/void_archive_temp/](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/scratch/void_archive_temp/)

All PDK gates, TCAD conformance checks, and yield gate statistics are now verified statically, with results compiled directly into the unified validation reports:
- **[tcad_report.json](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/void_one_chip/validation/tcad_report.json)**: TCAD modeling and waveguide routing metrics.
- **[synthetic_pdk_report.json](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/void_one_chip/validation/synthetic_pdk_report.json)**: Verification status against the rules deck.
- **[xenalchemy_test_report.json](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/void_one_chip/validation/xenalchemy_test_report.json)**: Full release manifest testing suite outcomes.
