#
# ORIGIN-V OMEGA: TIMING CONSTRAINTS
# -----------------------------------------------------------------------------
# SDC Format (Synopsys Design Constraints)
# Target: 3nm GAA-FET Process, 1GHz operation
#

# ============================================================================
# CLOCK DEFINITIONS
# ============================================================================

# Main system clock (1GHz = 1.0ns period)
create_clock -period 1.0 -name sys_clk [get_ports clk]
create_clock -period 1.0 -name clk [get_ports clk]

# Clock uncertainty (setup/hold margins for 3nm process)
set_clock_uncertainty -setup 0.05 [get_clocks sys_clk]
set_clock_uncertainty -hold 0.02 [get_clocks sys_clk]

# Clock transition time
set_clock_transition -max 0.1 [get_clocks sys_clk]

# Clock latency
set_clock_latency -source -max 0.2 [get_clocks sys_clk]
set_clock_latency -max 0.1 [get_clocks sys_clk]

# ============================================================================
# INPUT DELAYS
# ============================================================================

set_input_delay -clock sys_clk -max 0.3 [get_ports s_axis_tdata*]
set_input_delay -clock sys_clk -min 0.1 [get_ports s_axis_tdata*]

set_input_delay -clock sys_clk -max 0.3 [get_ports s_axis_tvalid]
set_input_delay -clock sys_clk -min 0.1 [get_ports s_axis_tvalid]

set_input_delay -clock sys_clk -max 0.3 [get_ports bio_entropy_in*]
set_input_delay -clock sys_clk -min 0.1 [get_ports bio_entropy_in*]

set_input_delay -clock sys_clk -max 0.3 [get_ports bio_entropy_valid]
set_input_delay -clock sys_clk -min 0.1 [get_ports bio_entropy_valid]

# ============================================================================
# OUTPUT DELAYS
# ============================================================================

set_output_delay -clock sys_clk -max 0.3 [get_ports s_axis_tready]
set_output_delay -clock sys_clk -min 0.1 [get_ports s_axis_tready]

set_output_delay -clock sys_clk -max 0.3 [get_ports founder_share*]
set_output_delay -clock sys_clk -min 0.1 [get_ports founder_share*]

set_output_delay -clock sys_clk -max 0.3 [get_ports liquidity_pool*]
set_output_delay -clock sys_clk -min 0.1 [get_ports liquidity_pool*]

set_output_delay -clock sys_clk -max 0.3 [get_ports mesh_maintenance*]
set_output_delay -clock sys_clk -min 0.1 [get_ports mesh_maintenance*]

set_output_delay -clock sys_clk -max 0.3 [get_ports public_net*]
set_output_delay -clock sys_clk -min 0.1 [get_ports public_net*]

set_output_delay -clock sys_clk -max 0.3 [get_ports hardware_storage_key*]
set_output_delay -clock sys_clk -min 0.1 [get_ports hardware_storage_key*]

set_output_delay -clock sys_clk -max 0.3 [get_ports governance_weight*]
set_output_delay -clock sys_clk -min 0.1 [get_ports governance_weight*]

set_output_delay -clock sys_clk -max 0.3 [get_ports civilization_state*]
set_output_delay -clock sys_clk -min 0.1 [get_ports civilization_state*]

# ============================================================================
# FALSE PATHS
# ============================================================================

# Reset is asynchronous
set_false_path -from [get_ports rst_n]

# PUF capture is one-time initialization
set_false_path -to [get_pins */u_sram_puf/puf_ready]
set_false_path -to [get_pins */u_sram_puf/omega_id*]

# ============================================================================
# MULTI-CYCLE PATHS
# ============================================================================

# Pulse velocity accumulator can take multiple cycles
set_multicycle_path -setup 2 -from [get_pins */u_pulse_velocity/*] -to [get_pins */governance_weight_reg*]

# Bio-latch mortality counter (very slow - 30 days)
set_multicycle_path -setup -from [get_pins */u_bio_latch/mortality_counter*] 1000000

# ============================================================================
# MAX DELAY CONSTRAINTS
# ============================================================================

# Critical path: Transaction to output (must be < 1 cycle)
set_max_delay -from [get_ports s_axis_tdata*] -to [get_ports founder_share*] 0.8
set_max_delay -from [get_ports s_axis_tdata*] -to [get_ports public_net*] 0.8

# ============================================================================
# DESIGN RULES
# ============================================================================

set_max_capacitance 0.5 [all_inputs]
set_max_transition 0.2 [all_outputs]
set_max_fanout 50 [all_inputs]

# ============================================================================
# EXCEPTIONS
# ============================================================================

# Allow slower paths for non-critical signals
set_max_delay 5.0 -from [get_pins */pulse_balance*] -to [get_pins */governance_weight*]
