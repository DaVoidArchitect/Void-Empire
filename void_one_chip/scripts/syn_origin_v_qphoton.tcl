#!/usr/bin/tclsh
#
# ORIGIN-V OMEGA QUANTUM-PHOTONIC: SYNTHESIS SCRIPT
# -----------------------------------------------------------------------------
# Target: 3nm GAA-FET + Silicon Photonics Process
# Tool: Synopsys Design Compiler / Cadence Genus
# ARM-Methodology: Hierarchical synthesis, multi-mode multi-corner
#

# ============================================================================
# SETUP
# ============================================================================

set DESIGN_NAME "origin_v_grand_core_qphoton"
set TOP_MODULE "origin_v_grand_core_qphoton"

# Library setup (replace with actual 3nm + photonics libraries)
set TARGET_LIBRARY "tsmc_3nm_gaa_stdcells.db tsmc_photonic_cells.db"
set LINK_LIBRARY   "* tsmc_3nm_gaa_stdcells.db tsmc_photonic_cells.db"
set SYMBOL_LIBRARY "tsmc_3nm_gaa_stdcells.sdb"

# Search paths
set search_path ". rtl rtl/include rtl/photonic rtl/stack* rtl/seu rtl/top"

# ============================================================================
# ANALYZE & ELABORATE
# ============================================================================

# Analyze all RTL files for quantum-photonic core
analyze -format sverilog -lib WORK \
    rtl/include/origin_v_params.svh \
    rtl/include/origin_v_qphoton_params.svh \
    rtl/stack01_puf/quantum_photonic_puf.sv \
    rtl/stack02_hardlaw/smf_unit.sv \
    rtl/stack03_biolatch/bio_latch.sv \
    rtl/stack03_biolatch/efuse_model.sv \
    rtl/stack07_pulse/pulse_velocity.sv \
    rtl/photonic/quantum_random_number_generator.sv \
    rtl/photonic/fractal_photonic_clock_tree.sv \
    rtl/photonic/photonic_noc_router_fractal.sv \
    rtl/photonic/quantum_key_distribution.sv \
    rtl/photonic/photonic_arithmetic_unit.sv \
    rtl/photonic/fractal_resonator_cavities.sv \
    rtl/top/origin_v_grand_core_qphoton.sv

# Elaborate design
elaborate $TOP_MODULE -lib WORK

# ============================================================================
# CONSTRAINTS
# ============================================================================

# Clock constraints (dual clock: electronic + photonic)
create_clock -period 1.0 -name sys_clk [get_ports clk]
create_clock -period 0.2 -name clk_photonic [get_ports clk_photonic_in]  # 5 GHz

set_clock_uncertainty -setup 0.05 [get_clocks sys_clk]
set_clock_uncertainty -hold 0.02 [get_clocks sys_clk]
set_clock_uncertainty -setup 0.01 [get_clocks clk_photonic]  # Tighter for photonic
set_clock_uncertainty -hold 0.005 [get_clocks clk_photonic]

set_clock_transition -max 0.1 [get_clocks sys_clk]
set_clock_transition -max 0.05 [get_clocks clk_photonic]  # Faster transition

# Input/output delays
set_input_delay -clock sys_clk -max 0.3 [all_inputs]
set_input_delay -clock clk_photonic -max 0.1 [get_ports {photon_* quantum_*}]  # Photonic inputs

set_output_delay -clock sys_clk -max 0.3 [all_outputs]
set_output_delay -clock clk_photonic -max 0.1 [get_ports {clk_photonic_out photonic_*}]

# ============================================================================
# CONSTRAINTS
# ============================================================================

# Set false paths between clock domains
set_false_path -from [get_clocks sys_clk] -to [get_clocks clk_photonic]
set_false_path -from [get_clocks clk_photonic] -to [get_clocks sys_clk]

# Async reset
set_false_path -from [get_ports rst_n] -to [all_registers]

# ============================================================================
# OPTIMIZATION
# ============================================================================

# Critical paths
set_max_delay 0.8 -from [get_ports s_axis_tdata] -to [get_ports {founder_share liquidity_pool mesh_maintenance public_net}]

# Area constraints (for photonic devices)
set_max_area 0  # Let optimizer decide

# ============================================================================
# COMPILE
# ============================================================================

compile_ultra -gate_clock -retime

# ============================================================================
# REPORTING
# ============================================================================

report_timing -max_paths 20 > reports/qphoton_timing.rpt
report_area > reports/qphoton_area.rpt
report_power > reports/qphoton_power.rpt
report_qor > reports/qphoton_qor.rpt

# ============================================================================
# WRITE OUTPUTS
# ============================================================================

write -format verilog -hierarchy -output netlist/origin_v_grand_core_qphoton.v
write -format ddc -hierarchy -output netlist/origin_v_grand_core_qphoton.ddc
write_sdf -version 3.0 netlist/origin_v_grand_core_qphoton.sdf

puts "Synthesis complete for $DESIGN_NAME"
puts "See reports/ directory for detailed results"
