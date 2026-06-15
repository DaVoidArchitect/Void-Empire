# OPEN SOURCE RELEASE: PRIMAL ORIGINS SoC IP CORE

**Brand:** Primal Origins  
**Version 3.0 - Quantum-Photonic Edition**

---

## RELEASE SCOPE

This open-source release contains **ONLY** the **Quantum-Photonic Grand Core** (`origin_v_grand_core_qphoton`). The standard core (`origin_v_grand_core`) is **NOT** included in this release.

---

## INCLUDED FILES

### Core Module
- `rtl/top/origin_v_grand_core_qphoton.sv` - **Main IP Core (Quantum-Photonic Edition)**

### Required Dependencies
- `rtl/include/origin_v_params.svh` - Base parameters
- `rtl/include/origin_v_qphoton_params.svh` - Quantum-photonic parameters

### Quantum-Photonic Modules
- `rtl/stack01_puf/quantum_photonic_puf.sv` - Quantum-enhanced PUF
- `rtl/photonic/fractal_photonic_clock_tree.sv` - H-tree clock distribution
- `rtl/photonic/photonic_noc_router_fractal.sv` - Optical NoC router
- `rtl/photonic/quantum_key_distribution.sv` - QKD for storage
- `rtl/photonic/photonic_arithmetic_unit.sv` - Optical ALU
- `rtl/photonic/fractal_resonator_cavities.sv` - Photonic storage
- `rtl/photonic/quantum_random_number_generator.sv` - QRNG

### Supporting Modules (Required)
- `rtl/stack02_hardlaw/smf_unit.sv` - Hard-Law calculations
- `rtl/stack03_biolatch/bio_latch.sv` - Bio-Latch
- `rtl/stack03_biolatch/efuse_model.sv` - E-fuse model
- `rtl/stack07_pulse/pulse_velocity.sv` - Pulse currency

### Documentation
- `docs/QUANTUM_PHOTONIC_ARCHITECTURE.md` - Complete architecture guide
- `QUANTUM_PHOTONIC_RELEASE_NOTES.md` - Release notes

---

## EXCLUDED FILES

The following are **NOT** included in this release:

- `rtl/top/origin_v_grand_core.sv` - Standard core (v2.0)
- `rtl/top/origin_v_top.sv` - Top-level integration (standard version)
- Any testbenches or simulation files
- Internal development documentation

---

## USAGE

### Instantiation Example

```systemverilog
`include "rtl/include/origin_v_params.svh"
`include "rtl/include/origin_v_qphoton_params.svh"

module my_soc (
    input  wire          sys_clk,
    input  wire          clk_photonic,  // 5 GHz optical clock
    input  wire          sys_rst_n,
    // ... other signals
);

    // Quantum-Photonic Grand Core
    origin_v_grand_core_qphoton #(
        .FOUNDER_ROOT_KEY(512'hYOUR_KEY_HERE),
        .NUM_CORES(1)  // Single core instance
    ) u_origin_v_qphoton (
        .clk(sys_clk),
        .clk_photonic_in(clk_photonic),
        .rst_n(sys_rst_n),
        
        // Transaction Interface
        .s_axis_tdata(transaction_data),
        .s_axis_tvalid(transaction_valid),
        .s_axis_tready(transaction_ready),
        
        // Bio-Entropy
        .bio_entropy_in(bio_data),
        .bio_entropy_valid(bio_valid),
        .fp_sensor_active(fp_active),
        .fp_sensor_data(fp_data),
        
        // Quantum-Photonic Interfaces
        .photon_resonance_freq(ring_freq),
        .quantum_state_measure(quantum_meas),
        .photon_detected(photon_detect),
        .photon_path_0(photon_path0),
        .photon_path_1(photon_path1),
        .quantum_photon_state(qkd_photons),
        .quantum_basis_choice(qkd_bases),
        
        // Outputs
        .puf_ready(puf_rdy),
        .omega_id(chip_id),
        .founder_share(founder_amt),
        .liquidity_pool(liquidity_amt),
        .mesh_maintenance(mesh_amt),
        .public_net(public_amt),
        .hardware_storage_key(storage_key),
        .quantum_key_valid(qkd_valid),
        .quantum_key_secure(qkd_secure),
        .pulse_balance(pulse_bal),
        .governance_weight(gov_weight),
        .asset_balance(asset_bal),
        .is_founder(is_founder_flag),
        .core_authorized(core_auth),
        .mesh_active(mesh_on),
        .civilization_state(civ_state),
        .error_code(err_code),
        .clk_photonic_out(clk_distributed),
        .clk_tree_locked(clk_locked),
        .photonic_clock_skew_ps(clock_skew),
        .photonic_noc_power_level(noc_power)
    );
endmodule
```

---

## VERIFICATION STATUS

### ✅ Synthesizable SystemVerilog
- All modules compile without errors
- Parameterized for universal adoption
- Compatible with Synopsys, Cadence, Verilator

### ✅ Complete Implementation
- All 11 stacks integrated
- Quantum-photonic enhancements throughout
- Fractal architecture implemented

### ⚠️ Manufacturer Verification Required
- **Physical photonic devices** require foundry validation
- **Quantum components** require specialized manufacturing
- **Optical interfaces** need characterization

---

## MANUFACTURING REQUIREMENTS

### Process Technology
- **Electronics:** 3nm GAA-FET (or compatible)
- **Photonics:** Silicon photonics process
- **Integration:** 3D hybrid bonding

### Key Components
- Mach-Zehnder Interferometers (MZI)
- Ring resonators
- Photodetectors (Ge-on-Si)
- Optical waveguides (220nm Si)

### Foundry Compatibility
- TSMC (CoWoS with photonics)
- Intel (Silicon Photonics)
- GlobalFoundries (45RFSOI + photonics)

---

## LICENSE

**Sovereign Open Hardware License (S-OHL)**

See `LICENSE` file for full terms.

---

## SUPPORT

For technical questions:
1. Review `docs/QUANTUM_PHOTONIC_ARCHITECTURE.md`
2. Check inline code comments
3. Refer to module interfaces

---

**"Light. Quantum. Fractal. Sovereign."**

*Primal Origins SoC IP Core v3.0 - Quantum-Photonic Edition - Open Source Release*
