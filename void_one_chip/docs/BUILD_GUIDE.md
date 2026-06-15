# ORIGIN-V OMEGA: BUILD GUIDE

Quick start guide for building and testing the Origin-V Omega SoC.

---

## PREREQUISITES

### EDA Tools

**Simulation:**
- Synopsys VCS, Mentor Questa, or Cadence Xcelium
- Or open-source: Verilator + SystemC

**Synthesis:**
- Synopsys Design Compiler
- Or Cadence Genus
- Or open-source: Yosys (with limitations)

### Standard Cell Library

- 3nm GAA-FET standard cell library (if synthesizing)
- For simulation-only, library not required

---

## QUICK START

### 1. Clone/Download the Repository

```bash
cd origin_v_omega
```

### 2. Run Simulation

```bash
# Using provided script
make sim

# Or manually
cd scripts
./run_simulation.sh
```

### 3. Run Synthesis (if tools available)

```bash
# Setup tool environment first
source /path/to/synopsys/setup.csh

# Run synthesis
make syn
```

---

## VERIFICATION

### Running Individual Testbenches

**SMF Unit Test:**
```bash
vcs -sverilog +incdir+rtl/include \
    rtl/include/origin_v_params.svh \
    rtl/stack02_hardlaw/smf_unit.sv \
    tb/tb_smf_unit.sv \
    -o simv_smf
./simv_smf
```

**Grand Core Test:**
```bash
vcs -sverilog +incdir+rtl/include \
    rtl/**/*.sv tb/tb_grand_core.sv \
    -o simv_grand
./simv_grand
```

### Expected Results

All testbenches should show:
```
==========================================
TEST SUMMARY
==========================================
Tests Run: 5
Errors: 0
RESULT: ALL TESTS PASSED
```

---

## SYNTHESIS

### Using Synopsys Design Compiler

```bash
dc_shell -f scripts/syn_origin_v.tcl
```

### Using Cadence Genus

```bash
genus -f scripts/syn_origin_v.tcl
```

### Using Yosys (Open Source)

```bash
yosys -p "read_verilog -sv rtl/**/*.sv; synth -top origin_v_grand_core; write_verilog netlist/origin_v_synth.v"
```

**Note:** Yosys has limited SystemVerilog support. Some constructs may need modification.

---

## TROUBLESHOOTING

### Compilation Errors

**Issue:** "Cannot find origin_v_params.svh"

**Solution:** Ensure include path is set:
```bash
+incdir+rtl/include
```

**Issue:** SystemVerilog syntax errors

**Solution:** Ensure your simulator supports SystemVerilog-2012 or later.

### Simulation Errors

**Issue:** X (unknown) values in simulation

**Solution:** Ensure reset is asserted long enough:
```systemverilog
rst_n = 0;
#100;  // Wait 100 time units
rst_n = 1;
```

### Synthesis Errors

**Issue:** Timing violations

**Solution:** Review timing constraints in `constraints/origin_v_timing.sdc`. May need to adjust clock period or use multi-cycle paths.

---

## NEXT STEPS

1. Review `docs/PRODUCTION_MANUAL.md` for manufacturing integration
2. Review timing reports in `reports/` directory
3. Review test coverage reports
4. Contact for IP licensing if manufacturing

---

**For detailed specifications, see the included specification documents.**
