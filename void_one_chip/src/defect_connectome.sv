// (c) 2026 VOID | Confidential Tape-Out Spec
// Void One - Defect Connectome (clockless, pulse-driven)

`timescale 1ns/1ps

module defect_connectome #(
    parameter int unsigned DEFECT_W = 8,
    parameter int unsigned BASE_PATH_EFF_PPM = 32'd720_000,
    parameter int unsigned MIN_PATH_EFF_PPM = 32'd120_000,
    parameter int unsigned MAX_PATH_EFF_PPM = 32'd995_000
) (
    input  logic                 activation_i,
    input  logic                 state_reset_i,
    input  logic                 update_pulse_i,
    input  logic                 route_success_i,
    input  logic                 route_fail_i,
    input  logic [DEFECT_W-1:0] defect_density_i,
    input  logic [1:0]           thermal_zone_i,
    output logic [31:0]          path_efficiency_ppm_o,
    output logic [31:0]          anomaly_score_ppm_o,
    output logic [15:0]          memory_retention_pct_o,
    output logic                 quarantine_recommend_o
);

  localparam logic [1:0] THERMAL_CULTIVATION = 2'd0;
  localparam logic [1:0] THERMAL_SOVEREIGN   = 2'd1;
  localparam logic [1:0] THERMAL_COLLAPSE    = 2'd2;

  logic [31:0] path_eff_q;
  logic [31:0] anomaly_q;
  logic [31:0] memory_trace_ppm_q;
  logic [31:0] memory_peak_ppm_q;

  always_ff @(posedge update_pulse_i or posedge state_reset_i) begin
    if (state_reset_i) begin
      path_eff_q         <= BASE_PATH_EFF_PPM;
      anomaly_q          <= 32'd280_000;
      memory_trace_ppm_q <= 32'd600_000;
      memory_peak_ppm_q  <= 32'd600_000;
    end else if (activation_i) begin
      logic [31:0] defect_term;
      logic [31:0] thermal_penalty;

      defect_term = ({24'd0, defect_density_i} << 6);
      unique case (thermal_zone_i)
        THERMAL_CULTIVATION: thermal_penalty = 32'd0;
        THERMAL_SOVEREIGN:   thermal_penalty = 32'd8_000;
        default:             thermal_penalty = 32'd30_000;
      endcase

      if (route_success_i && !route_fail_i) begin
        if (path_eff_q < (MAX_PATH_EFF_PPM - 32'd32_000)) begin
          path_eff_q <= path_eff_q + 32'd32_000 + defect_term;
        end else begin
          path_eff_q <= MAX_PATH_EFF_PPM;
        end

        if (anomaly_q > (32'd28_000 + defect_term)) begin
          anomaly_q <= anomaly_q - 32'd28_000 - defect_term + thermal_penalty;
        end else begin
          anomaly_q <= 32'd0 + thermal_penalty;
        end

        if (memory_trace_ppm_q < 32'd980_000) begin
          memory_trace_ppm_q <= memory_trace_ppm_q + 32'd24_000;
        end else begin
          memory_trace_ppm_q <= 32'd995_000;
        end
      end else if (route_fail_i) begin
        if (path_eff_q > (MIN_PATH_EFF_PPM + 32'd36_000)) begin
          path_eff_q <= path_eff_q - 32'd36_000;
        end else begin
          path_eff_q <= MIN_PATH_EFF_PPM;
        end

        if (anomaly_q < 32'd970_000) begin
          anomaly_q <= anomaly_q + 32'd48_000 + defect_term + thermal_penalty;
        end else begin
          anomaly_q <= 32'd995_000;
        end

        if (memory_trace_ppm_q > 32'd22_000) begin
          memory_trace_ppm_q <= memory_trace_ppm_q - 32'd22_000;
        end else begin
          memory_trace_ppm_q <= 32'd0;
        end
      end else begin
        // Homeostatic drift with bounded decay to avoid lock-in.
        if (path_eff_q > BASE_PATH_EFF_PPM) begin
          path_eff_q <= path_eff_q - 32'd4_000;
        end else if (path_eff_q < BASE_PATH_EFF_PPM) begin
          path_eff_q <= path_eff_q + 32'd2_000;
        end

        if (anomaly_q > 32'd4_000) begin
          anomaly_q <= anomaly_q - 32'd4_000;
        end

        if (memory_trace_ppm_q > 32'd6_000) begin
          memory_trace_ppm_q <= memory_trace_ppm_q - 32'd6_000;
        end
      end

      if (memory_trace_ppm_q > memory_peak_ppm_q) begin
        memory_peak_ppm_q <= memory_trace_ppm_q;
      end
    end
  end

  always_comb begin
    logic [63:0] retention_scaled;

    path_efficiency_ppm_o   = path_eff_q;
    anomaly_score_ppm_o     = anomaly_q;
    quarantine_recommend_o  = (anomaly_q > 32'd720_000) || (path_eff_q < 32'd340_000);

    if (memory_peak_ppm_q == 32'd0) begin
      memory_retention_pct_o = 16'd100;
    end else begin
      retention_scaled = (64'(memory_trace_ppm_q) * 64'd100) / memory_peak_ppm_q;
      if (retention_scaled > 64'd65535) begin
        memory_retention_pct_o = 16'hFFFF;
      end else begin
        memory_retention_pct_o = logic'(retention_scaled[15:0]);
      end
    end
  end

endmodule
