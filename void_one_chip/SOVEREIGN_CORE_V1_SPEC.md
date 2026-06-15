# VOID ONE V2 SPECIFICATION
## VOID Sovereign Data Room | Chaos/Darkness Technical Baseline

### 1. Scope and Authority
This document defines the Void One V2 execution envelope for all artifacts in:

- `VoidAlchmey/src/`
- `VoidAlchmey/validation/`
- `VoidAlchmey/pdk/`
- `VoidAlchmey/AlchemyGDSII/`
- `VoidAlchmey/VOID_Sovereign_Core_Package/`

Legacy filename is retained for repository continuity; content authority is V2.

---

### 2. Constitutional Constraints (Hard Law)

1. **No Silicon:** no silicon substrate, no CMOS substitution, no Si-photonic fallback.
2. **No Copper:** no copper interconnect, no copper via insertion, no copper package reroute.
3. **Zero Clock:** no global clock trees, no synchronous retrofit.
4. **No Orthogonal Geometry:** no right-angle routing, no orthogonal-grid remap.
5. **Chakra + Cultivation:** mandatory control metadata and runtime progression semantics.
6. **L3 Treasury Immutability:** Recursive Treasury pathways remain physically non-modifiable.

Any flow violating these constraints is non-compliant and must halt.

---

### 3. Lexicon Baseline (Mandatory)

- **Void One:** post-silicon, post-copper, bounded-chaos compute substrate.
- **Recursive Treasury:** entropy-balancing economic engine enforced in hardware.
- **Hard-Law:** immutable protocol behavior executed in gate-level logic.
- **Subnet Sovereignty:** deterministic partitioning of compute/economic domains.
- **Thermodynamic Transmutation:** bounded heat-to-performance conversion policy.
- **Dark-Channel Doctrine:** non-radiative-first transport and coherence policy.
- **Defect Sovereignty:** mapped defect utilization with strict safety bounds.

---

### 4. Material and Physics Stack (V2)

| Layer | Material Class | Physics Role | Enforcement Coupling | Verification Anchor |
|---|---|---|---|---|
| L0 | C60 / Aerogel Composite | Outer thermal barrier + transient damping | Surface safety and ingress smoothing | `validation/tcad_isotopic_diamond.py` |
| L1 | Isotopic 12C Diamond | Primary thermal steering and containment | Core gradient management and reliability | `validation/tcad_report.json` |
| L2 | Beryllium Aluminate Coupling | Mechanical and phase continuity | Interlayer coupling under transmutation loads | TCAD continuity checks |
| L3 | Re6Se8Cl2 Superatomic Logic | Topological compute + treasury-hard-law transform | Charter state control + immutable treasury pathways | `src/topological_braider.sv`, `validation/void_channel_mesh.py` |
| L4 | Amorphous Carbon / BiSb Dark Layer | Dark-channel transport, shielding, non-radiative coherence | Replaces photonic-first doctrine | `validation/void_channel_mesh.py` |
| L5 | Multi-Doped Graphene Interconnect | Coherent interconnect spine with no copper | Cross-layer signaling integrity | `pdk/XENALCHEMY_Golden_BOM.csv` |

---

### 5. Computation Doctrine

#### 5.1 Resonant + Chaotic Hybrid Compute
The compute plane combines deterministic hard-law operations and bounded chaotic transforms.
Chakra-band and cultivation-stage controls remain first-class runtime signals.

#### 5.2 Thermodynamic Transmutation Bands
V2 replaces zero-heat doctrine with bounded thermal bands:

- **Cultivation Zone:** heat improves lock quality and entropy harvest.
- **Sovereign Zone:** target band for sustained throughput.
- **Collapse Guard Zone:** protection actions engage and unstable pathways are de-rated.

Thermal behavior beyond guard rails is treated as protocol risk requiring mitigation, not performance gain.

#### 5.3 Defect Sovereignty Runtime
Defects are characterized post-fabrication and loaded as routing priors. Runtime fabric uses this map to:

- exploit stable defect channels,
- avoid collapse-prone clusters,
- harvest bounded entropy for adaptive compute.

---

### 6. Treasury ALU (Recursive Protocol Law)

`src/transaction_routing_alu.sv` enforces economic hard-law at line rate.

#### 6.1 Inter-Subnet Law
When `src_subnet_id_i != dst_subnet_id_i`:

- Cross-subnet transfer is declared.
- `INTER_SUBNET_TARIFF_BPS = 618` is applied.
- Tariff is routed to Genesis treasury path (`treasury_credit_o`).

#### 6.2 Intra-Subnet Law
When `src_subnet_id_i == dst_subnet_id_i`:

- Treasury tariff is zero.
- `INTRA_SUBNET_LEASE_BPS = 16` is applied.
- Localized activity accumulates in internal volume state.

#### 6.3 Non-Bypass Requirement
Formal properties in `validation/formal_properties.sv` enforce treasury-path coherence.

---

### 7. Subnet Charter Register (Identity + Economic Agency)

`src/subnet_charter_reg.sv` defines charter issuance and revocation:

- Asset issuance through `mint_subnet_asset(...)`
- Lease compliance through cyclical tick state
- Hard revocation (`revoke_subnet_id_o = 1`) on persistent non-payment

This path remains hardware-native governance, not external arbitration.

---

### 8. Form Factors

| Form Factor | Envelope Diameter | Compute-Radius | Sovereignty-Tier | Target Role |
|---|---:|---:|---|---|
| Sovereign_Apex | 212 mm | 106 mm | Tier-A | Macro-domain orchestration + treasury authority |
| Sovereign_Monolith | 100 mm | 50 mm | Tier-B | Regional sovereign concentration |
| Sovereign_Node | 15 mm | 7.5 mm | Tier-C | Edge execution + local charter enforcement |
| Sovereign_Seed | 100 um | 50 um | Tier-D | Embedded trust anchor |

Form-factor scaling remains tied to `1.6180339887` in `src/sovereign_core_top.sv`.

---

### 9. Validation Cross-Reference Matrix

| Objective | Source / Validation Artifact |
|---|---|
| Hard-law routing and treasury non-bypass | `validation/formal_core.sby`, `validation/formal_properties.sv` |
| Thermal gradient + transmutation band safety | `validation/tcad_isotopic_diamond.py`, `validation/tcad_report.json` |
| Dark-channel coherence and topological checks | `validation/void_channel_mesh.py`, `validation/void_channel_report.json` |
| Material hard-law compliance (no silicon/no copper) | `validation/material_compliance_check.py` |
| Integrated verdict | `validation/run_xenalchemy_tests.py`, `validation/xenalchemy_test_report.json` |

---

### 10. Strategic Constraint
All architecture, validation, and onboarding artifacts must use this V2 lexicon and constraints.
Any artifact reintroducing silicon/copper dependency or photonic-first assumptions is non-compliant.
