// (c) 2026 VOID | Confidential Tape-Out Spec
// Void One - Plasticity Engine (Hebbian/anti-Hebbian, pulse-driven)

`timescale 1ns/1ps

module plasticity_engine #(
    parameter int unsigned MIN_WEIGHT_PPM = 32'd120_000,
    parameter int unsigned MAX_WEIGHT_PPM = 32'd995_000,
    parameter int unsigned HOMEOSTATIC_CENTER_PPM = 32'd760_000
) (
    input  logic        activation_i,
    input  logic        state_reset_i,
    input  logic        update_pulse_i,
    input  logic        route_success_i,
    input  logic        route_fail_i,
    input  logic [31:0] path_weight_ppm_i,
    output logic [31:0] path_weight_ppm_o,
    output logic [31:0] forgetting_rate_ppm_o,
    output logic [15:0] convergence_window_o
);

  logic [31:0] weight_q;
  logic [31:0] forgetting_rate_q;
  logic [15:0] convergence_window_q;

  always_ff @(posedge update_pulse_i or posedge state_reset_i) begin
    if (state_reset_i) begin
      weight_q             <= HOMEOSTATIC_CENTER_PPM;
      forgetting_rate_q    <= 32'd50_000;
      convergence_window_q <= 16'd0;
    end else if (activation_i) begin
      // Seed from external path value, then adapt with bounded plasticity.
      weight_q <= path_weight_ppm_i;

      if (route_success_i && !route_fail_i) begin
        if (weight_q < (MAX_WEIGHT_PPM - 32'd20_000)) begin
          weight_q <= weight_q + 32'd20_000;
        end else begin
          weight_q <= MAX_WEIGHT_PPM;
        end

        if (forgetting_rate_q > 32'd2_000) begin
          forgetting_rate_q <= forgetting_rate_q - 32'd2_000;
        end

        if (convergence_window_q < 16'd1024) begin
          convergence_window_q <= convergence_window_q + 16'd1;
        end
      end else if (route_fail_i) begin
        if (weight_q > (MIN_WEIGHT_PPM + 32'd16_000)) begin
          weight_q <= weight_q - 32'd16_000;
        end else begin
          weight_q <= MIN_WEIGHT_PPM;
        end

        if (forgetting_rate_q < 32'd990_000) begin
          forgetting_rate_q <= forgetting_rate_q + 32'd4_000;
        end

        convergence_window_q <= 16'd0;
      end else begin
        // Homeostatic recentering.
        if (weight_q > HOMEOSTATIC_CENTER_PPM) begin
          weight_q <= weight_q - 32'd3_000;
        end else if (weight_q < HOMEOSTATIC_CENTER_PPM) begin
          weight_q <= weight_q + 32'd2_000;
        end

        if (forgetting_rate_q > 32'd1_000) begin
          forgetting_rate_q <= forgetting_rate_q - 32'd1_000;
        end
      end
    end
  end

  assign path_weight_ppm_o    = weight_q;
  assign forgetting_rate_ppm_o = forgetting_rate_q;
  assign convergence_window_o  = convergence_window_q;

endmodule
