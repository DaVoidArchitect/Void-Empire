// (c) 2026 VOID | Confidential Tape-Out Spec
// Void One - Clockless Subnet Charter Register / Recursive Protocol Ledger

`timescale 1ns/1ps

module subnet_charter_reg #(
    parameter int unsigned SUBNET_ID_W = 8,
    parameter int unsigned VALUE_W = 64,
    parameter int unsigned LEASE_GRACE_CYCLES = 128
) (
    input  logic                       activation_i,
    input  logic                       state_reset_i,
    input  logic                       ledger_pulse_i,
    input  logic [2:0]                 chakra_band_i,
    input  logic [3:0]                 cultivation_stage_i,
    input  logic [15:0]                thermal_input_milliK_i,
    input  logic [7:0]                 defect_density_i,
    input  logic                       mint_req_i,
    input  logic [SUBNET_ID_W-1:0]     mint_subnet_id_i,
    input  logic [VALUE_W-1:0]         ouroboros_collateral_i,
    input  logic                       lease_tick_i,
    input  logic                       lease_paid_i,
    output logic                       asset_minted_o,
    output logic [SUBNET_ID_W-1:0]     minted_subnet_id_o,
    output logic [VALUE_W-1:0]         minted_asset_value_o,
    output logic                       revoke_subnet_id_o,
    output logic [VALUE_W-1:0]         internal_volume_q_o,
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

  // Hard-coded VOID Recursive Protocol constants.
  localparam int INTER_SUBNET_TARIFF_BPS = 618;  // 6.18%
  localparam int INTRA_SUBNET_LEASE_BPS  = 16;   // 0.1618% (rounded BPS representation)
  localparam logic [17:0] GOLDEN_TURN_MDEG = 18'd137507;
  localparam logic [1:0] THERMAL_CULTIVATION = 2'd0;
  localparam logic [1:0] THERMAL_SOVEREIGN   = 2'd1;
  localparam logic [1:0] THERMAL_COLLAPSE    = 2'd2;
  localparam int unsigned CULTIVATION_MAX_MK = 16'd2400;
  localparam int unsigned SOVEREIGN_MAX_MK   = 16'd5600;

  logic [15:0] lease_age_q;
  logic [VALUE_W-1:0] internal_volume_q;
  logic [15:0] cultivation_depth_q;
  logic [VALUE_W*2-1:0] mint_scaled_w;
  logic [VALUE_W-1:0]   mint_base_value_w;

  function automatic logic [31:0] mul_phi(input logic [31:0] base);
    logic [63:0] scaled;
    begin
      scaled = base * PHI_NUM;
      mul_phi = scaled / PHI_DEN;
    end
  endfunction

  always_comb begin
    // Mint model: principal + harmonic issuance uplift derived from INTER_SUBNET_TARIFF_BPS.
    mint_scaled_w     = ouroboros_collateral_i * INTER_SUBNET_TARIFF_BPS;
    mint_base_value_w = ouroboros_collateral_i + (mint_scaled_w / 10000);
  end

  // Clockless progression: ledger transitions only on explicit ledger pulses.
  always_ff @(posedge ledger_pulse_i or posedge state_reset_i) begin
    if (state_reset_i) begin
      asset_minted_o       <= 1'b0;
      minted_subnet_id_o   <= '0;
      minted_asset_value_o <= '0;
      revoke_subnet_id_o   <= 1'b0;
      lease_age_q          <= '0;
      internal_volume_q    <= '0;
      cultivation_depth_q  <= '0;
    end else if (activation_i) begin
      asset_minted_o <= 1'b0;
      cultivation_depth_q <= cultivation_depth_q + cultivation_stage_i + chakra_band_i;

      if (mint_req_i && !collapse_guard_o) begin
        asset_minted_o       <= 1'b1;
        minted_subnet_id_o   <= mint_subnet_id_i;
        minted_asset_value_o <= mint_base_value_w + (mint_base_value_w * defect_density_i / 1000);
        internal_volume_q    <= internal_volume_q + ouroboros_collateral_i;
      end

      if (lease_tick_i) begin
        if (lease_paid_i) begin
          lease_age_q        <= '0;
          revoke_subnet_id_o <= 1'b0;
        end else begin
          if (lease_age_q < LEASE_GRACE_CYCLES[15:0]) begin
            lease_age_q <= lease_age_q + 1'b1 + chakra_band_i[0];
          end

          // Strict revocation requirement: unpaid cyclical lease hard-revokes sync.
          if (lease_age_q >= LEASE_GRACE_CYCLES[15:0]) begin
            revoke_subnet_id_o <= 1'b1;
          end
        end
      end
    end
  end

  assign internal_volume_q_o = internal_volume_q;

  always_comb begin
    logic [31:0] width_seed;

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

    entropy_gain_ppm_o = activation_i
      ? (16'd900 + (chakra_band_i * 16'd23) + (cultivation_stage_i * 16'd17)
        + (defect_density_i * 16'd8)
        + (thermal_zone_o == THERMAL_SOVEREIGN ? 16'd160 : 16'd0))
      : 16'd0;

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
