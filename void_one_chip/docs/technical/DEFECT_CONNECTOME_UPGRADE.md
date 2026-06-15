# Void One — Defect Connectome Upgrade

## Purpose
This upgrade converts defect handling from static fault tolerance into adaptive pathway intelligence.
Defects are treated as a controlled connectome substrate that can reinforce, decay, quarantine,
and recover pathways while preserving constitutional hard-law constraints.

## Architectural Additions

### 1) Defect Graph Layer (`src/defect_connectome.sv`)
- Tracks route success/failure pulses under defect density and thermal-zone pressure.
- Emits:
  - `path_efficiency_ppm_o`
  - `anomaly_score_ppm_o`
  - `memory_retention_pct_o`
  - `quarantine_recommend_o`

### 2) Plasticity Layer (`src/plasticity_engine.sv`)
- Implements Hebbian reinforcement and anti-Hebbian decay around a homeostatic operating center.
- Emits:
  - `path_weight_ppm_o`
  - `forgetting_rate_ppm_o`
  - `convergence_window_o`

### 3) Immune/Pruning Layer (`src/immune_pruner.sv`)
- Performs anomaly-triggered quarantine recommendation and pruning confidence tracking.
- Emits:
  - `quarantine_o`
  - `precision_proxy_ppm_o`
  - `recall_proxy_ppm_o`

### 4) Top-Level Integration (`src/sovereign_core_top.sv`)
- Integrates all connectome/plasticity/immune modules.
- Uses route pulse semantics:
  - `route_success_w = activation_i && geometry_commit_i && !collapse_guard_o`
  - `route_fail_w    = activation_i && geometry_commit_i &&  collapse_guard_o`

## Validation + Evidence Pipeline

### Connectome Model
- Script: `validation/defect_connectome_mesh.py`
- Output: `validation/defect_connectome_report.json`
- KPIs:
  - `connectome_path_efficiency`
  - `plasticity_convergence_time`
  - `catastrophic_forgetting_rate`
  - `defect_memory_retention_pct`
  - `quarantine_precision`
  - `quarantine_recall`

### Statistical Yield Model
- Script: `tools/generate_yield_report.py`
- Output: `validation/yield_report.json`
- Provides raw and mission confidence bands (`p10/p50/p90`) and gate flags.
- Yield is treated probabilistically (confidence certification), not as deterministic 100% claim.

### Yield Gate
- Script: `validation/yield_gate.py`
- Output: `validation/yield_gate_report.json`
- Hard-fails if any statistical gate is not met.

### Runner Integration
- Script: `validation/run_xenalchemy_tests.py`
- Sections include `defect_connectome`, `yield_model`, and `yield_gate`.

### KPI + Readiness Integration
- KPI template: `validation/living_system_kpi_template.json`
- Auto-population: `tools/populate_living_kpis.py`
- Readiness report: `tools/generate_frontier_readiness_report.py`

## Certification Targets (Defect Connectome)
- `connectome_path_efficiency >= 0.78`
- `plasticity_convergence_time <= 12`
- `catastrophic_forgetting_rate <= 0.05`
- `defect_memory_retention_pct >= 90.0`
- `quarantine_precision >= 0.90`
- `quarantine_recall >= 0.88`

## Certification Targets (Statistical Yield)
- `raw_die_yield.p50 >= 0.89`
- `raw_die_yield.p90 >= 0.86`
- `mission_yield.p50 >= 0.98`
- `mission_yield.p90 >= 0.97`
- `yield_gate_report.pass == true`

## Reproducible Execution Sequence
From repository root:

1. `python VoidAlchmey/validation/run_xenalchemy_tests.py`
2. `python VoidAlchmey/tools/populate_living_kpis.py`
3. `python VoidAlchmey/tools/generate_frontier_readiness_report.py`

For strict verification, set required environment flags before step 1:
- `XENALCHEMY_REQUIRE_SBY=1`
- `XENALCHEMY_REQUIRE_QUTIP=1`
- `XENALCHEMY_ENABLE_SPDK=1`
