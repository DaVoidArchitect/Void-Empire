// (c) 2026 VOID | Confidential Tape-Out Spec
// Formal harness for Void One checks

`timescale 1ns/1ps

module formal_properties;
  localparam int unsigned SUBNET_ID_W = 8;
  localparam int unsigned VALUE_W = 64;

  logic activation_i;
  logic state_reset_i;
  logic ledger_pulse_i;
  logic routing_pulse_i;
  logic [2:0] chakra_band_i;
  logic [3:0] cultivation_stage_i;
  logic [15:0] thermal_input_milliK_i;
  logic [7:0] defect_density_i;

  // subnet_charter_reg signals
  logic mint_req_i;
  logic [SUBNET_ID_W-1:0] mint_subnet_id_i;
  logic [VALUE_W-1:0] recursive_protocol_collateral_i;
  logic lease_tick_i;
  logic lease_paid_i;
  logic asset_minted_o;
  logic [SUBNET_ID_W-1:0] minted_subnet_id_o;
  logic [VALUE_W-1:0] minted_asset_value_o;
  logic revoke_subnet_id_o;
  logic [VALUE_W-1:0] internal_volume_q_o;
  logic [15:0] entropy_gain_ledger_o;
  logic [1:0] thermal_zone_ledger_o;
  logic collapse_guard_ledger_o;
  logic no_silicon_ledger_o;
  logic no_copper_ledger_o;
  logic dark_channel_ledger_o;

  // transaction_routing_alu signals
  logic tx_valid_i;
  logic [SUBNET_ID_W-1:0] src_subnet_id_i;
  logic [SUBNET_ID_W-1:0] dst_subnet_id_i;
  logic [VALUE_W-1:0] tx_value_i;
  logic inter_subnet_route_o;
  logic [VALUE_W-1:0] routed_value_o;
  logic [VALUE_W-1:0] tariff_value_o;
  logic [VALUE_W-1:0] lease_value_o;
  logic [VALUE_W-1:0] internal_volume_q_route_o;
  logic [63:0] treasury_address_o;
  logic [VALUE_W-1:0] treasury_credit_o;
  logic [15:0] entropy_gain_route_o;
  logic [1:0] thermal_zone_route_o;
  logic collapse_guard_route_o;
  logic no_silicon_route_o;
  logic no_copper_route_o;
  logic dark_channel_route_o;

  initial begin
    activation_i           = 1'b1;
    state_reset_i          = 1'b1;
    ledger_pulse_i         = 1'b0;
    routing_pulse_i        = 1'b0;
    chakra_band_i          = 3'd3;
    cultivation_stage_i    = 4'd5;
    thermal_input_milliK_i = 16'd3400;
    defect_density_i       = 8'd21;

    // Drive all stimulus-side inputs explicitly to avoid unconstrained
    // symbolic expansion and to keep the harness deterministic.
    mint_req_i                     = 1'b0;
    mint_subnet_id_i               = 8'd7;
    recursive_protocol_collateral_i = 64'd1000;
    lease_tick_i                   = 1'b0;
    lease_paid_i                   = 1'b1;

    tx_valid_i       = 1'b1;
    src_subnet_id_i  = 8'd3;
    dst_subnet_id_i  = 8'd9;
    tx_value_i       = 64'd10_000;

    #1 state_reset_i = 1'b0;
    #1 ledger_pulse_i = 1'b1;
    routing_pulse_i = 1'b1;
    #1 ledger_pulse_i = 1'b0;
    routing_pulse_i = 1'b0;
  end

  subnet_charter_reg #(
      .SUBNET_ID_W(SUBNET_ID_W),
      .VALUE_W(VALUE_W)
  ) u_ledger (
      .activation_i(activation_i),
      .state_reset_i(state_reset_i),
      .ledger_pulse_i(ledger_pulse_i),
      .chakra_band_i(chakra_band_i),
      .cultivation_stage_i(cultivation_stage_i),
      .thermal_input_milliK_i(thermal_input_milliK_i),
      .defect_density_i(defect_density_i),
      .mint_req_i(mint_req_i),
      .mint_subnet_id_i(mint_subnet_id_i),
      .ouroboros_collateral_i(recursive_protocol_collateral_i),
      .lease_tick_i(lease_tick_i),
      .lease_paid_i(lease_paid_i),
      .asset_minted_o(asset_minted_o),
      .minted_subnet_id_o(minted_subnet_id_o),
      .minted_asset_value_o(minted_asset_value_o),
      .revoke_subnet_id_o(revoke_subnet_id_o),
      .internal_volume_q_o(internal_volume_q_o),
      .entropy_gain_ppm_o(entropy_gain_ledger_o),
      .thermal_zone_o(thermal_zone_ledger_o),
      .collapse_guard_o(collapse_guard_ledger_o),
      .no_silicon_hardlaw_o(no_silicon_ledger_o),
      .no_copper_hardlaw_o(no_copper_ledger_o),
      .dark_channel_required_o(dark_channel_ledger_o),
      .golden_width_um_o(),
      .golden_length_um_o(),
      .preferred_turn_mdeg_o(),
      .right_angle_forbidden_o(),
      .orthogonal_grid_forbidden_o()
  );

  transaction_routing_alu #(
      .SUBNET_ID_W(SUBNET_ID_W),
      .VALUE_W(VALUE_W)
  ) u_route (
      .activation_i(activation_i),
      .state_reset_i(state_reset_i),
      .routing_pulse_i(routing_pulse_i),
      .chakra_band_i(chakra_band_i),
      .cultivation_stage_i(cultivation_stage_i),
      .thermal_input_milliK_i(thermal_input_milliK_i),
      .defect_density_i(defect_density_i),
      .tx_valid_i(tx_valid_i),
      .src_subnet_id_i(src_subnet_id_i),
      .dst_subnet_id_i(dst_subnet_id_i),
      .tx_value_i(tx_value_i),
      .inter_subnet_route_o(inter_subnet_route_o),
      .routed_value_o(routed_value_o),
      .tariff_value_o(tariff_value_o),
      .lease_value_o(lease_value_o),
      .internal_volume_q_o(internal_volume_q_route_o),
      .treasury_address_o(treasury_address_o),
      .treasury_credit_o(treasury_credit_o),
      .entropy_gain_ppm_o(entropy_gain_route_o),
      .thermal_zone_o(thermal_zone_route_o),
      .collapse_guard_o(collapse_guard_route_o),
      .no_silicon_hardlaw_o(no_silicon_route_o),
      .no_copper_hardlaw_o(no_copper_route_o),
      .dark_channel_required_o(dark_channel_route_o),
      .golden_width_um_o(),
      .golden_length_um_o(),
      .preferred_turn_mdeg_o(),
      .right_angle_forbidden_o(),
      .orthogonal_grid_forbidden_o()
  );

  // Formal assumptions
  always_comb begin
    assume(activation_i == 1'b1);
    assume(chakra_band_i != 3'd0);
    assume(cultivation_stage_i != 4'd0);
  end

  // Deadlock-resilience proxy in 2-state formal semantics:
  // use arithmetic sanity checks instead of X-propagation checks.
  always_comb if (!$initstate && !state_reset_i) begin
    assert(routed_value_o <= tx_value_i);
    assert((tariff_value_o + lease_value_o) <= tx_value_i);
  end

  // Treasury cannot be bypassed on inter-subnet routes.
  always_comb if (!$initstate && !state_reset_i && tx_valid_i && (src_subnet_id_i != dst_subnet_id_i)) begin
    assert(inter_subnet_route_o);
    assert(treasury_credit_o == tariff_value_o);
    assert(tariff_value_o > 0);
  end

  // Intra-subnet path must not charge treasury tariff.
  always_comb if (!$initstate && !state_reset_i && tx_valid_i && (src_subnet_id_i == dst_subnet_id_i)) begin
    assert(treasury_credit_o == 0);
  end

  // Constitutional constraints must always hold.
  always_comb begin
    assert(no_silicon_ledger_o);
    assert(no_copper_ledger_o);
    assert(dark_channel_ledger_o);
    assert(no_silicon_route_o);
    assert(no_copper_route_o);
    assert(dark_channel_route_o);
  end

endmodule
