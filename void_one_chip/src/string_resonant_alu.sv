// (c) 2026 VOID | Confidential Tape-Out Spec
// Void One - Clockless String Resonant ALU

`timescale 1ns/1ps

module string_resonant_alu #(
    parameter int unsigned DATA_W = 32,
    parameter int unsigned HARMONIC_PHASES = 9
) (
    input  logic                        activation_i,
    input  logic                        state_reset_i,
    input  logic                        compute_pulse_i,
    input  logic [2:0]                  chakra_band_i,
    input  logic [3:0]                  cultivation_stage_i,
    input  logic [15:0]                 thermal_input_milliK_i,
    input  logic [7:0]                  defect_density_i,
    input  logic [HARMONIC_PHASES-1:0]  harmonic_phase_vector_i,
    input  logic [15:0]                 resonance_amplitude_i,
    input  logic [DATA_W-1:0]           a_i,
    input  logic [DATA_W-1:0]           b_i,
    input  logic [DATA_W-1:0]           c_i,
    input  logic [1:0]                  op_i,
    output logic                        harmonic_lock_o,
    output logic [DATA_W-1:0]           p_o,
    output logic [DATA_W-1:0]           q_o,
    output logic [DATA_W-1:0]           r_o,
    output logic [DATA_W-1:0]           result_o,
    output logic [15:0]                 thermal_delta_milliK_o,
    output logic [15:0]                 entropy_gain_ppm_o,
    output logic [1:0]                  thermal_zone_o,
    output logic                        collapse_guard_o,
    output logic                        no_silicon_hardlaw_o,
    output logic                        no_copper_hardlaw_o,
    output logic                        dark_channel_required_o,
    output logic [31:0]                 golden_width_um_o,
    output logic [31:0]                 golden_length_um_o,
    output logic [17:0]                 preferred_turn_mdeg_o,
    output logic                        right_angle_forbidden_o
);

  localparam int unsigned PHI_NUM = 32'd1_618_034;
  localparam int unsigned PHI_DEN = 32'd1_000_000;
  localparam logic [17:0] GOLDEN_TURN_MDEG = 18'd137507;
  localparam logic [1:0] THERMAL_CULTIVATION = 2'd0;
  localparam logic [1:0] THERMAL_SOVEREIGN   = 2'd1;
  localparam logic [1:0] THERMAL_COLLAPSE    = 2'd2;
  localparam int unsigned CULTIVATION_MAX_MK = 16'd2400;
  localparam int unsigned SOVEREIGN_MAX_MK   = 16'd5600;
  localparam int unsigned THERMAL_TARGET_MK  = 16'd3600;

  logic [$clog2(HARMONIC_PHASES+1)-1:0] active_phase_count;
  logic [DATA_W-1:0] resonant_mask;
  logic [DATA_W-1:0] defect_mask;
  logic              fredkin_ctrl;
  logic [15:0]       lock_threshold_q;

  function automatic logic [31:0] mul_phi(input logic [31:0] base);
    logic [63:0] scaled;
    begin
      scaled = base * PHI_NUM;
      mul_phi = scaled / PHI_DEN;
    end
  endfunction

  function automatic logic [DATA_W-1:0] build_resonant_mask(
      input logic [HARMONIC_PHASES-1:0] phases,
      input logic [15:0] amp
  );
    logic [DATA_W-1:0] mask;
    int idx;
    begin
      mask = '0;
      for (idx = 0; idx < DATA_W; idx++) begin
        mask[idx] = phases[idx % HARMONIC_PHASES] ^ amp[idx % 16];
      end
      build_resonant_mask = mask;
    end
  endfunction

  // Clockless transitions occur only on explicit compute pulses.
  always_ff @(posedge compute_pulse_i or posedge state_reset_i) begin
    if (state_reset_i) begin
      lock_threshold_q <= 16'd3;
    end else if (activation_i) begin
      lock_threshold_q <= 16'(
        3 + (chakra_band_i / 2) + (cultivation_stage_i / 3) + (defect_density_i / 64)
      );
    end
  end

  always_comb begin
    if (thermal_input_milliK_i <= CULTIVATION_MAX_MK) begin
      thermal_zone_o   = THERMAL_CULTIVATION;
      collapse_guard_o = 1'b0;
    end else if (thermal_input_milliK_i <= SOVEREIGN_MAX_MK) begin
      thermal_zone_o   = THERMAL_SOVEREIGN;
      collapse_guard_o = 1'b0;
    end else begin
      thermal_zone_o   = THERMAL_COLLAPSE;
      collapse_guard_o = 1'b1;
    end

    active_phase_count = $countones(harmonic_phase_vector_i);
    resonant_mask      = build_resonant_mask(harmonic_phase_vector_i, resonance_amplitude_i);
    defect_mask        = {DATA_W{defect_density_i[0]}} ^ {DATA_W{defect_density_i[3]}};

    harmonic_lock_o    = activation_i && compute_pulse_i
      && !collapse_guard_o
      && (active_phase_count >= lock_threshold_q[$clog2(HARMONIC_PHASES+1)-1:0]);
  end

  always_comb begin
    p_o = a_i;
    q_o = b_i;
    r_o = c_i;

    fredkin_ctrl = a_i[0] ^ resonant_mask[0] ^ chakra_band_i[0] ^ cultivation_stage_i[0];

    if (harmonic_lock_o) begin
      unique case (op_i)
        2'b00: begin
          p_o = a_i;
          q_o = b_i;
          r_o = c_i ^ (a_i & b_i);
        end
        2'b01: begin
          p_o = a_i;
          q_o = fredkin_ctrl ? c_i : b_i;
          r_o = fredkin_ctrl ? b_i : c_i;
        end
        2'b10: begin
          p_o = a_i ^ {DATA_W{chakra_band_i[1]}};
          q_o = b_i ^ {DATA_W{cultivation_stage_i[1]}};
          r_o = a_i ^ b_i ^ c_i ^ resonant_mask ^ defect_mask;
        end
        default: begin
          p_o = a_i;
          q_o = b_i;
          r_o = c_i;
        end
      endcase
    end

    result_o = (p_o ^ q_o ^ r_o) ^ (collapse_guard_o ? {DATA_W{1'b0}} : defect_mask);
  end

  always_comb begin
    logic [31:0] width_seed;
    width_seed            = 161 + (int'(active_phase_count) * 23)
      + (int'(chakra_band_i) * 17) + (int'(cultivation_stage_i) * 11);
    golden_width_um_o     = activation_i ? width_seed : 32'd0;
    golden_length_um_o    = activation_i ? mul_phi(golden_width_um_o) : 32'd0;
    preferred_turn_mdeg_o = GOLDEN_TURN_MDEG;

    if (thermal_input_milliK_i >= THERMAL_TARGET_MK) begin
      thermal_delta_milliK_o = thermal_input_milliK_i - THERMAL_TARGET_MK;
    end else begin
      thermal_delta_milliK_o = THERMAL_TARGET_MK - thermal_input_milliK_i;
    end

    entropy_gain_ppm_o = activation_i
      ? (16'd1000 + (active_phase_count * 16'd31) + (defect_density_i * 16'd7)
        + (thermal_zone_o == THERMAL_SOVEREIGN ? 16'd210 : 16'd0))
      : 16'd0;

    no_silicon_hardlaw_o  = 1'b1;
    no_copper_hardlaw_o   = 1'b1;
    dark_channel_required_o = 1'b1;
    right_angle_forbidden_o = 1'b1;
  end

endmodule

