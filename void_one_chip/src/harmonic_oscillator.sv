// (c) 2026 VOID | Confidential Tape-Out Spec
// Void One - Clockless 9-Phase Harmonic Oscillator

`timescale 1ns/1ps

module harmonic_oscillator #(
    parameter int unsigned PHASE_COUNT = 9
) (
    input  logic                   activation_i,
    input  logic                   state_reset_i,
    input  logic                   cultivation_pulse_i,
    input  logic [2:0]             chakra_band_i,
    input  logic [3:0]             cultivation_stage_i,
    input  logic [15:0]            resonance_seed_i,
    input  logic [15:0]            thermal_input_milliK_i,
    input  logic [7:0]             defect_density_i,
    output logic [PHASE_COUNT-1:0] phase_vector_o,
    output logic [3:0]             state_o,
    output logic                   phase_valid_o,
    output logic [15:0]            resonance_energy_o,
    output logic [15:0]            entropy_gain_ppm_o,
    output logic [1:0]             thermal_zone_o,
    output logic                   collapse_guard_o,
    output logic [31:0]            golden_width_um_o,
    output logic [31:0]            golden_length_um_o,
    output logic [31:0]            golden_arc_radius_um_o,
    output logic [17:0]            preferred_turn_mdeg_o,
    output logic                   right_angle_forbidden_o
);

  real GEOMETRIC_PHI = 1.6180339887;

  // Mandated non-linear progression: 3 -> 6 -> 9.
  localparam logic [3:0] STATE_INIT      = 4'd3;
  localparam logic [3:0] STATE_STABILIZE = 4'd6;
  localparam logic [3:0] STATE_RESONATE  = 4'd9;
  localparam logic [17:0] GOLDEN_TURN_MDEG = 18'd137507;
  localparam logic [1:0] THERMAL_CULTIVATION = 2'd0;
  localparam logic [1:0] THERMAL_SOVEREIGN   = 2'd1;
  localparam logic [1:0] THERMAL_COLLAPSE    = 2'd2;
  localparam int unsigned CULTIVATION_MAX_MK = 16'd2400;
  localparam int unsigned SOVEREIGN_MAX_MK   = 16'd5600;

  localparam int unsigned IDX_W = (PHASE_COUNT <= 2) ? 1 : $clog2(PHASE_COUNT);

  logic [3:0]       state_q;
  logic [IDX_W-1:0] phase_index_q;
  logic [15:0]      cultivation_depth_q;

  function automatic int wrap_index(input int raw_idx);
    if (raw_idx >= int'(PHASE_COUNT)) begin
      wrap_index = raw_idx - int'(PHASE_COUNT);
    end else begin
      wrap_index = raw_idx;
    end
  endfunction

  function automatic int active_phase_goal(
      input logic [3:0] state_v,
      input logic [2:0] chakra_band,
      input logic [3:0] cultivation_stage,
      input logic [1:0] thermal_zone,
      input logic [7:0] defect_density
  );
    int base;
    int defect_bias;
    begin
      case (state_v)
        STATE_INIT:      base = 3;
        STATE_STABILIZE: base = 6;
        default:         base = 9;
      endcase

      defect_bias = defect_density / 32;
      base = base + (chakra_band / 3) + (cultivation_stage / 4) + defect_bias;
      if (thermal_zone == THERMAL_SOVEREIGN) begin
        base = base + 1;
      end
      if (thermal_zone == THERMAL_COLLAPSE) begin
        base = base - 2;
      end
      if (base < 1) begin
        base = 1;
      end
      if (base > int'(PHASE_COUNT)) begin
        base = int'(PHASE_COUNT);
      end
      active_phase_goal = base;
    end
  endfunction

  // Clockless progression: state advances only on explicit cultivation pulses.
  always_latch begin
    if (state_reset_i) begin
      state_q             <= STATE_INIT;
      phase_index_q       <= '0;
      cultivation_depth_q <= '0;
    end else if (activation_i && cultivation_pulse_i) begin
      if (phase_index_q == (PHASE_COUNT - 1)) begin
        phase_index_q <= '0;
      end else begin
        phase_index_q <= phase_index_q + 1'b1;
      end

      cultivation_depth_q <= cultivation_depth_q + 1'b1;

      if ((chakra_band_i >= 3'd2) && (cultivation_stage_i >= 4'd2)) begin
        state_q <= STATE_STABILIZE;
      end
      if ((chakra_band_i >= 3'd4) && (cultivation_stage_i >= 4'd5) && !collapse_guard_o) begin
        state_q <= STATE_RESONATE;
      end
      if (collapse_guard_o) begin
        state_q <= STATE_STABILIZE;
      end
    end
  end

  always_comb begin
    int i;
    int active_phases;
    int thermal_bonus;
    int resonance_accum;

    phase_vector_o = '0;
    state_o        = state_q;
    phase_valid_o  = activation_i;

    if (thermal_input_milliK_i <= CULTIVATION_MAX_MK) begin
      thermal_zone_o   = THERMAL_CULTIVATION;
      collapse_guard_o = 1'b0;
      thermal_bonus    = 13;
    end else if (thermal_input_milliK_i <= SOVEREIGN_MAX_MK) begin
      thermal_zone_o   = THERMAL_SOVEREIGN;
      collapse_guard_o = 1'b0;
      thermal_bonus    = 37;
    end else begin
      thermal_zone_o   = THERMAL_COLLAPSE;
      collapse_guard_o = 1'b1;
      thermal_bonus    = -21;
    end

    active_phases = active_phase_goal(
      state_q,
      chakra_band_i,
      cultivation_stage_i,
      thermal_zone_o,
      defect_density_i
    );

    for (i = 0; i < PHASE_COUNT; i++) begin
      if (i < active_phases) begin
        phase_vector_o[wrap_index(int'(phase_index_q) + i)] = 1'b1;
      end
    end

    resonance_accum = active_phases * (state_q + chakra_band_i + cultivation_stage_i)
      + resonance_seed_i[7:0] + thermal_bonus + (defect_density_i / 4);
    if (resonance_accum < 0) begin
      resonance_accum = 0;
    end
    resonance_energy_o = activation_i ? 16'(resonance_accum) : 16'd0;

    entropy_gain_ppm_o = activation_i
      ? (16'd1000 + (active_phases * 16'd37) + (defect_density_i * 16'd9)
        + (thermal_zone_o == THERMAL_SOVEREIGN ? 16'd180 : 16'd0))
      : 16'd0;

    golden_width_um_o      = activation_i
      ? (32'd161 + (active_phases * 32'd23) + (chakra_band_i * 32'd17) + (cultivation_stage_i * 32'd11))
      : 32'd0;
    golden_length_um_o     = activation_i ? $rtoi(golden_width_um_o * GEOMETRIC_PHI) : 32'd0;
    golden_arc_radius_um_o = activation_i ? $rtoi(golden_length_um_o * GEOMETRIC_PHI) : 32'd0;

    preferred_turn_mdeg_o   = GOLDEN_TURN_MDEG;
    right_angle_forbidden_o = 1'b1;
  end

endmodule

