// (c) 2026 VOID | Confidential Tape-Out Spec
// Void One - Clockless Topological Braider

`timescale 1ns/1ps

module topological_braider #(
    parameter int unsigned DATA_W = 32,
    parameter int unsigned BRAID_CHANNELS = 9
) (
    input  logic                        activation_i,
    input  logic                        state_reset_i,
    input  logic                        braid_pulse_i,
    input  logic [2:0]                  chakra_band_i,
    input  logic [3:0]                  cultivation_stage_i,
    input  logic [15:0]                 thermal_input_milliK_i,
    input  logic [7:0]                  defect_density_i,
    input  logic [BRAID_CHANNELS-1:0]   braid_seed_i,
    input  logic [DATA_W-1:0]           braid_payload_i,
    output logic [DATA_W-1:0]           braided_payload_o,
    output logic [15:0]                 braid_energy_o,
    output logic [15:0]                 entropy_gain_ppm_o,
    output logic [1:0]                  thermal_zone_o,
    output logic                        collapse_guard_o,
    output logic                        no_silicon_hardlaw_o,
    output logic                        no_copper_hardlaw_o,
    output logic                        dark_channel_required_o,
    output logic [31:0]                 golden_width_um_o,
    output logic [31:0]                 golden_length_um_o,
    output logic [31:0]                 golden_arc_radius_um_o,
    output logic [17:0]                 preferred_turn_mdeg_o,
    output logic                        right_angle_forbidden_o,
    output logic                        orthogonal_grid_forbidden_o
);

  real GEOMETRIC_PHI = 1.6180339887;
  localparam logic [17:0] GOLDEN_TURN_MDEG = 18'd137507;
  localparam logic [1:0] THERMAL_CULTIVATION = 2'd0;
  localparam logic [1:0] THERMAL_SOVEREIGN   = 2'd1;
  localparam logic [1:0] THERMAL_COLLAPSE    = 2'd2;
  localparam int unsigned CULTIVATION_MAX_MK = 16'd2400;
  localparam int unsigned SOVEREIGN_MAX_MK   = 16'd5600;

  logic [DATA_W-1:0] braid_state_q;
  logic [15:0]       braid_depth_q;

  function automatic logic [DATA_W-1:0] braid_mask(
      input logic [BRAID_CHANNELS-1:0] braid_seed,
      input logic [2:0] chakra_band,
      input logic [3:0] cultivation_stage
  );
    logic [DATA_W-1:0] mask;
    int idx;
    begin
      mask = '0;
      for (idx = 0; idx < DATA_W; idx++) begin
        mask[idx] = braid_seed[idx % BRAID_CHANNELS]
          ^ chakra_band[idx % 3]
          ^ cultivation_stage[idx % 4];
      end
      braid_mask = mask;
    end
  endfunction

  // Clockless braiding transitions occur only on explicit braid pulses.
  always_latch begin
    if (state_reset_i) begin
      braid_state_q <= '0;
      braid_depth_q <= 16'd3;
    end else if (activation_i && braid_pulse_i) begin
      if (!collapse_guard_o) begin
        braid_state_q <= braid_payload_i
          ^ braid_mask(braid_seed_i, chakra_band_i, cultivation_stage_i)
          ^ {DATA_W{defect_density_i[0]}};
      end
      braid_depth_q <= 16'(
        3 + $countones(braid_seed_i) + chakra_band_i + cultivation_stage_i + (defect_density_i / 32)
      );
    end
  end

  always_comb begin
    int width_seed;

    braided_payload_o = activation_i ? braid_state_q : '0;
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

    braid_energy_o = activation_i
      ? (collapse_guard_o ? (braid_depth_q >> 1) : braid_depth_q)
      : 16'd0;

    entropy_gain_ppm_o = activation_i
      ? (16'd1200 + (16'($countones(braid_seed_i)) * 16'd19)
        + (defect_density_i * 16'd11)
        + (thermal_zone_o == THERMAL_SOVEREIGN ? 16'd250 : 16'd0))
      : 16'd0;

    width_seed            = 161 + (int'(chakra_band_i) * 17) + (int'(cultivation_stage_i) * 11)
      + ($countones(braid_seed_i) * 5);
    golden_width_um_o     = activation_i ? logic'(width_seed[31:0]) : 32'd0;
    golden_length_um_o    = activation_i ? $rtoi(golden_width_um_o * GEOMETRIC_PHI) : 32'd0;
    golden_arc_radius_um_o = activation_i ? $rtoi(golden_length_um_o * GEOMETRIC_PHI) : 32'd0;

    preferred_turn_mdeg_o       = GOLDEN_TURN_MDEG;
    no_silicon_hardlaw_o        = 1'b1;
    no_copper_hardlaw_o         = 1'b1;
    dark_channel_required_o     = 1'b1;
    right_angle_forbidden_o     = 1'b1;
    orthogonal_grid_forbidden_o = 1'b1;
  end

endmodule

