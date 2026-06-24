# VOID Release Gates and CI Verification Spec (v0.1)

## Purpose
Define a release-gate model that ensures every Void release is constitutionally compliant,
clockless-safe, and evidence-linked from RTL through validation outputs.

## Release Doctrine
A release is **eligible** only when all mandatory gates pass and a signed manifest binds:
- source artifacts,
- validation reports,
- version metadata,
- release tree hash.

## Mandatory Gates

| Gate | Intent | Primary Artifact | Pass Condition |
|---|---|---|---|
| Material Compliance | enforce no-silicon/no-copper law | `validation/material_compliance_report.json` | no violations |
| Clockless Compliance | enforce no global clock and pulse-only `always_ff` | `validation/clockless_gate_report.json` | no forbidden identifiers, all sequential edges are pulse/reset compliant |
| Formal Hard-Law | prove treasury and constitutional invariants | formal logs + `validation/xenalchemy_test_report.json` | formal pass (or explicit skip policy when allowed) |
| Defect/Channel/Thermal | verify runtime physics proxies | individual reports + integrated test report | all required gates pass |
| Yield Gate | ensure statistical viability thresholds | `validation/yield_gate_report.json` | all yield gates pass |
| Synthetic PDK (optional-strict) | enforce candidate stack viability | `validation/synthetic_pdk_report.json` | pass when enabled |

## CI Pipeline Order (Recommended)
1. Lint + static checks.
2. Clockless compliance gate.
3. Material compliance gate.
4. Formal/physics/yield integrated gate (`run_xenalchemy_tests.py`).
5. Release manifest generation (`tools/generate_xenalchemy_release_manifest.py`).

## Failure Policy
- Any mandatory gate failure blocks release.
- Optional gates become mandatory when strict env flags are enabled.
- No manual override is permitted for constitutional failures (clock/material hard-law).

## Strictness Controls (Environment)
- `XENALCHEMY_REQUIRE_SBY=1` — formal gate must execute and pass.
- `XENALCHEMY_ENABLE_SPDK=1` — synthetic PDK gate enabled.
- `XENALCHEMY_REQUIRE_QUTIP=1` — strict quantum tooling requirement.
- `XENALCHEMY_REQUIRE_LIVING_POLICY=1` — strict living-policy checks.

## Evidence Bundle Requirements
Each release bundle must include at minimum:
- `validation/xenalchemy_test_report.json`
- `validation/clockless_gate_report.json`
- `validation/material_compliance_report.json`
- `validation/xenalchemy_release_manifest.json`
- `VERSION.json`

## Auditability Requirements
1. Reports must be machine-readable JSON.
2. Release manifest tree hash must be reproducible from repository content.
3. Any regenerated report that changes gate outcomes requires new release ID issuance.

## Command Baseline
Typical pre-release flow:

1. `python validation/clockless_gate.py`
2. `python validation/material_compliance_check.py`
3. `python validation/run_xenalchemy_tests.py`
4. `python tools/generate_xenalchemy_release_manifest.py`
