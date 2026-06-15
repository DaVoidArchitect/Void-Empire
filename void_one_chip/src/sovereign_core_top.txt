// (c) 2026 VOID | Confidential Tape-Out Spec
// Void One - Timing-Tree-Free Top-Level Architecture

`timescale 1ns/1ps

module sovereign_core_top #(
    parameter logic [1:0] FORM_FACTOR_SELECT = 2'd0
) (
    input  logic        activation_i,
    input  logic        state_reset_i,
    input  logic        geometry_commit_i,
    input  logic [2:0]  chakra_band_i,
    input  logic [2:0]  cultivation_stage_i,
    input  logic [15:0] thermal_input_milliK_i,
    input  logic [7:0]  defect_density_i,
    output logic [1:0]  form_factor_id_o,
    output logic [31:0] form_factor_diameter_um_o,
    output logic [31:0] phi_tier1_um_o,
    output logic [31:0] phi_tier2_um_o,
    output logic [31:0] phi_tier3_um_o,
    output logic [31:0] golden_width_um_o,
    output logic [31:0] golden_length_um_o,
    output logic [31:0] golden_arc_radius_um_o,
    output logic [17:0] preferred_turn_mdeg_o,
    output logic [15:0] entropy_gain_ppm_o,
    output logic [31:0] connectome_path_efficiency_ppm_o,
    output logic [31:0] connectome_anomaly_score_ppm_o,
    output logic [15:0] connectome_memory_retention_pct_o,
    output logic [31:0] plasticity_forgetting_rate_ppm_o,
    output logic [15:0] plasticity_convergence_window_o,
    output logic [31:0] immune_precision_ppm_o,
    output logic [31:0] immune_recall_ppm_o,
    output logic        immune_quarantine_o,
    output logic [1:0]  thermal_zone_o,
    output logic        collapse_guard_o,
    output logic        no_silicon_hardlaw_o,
    output logic        no_copper_hardlaw_o,
    output logic        dark_channel_required_o,
    output logic        right_angle_forbidden_o,
    output logic        orthogonal_grid_forbidden_o
);

  localparam int unsigned PHI_NUM = 32'd1_618_034;
  localparam int unsigned PHI_DEN = 32'd1_000_000;

  typedef enum logic [1:0] {
    SOVEREIGN_APEX     = 2'd0,
    SOVEREIGN_MONOLITH = 2'd1,
    SOVEREIGN_NODE     = 2'd2,
    SOVEREIGN_SEED     = 2'd3
  } sovereign_form_factor_e;

  // Thermodynamic transmutation band IDs.
  localparam logic [1:0] THERMAL_CULTIVATION = 2'd0;
  localparam logic [1:0] THERMAL_SOVEREIGN   = 2'd1;
  localparam logic [1:0] THERMAL_COLLAPSE    = 2'd2;

  // Band thresholds are intentionally bounded and physically plausible.
  localparam int unsigned CULTIVATION_MAX_MK = 16'd2400;
  localparam int unsigned SOVEREIGN_MAX_MK   = 16'd5600;

  localparam int unsigned SOVEREIGN_APEX_DIAMETER_UM     = 32'd212000;
  localparam int unsigned SOVEREIGN_MONOLITH_DIAMETER_UM = 32'd100000;
  localparam int unsigned SOVEREIGN_NODE_DIAMETER_UM     = 32'd15000;
  localparam int unsigned SOVEREIGN_SEED_DIAMETER_UM     = 32'd100;
  localparam logic [17:0] GOLDEN_TURN_MDEG = 18'd137507;

  logic [31:0] selected_diameter_um;
  logic [31:0] chakra_gain_ppm_q;
  logic [31:0] cultivation_gain_ppm_q;
  logic [31:0] connectome_path_eff_ppm_w;
  logic [31:0] connectome_anomaly_ppm_w;
  logic [15:0] connectome_memory_retention_pct_w;
  logic        connectome_quarantine_w;
  logic [31:0] plasticity_path_weight_ppm_w;
  logic [31:0] plasticity_forgetting_rate_ppm_w;
  logic [15:0] plasticity_convergence_window_w;
  logic        route_success_w;
  logic        route_fail_w;

  assign route_success_w = activation_i && geometry_commit_i && !collapse_guard_o;
  assign route_fail_w    = activation_i && geometry_commit_i && collapse_guard_o;

  defect_connectome u_defect_connectome (
      .activation_i(activation_i),
      .state_reset_i(state_reset_i),
      .update_pulse_i(geometry_commit_i),
      .route_success_i(route_success_w),
      .route_fail_i(route_fail_w),
      .defect_density_i(defect_density_i),
      .thermal_zone_i(thermal_zone_o),
      .path_efficiency_ppm_o(connectome_path_eff_ppm_w),
      .anomaly_score_ppm_o(connectome_anomaly_ppm_w),
      .memory_retention_pct_o(connectome_memory_retention_pct_w),
      .quarantine_recommend_o(connectome_quarantine_w)
  );

  plasticity_engine u_plasticity_engine (
      .activation_i(activation_i),
      .state_reset_i(state_reset_i),
      .update_pulse_i(geometry_commit_i),
      .route_success_i(route_success_w),
      .route_fail_i(route_fail_w),
      .path_weight_ppm_i(connectome_path_eff_ppm_w),
      .path_weight_ppm_o(plasticity_path_weight_ppm_w),
      .forgetting_rate_ppm_o(plasticity_forgetting_rate_ppm_w),
      .convergence_window_o(plasticity_convergence_window_w)
  );

  immune_pruner u_immune_pruner (
      .activation_i(activation_i),
      .state_reset_i(state_reset_i),
      .update_pulse_i(geometry_commit_i),
      .anomaly_score_ppm_i(connectome_anomaly_ppm_w),
      .path_efficiency_ppm_i(plasticity_path_weight_ppm_w),
      .quarantine_o(immune_quarantine_o),
      .quarantine_score_ppm_o(),
      .precision_proxy_ppm_o(immune_precision_ppm_o),
      .recall_proxy_ppm_o(immune_recall_ppm_o)
  );

  function automatic logic [31:0] apply_gain(input logic [31:0] base, input logic [31:0] gain_ppm);
    logic [63:0] scaled;
    begin
      scaled = base * gain_ppm;
      apply_gain = scaled / 32'd1_000_000;
    end
  endfunction

  function automatic logic [31:0] mul_phi(input logic [31:0] base);
    logic [63:0] scaled;
    begin
      scaled = base * PHI_NUM;
      mul_phi = scaled / PHI_DEN;
    end
  endfunction

  function automatic logic [31:0] div_phi(input logic [31:0] base);
    logic [63:0] scaled;
    begin
      scaled = base * PHI_DEN;
      div_phi = scaled / PHI_NUM;
    end
  endfunction

  // Clockless progression: state advances only on explicit geometry commit pulses.
  always_ff @(posedge geometry_commit_i or posedge state_reset_i) begin
    if (state_reset_i) begin
      chakra_gain_ppm_q      <= 32'd1_000_000;
      cultivation_gain_ppm_q <= 32'd1_000_000;
    end else if (activation_i) begin
      chakra_gain_ppm_q      <= 32'd1_000_000 + (32'(chakra_band_i) * 32'd61_800);
      cultivation_gain_ppm_q <= 32'd1_000_000 + (32'(cultivation_stage_i) * 32'd38_200);
    end
  end

  always_comb begin
    logic [31:0] defect_gain_ppm;
    logic [31:0] thermal_gain_ppm;

    unique case (FORM_FACTOR_SELECT)
      SOVEREIGN_APEX:     selected_diameter_um = SOVEREIGN_APEX_DIAMETER_UM;
      SOVEREIGN_MONOLITH: selected_diameter_um = SOVEREIGN_MONOLITH_DIAMETER_UM;
      SOVEREIGN_NODE:     selected_diameter_um = SOVEREIGN_NODE_DIAMETER_UM;
      default:            selected_diameter_um = SOVEREIGN_SEED_DIAMETER_UM;
    endcase

    if (thermal_input_milliK_i <= CULTIVATION_MAX_MK) begin
      thermal_zone_o   = THERMAL_CULTIVATION;
      collapse_guard_o = 1'b0;
      thermal_gain_ppm = 32'd1_060_000;
    end else if (thermal_input_milliK_i <= SOVEREIGN_MAX_MK) begin
      thermal_zone_o   = THERMAL_SOVEREIGN;
      collapse_guard_o = 1'b0;
      thermal_gain_ppm = 32'd1_150_000;
    end else begin
      thermal_zone_o   = THERMAL_COLLAPSE;
      collapse_guard_o = 1'b1;
      thermal_gain_ppm = 32'd980_000;
    end

    defect_gain_ppm = 32'd1_000_000 + (32'(defect_density_i) * 32'd1_200);

    form_factor_id_o          = FORM_FACTOR_SELECT;
    form_factor_diameter_um_o = activation_i ? selected_diameter_um : 32'd0;

    phi_tier1_um_o = activation_i
      ? apply_gain(
          apply_gain(mul_phi(selected_diameter_um), chakra_gain_ppm_q),
          thermal_gain_ppm
        )
      : 32'd0;

    phi_tier2_um_o = activation_i
      ? apply_gain(
          apply_gain(div_phi(selected_diameter_um), cultivation_gain_ppm_q),
          defect_gain_ppm
        )
      : 32'd0;

    phi_tier3_um_o = activation_i
      ? div_phi(phi_tier2_um_o)
      : 32'd0;

    golden_width_um_o      = activation_i ? (phi_tier3_um_o + 32'd89) : 32'd0;
    golden_length_um_o     = activation_i ? mul_phi(golden_width_um_o) : 32'd0;
    golden_arc_radius_um_o = activation_i ? mul_phi(golden_length_um_o) : 32'd0;

    entropy_gain_ppm_o = activation_i
      ? 16'(
          thermal_gain_ppm[15:0]
          + defect_gain_ppm[15:0]
          + 16'(chakra_band_i)
          + 16'(cultivation_stage_i)
          + (immune_quarantine_o ? 16'd13 : 16'd29)
        )
      : 16'd0;

    connectome_path_efficiency_ppm_o = activation_i ? connectome_path_eff_ppm_w : 32'd0;
    connectome_anomaly_score_ppm_o = activation_i ? connectome_anomaly_ppm_w : 32'd0;
    connectome_memory_retention_pct_o = activation_i ? connectome_memory_retention_pct_w : 16'd0;
    plasticity_forgetting_rate_ppm_o = activation_i ? plasticity_forgetting_rate_ppm_w : 32'd0;
    plasticity_convergence_window_o = activation_i ? plasticity_convergence_window_w : 16'd0;

    preferred_turn_mdeg_o       = GOLDEN_TURN_MDEG;
    no_silicon_hardlaw_o        = 1'b1;
    no_copper_hardlaw_o         = 1'b1;
    dark_channel_required_o     = 1'b1;
    right_angle_forbidden_o     = 1'b1;
    orthogonal_grid_forbidden_o = 1'b1;
  end

endmodule
