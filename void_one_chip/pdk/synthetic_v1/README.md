# VOID Synthetic PDK (sPDK) v1

This directory bootstraps a **custom synthetic PDK** workflow for frontier stack exploration,
without tying discovery to a single foundry node from day one.

## Purpose

- convert materials + physics priors into a candidate stack,
- enforce constitutional hard-law (`no silicon`, `no copper`, L3 immutability),
- emit evidence artifacts consumable by validation and funding dossiers.

## Core Inputs

- `material_library.yaml`: candidate materials and physical properties
- `stack_manifest.yaml`: layer intent and selection targets
- `process_envelope.yaml`: thermal/defect/living-system operating envelope
- `rule_deck.yaml`: scoring and pass/fail thresholds

## Generated Outputs

Emitted by `tools/generate_synthetic_pdk.py`:

- `generated/XENALCHEMY_Synthetic_Candidate_BOM.csv`
- `generated/synthetic_candidate_manifest.json`
- `generated/synthetic_evidence_summary.json`

## Typical Flow

1. `python VoidAlchmey/tools/generate_synthetic_pdk.py`
2. `python VoidAlchmey/validation/synthetic_pdk_gate.py`
3. Optional integrated gate:
   - `set XENALCHEMY_ENABLE_SPDK=1 && python VoidAlchmey/validation/run_xenalchemy_tests.py`
