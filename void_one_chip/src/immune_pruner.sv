// (c) 2026 VOID | Confidential Tape-Out Spec
// Void One - Immune Pruner for defect-route quarantine

`timescale 1ns/1ps

module immune_pruner (
    input  logic        activation_i,
    input  logic        state_reset_i,
    input  logic        update_pulse_i,
    input  logic [31:0] anomaly_score_ppm_i,
    input  logic [31:0] path_efficiency_ppm_i,
    output logic        quarantine_o,
    output logic [31:0] quarantine_score_ppm_o,
    output logic [31:0] precision_proxy_ppm_o,
    output logic [31:0] recall_proxy_ppm_o
);

  logic [31:0] quarantine_score_q;
  logic [31:0] precision_q;
  logic [31:0] recall_q;

  always_ff @(posedge update_pulse_i or posedge state_reset_i) begin
    if (state_reset_i) begin
      quarantine_score_q <= 32'd200_000;
      precision_q        <= 32'd900_000;
      recall_q           <= 32'd880_000;
    end else if (activation_i) begin
      if (anomaly_score_ppm_i > 32'd700_000 || path_efficiency_ppm_i < 32'd320_000) begin
        if (quarantine_score_q < 32'd995_000) begin
          quarantine_score_q <= quarantine_score_q + 32'd32_000;
        end

        if (precision_q > 32'd860_000) begin
          precision_q <= precision_q - 32'd2_000;
        end
        if (recall_q < 32'd990_000) begin
          recall_q <= recall_q + 32'd4_000;
        end
      end else begin
        if (quarantine_score_q > 32'd6_000) begin
          quarantine_score_q <= quarantine_score_q - 32'd6_000;
        end

        if (precision_q < 32'd995_000) begin
          precision_q <= precision_q + 32'd1_500;
        end
        if (recall_q > 32'd880_000) begin
          recall_q <= recall_q - 32'd800;
        end
      end
    end
  end

  assign quarantine_o           = (quarantine_score_q > 32'd720_000);
  assign quarantine_score_ppm_o = quarantine_score_q;
  assign precision_proxy_ppm_o  = precision_q;
  assign recall_proxy_ppm_o     = recall_q;

endmodule
