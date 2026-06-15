# V1 to Void One V2 Migration Guide

## Migration Objectives
- Convert legacy Sovereign Core doctrine to Void One doctrine
- Enforce no-silicon/no-copper constitutional constraints
- Replace photonic-first assumptions with dark-channel validation

## Migration Steps
1. Update constitutional docs (`THE_MANIFESTO.md`, `SOVEREIGN_CORE_V1_SPEC.md`)
2. Update BOM and process/package specifications
3. Update RTL interfaces with thermal/defect-aware outputs and guards
4. Replace validation runners and checks with Void stack equivalents
5. Regenerate lattice and mask metadata from updated generators

## Compatibility Notes
- Existing file paths are retained where practical for repository continuity.
- `SOVEREIGN_CORE_V1_SPEC.md` filename remains but contents define V2 authority.

## Verification Checklist
- [ ] `python VoidAlchmey/validation/material_compliance_check.py`
- [ ] `python VoidAlchmey/validation/tcad_isotopic_diamond.py`
- [ ] `python VoidAlchmey/validation/void_channel_mesh.py`
- [ ] `python VoidAlchmey/validation/run_xenalchemy_tests.py`
