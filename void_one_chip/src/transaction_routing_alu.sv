// (c) 2026 VOID | Confidential Tape-Out Spec
// Void One - Clockless Transaction Routing ALU / Toll Gate

`timescale 1ns/1ps

module transaction_routing_alu #(
    parameter int unsigned SUBNET_ID_W = 8,
    parameter int unsigned VALUE_W = 64,
    parameter int unsigned BPS_DENOM = 10_000,
    parameter logic [63:0] XENALCHEMY_GENESIS_TREASURY_ADDR = 64'h58454E41_4C434845  // "XENALCHE"
) (
    input  logic                       activation_i,
    input  logic                       state_reset_i,
    input  logic                       routing_pulse_i,
    input  logic [2:0]                 chakra_band_i,
    input  logic [3:0]                 cultivation_stage_i,
    input  logic [15:0]                thermal_input_milliK_i,
    input  logic [7:0]                 defect_density_i,
    input  logic                       tx_valid_i,
    input  logic [SUBNET_ID_W-1:0]     src_subnet_id_i,
    input  logic [SUBNET_ID_W-1:0]     dst_subnet_id_i,
    input  logic [VALUE_W-1:0]         tx_value_i,
    output logic                       inter_subnet_route_o,
    output logic [VALUE_W-1:0]         routed_value_o,
    output logic [VALUE_W-1:0]         tariff_value_o,
    output logic [VALUE_W-1:0]         lease_value_o,
    output logic [VALUE_W-1:0]         internal_volume_q_o,
    output logic [63:0]                treasury_address_o,
    output logic [VALUE_W-1:0]         treasury_credit_o,
    output logic [15:0]                entropy_gain_ppm_o,
    output logic [1:0]                 thermal_zone_o,
    output logic                       collapse_guard_o,
    output logic                       no_silicon_hardlaw_o,
    output logic                       no_copper_hardlaw_o,
    output logic                       dark_channel_required_o,
    output logic [31:0]                golden_width_um_o,
    output logic [31:0]                golden_length_um_o,
    output logic [17:0]                preferred_turn_mdeg_o,
    output logic                       right_angle_forbidden_o,
    output logic                       orthogonal_grid_forbidden_o
);

  localparam int unsigned PHI_NUM = 32'd1_618_034;
  localparam int unsigned PHI_DEN = 32'd1_000_000;

  // Hard-coded VOID Recursive Protocol economics.
  localparam int INTER_SUBNET_TARIFF_BPS = 618; // 6.18%
  localparam int INTRA_SUBNET_LEASE_BPS  = 16;  // 0.1618% (rounded BPS representation)
  localparam logic [17:0] GOLDEN_TURN_MDEG = 18'd137507;
  localparam logic [1:0] THERMAL_CULTIVATION = 2'd0;
  localparam logic [1:0] THERMAL_SOVEREIGN   = 2'd1;
  localparam logic [1:0] THERMAL_COLLAPSE    = 2'd2;
  localparam int unsigned CULTIVATION_MAX_MK = 16'd2400;
  localparam int unsigned SOVEREIGN_MAX_MK   = 16'd5600;

  logic [VALUE_W-1:0] internal_volume_q;
  logic [VALUE_W*2-1:0] tariff_product;
  logic [VALUE_W*2-1:0] lease_product;

  function automatic logic [31:0] mul_phi(input logic [31:0] base);
    logic [63:0] scaled;
    begin
      scaled = base * PHI_NUM;
      mul_phi = scaled / PHI_DEN;
    end
  endfunction

  always_comb begin
    inter_subnet_route_o = (src_subnet_id_i != dst_subnet_id_i);

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

    tariff_product = tx_value_i * INTER_SUBNET_TARIFF_BPS;
    lease_product  = tx_value_i * INTRA_SUBNET_LEASE_BPS;

    tariff_value_o = inter_subnet_route_o ? (tariff_product / BPS_DENOM) : '0;
    lease_value_o  = inter_subnet_route_o ? '0 : (lease_product / BPS_DENOM);

    if (!collapse_guard_o && tx_value_i >= (tariff_value_o + lease_value_o)) begin
      routed_value_o = tx_value_i - tariff_value_o - lease_value_o;
    end else begin
      routed_value_o = '0;
    end

    treasury_address_o = XENALCHEMY_GENESIS_TREASURY_ADDR;
    treasury_credit_o  = inter_subnet_route_o ? tariff_value_o : '0;

    entropy_gain_ppm_o = activation_i
      ? (16'd800 + (inter_subnet_route_o ? 16'd210 : 16'd70)
        + (defect_density_i * 16'd6)
        + (thermal_zone_o == THERMAL_SOVEREIGN ? 16'd120 : 16'd0))
      : 16'd0;
  end

  // Clockless internal volume updates occur only on explicit routing pulses.
  always_ff @(posedge routing_pulse_i or posedge state_reset_i) begin
    if (state_reset_i) begin
      internal_volume_q <= '0;
    end else if (
      activation_i && tx_valid_i && !inter_subnet_route_o && !collapse_guard_o
    ) begin
      // Intra-subnet lease basis tracker.
      internal_volume_q <= internal_volume_q + tx_value_i + chakra_band_i + cultivation_stage_i;
    end
  end

  assign internal_volume_q_o = internal_volume_q;

  always_comb begin
    logic [31:0] width_seed;

    width_seed              = 161 + (int'(chakra_band_i) * 17) + (int'(cultivation_stage_i) * 11);
    golden_width_um_o       = activation_i ? width_seed : 32'd0;
    golden_length_um_o      = activation_i ? mul_phi(golden_width_um_o) : 32'd0;
    preferred_turn_mdeg_o   = GOLDEN_TURN_MDEG;
    no_silicon_hardlaw_o    = 1'b1;
    no_copper_hardlaw_o     = 1'b1;
    dark_channel_required_o = 1'b1;
    right_angle_forbidden_o = 1'b1;
    orthogonal_grid_forbidden_o = 1'b1;
  end

endmodule
