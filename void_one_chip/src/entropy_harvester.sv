// (c) 2026 VOID | Confidential Tape-Out Spec
// Void One - Non-Linear Entropy Harvester (Sovereign Path)

`timescale 1ns/1ps

module entropy_harvester #(
    parameter int unsigned THERMAL_W = 16,
    parameter int unsigned HARVEST_TARGET_MK = 16'd4200,
    parameter int unsigned MAX_HEAT_LOAD_MK = 16'd9500,
    parameter int unsigned EXP_STEP_MK = 16'd1200,
    parameter int unsigned FEEDBACK_LOOPS = 4,
    parameter int unsigned BASE_EFF_PPM = 32'd1800,
    parameter int unsigned MAX_EFF_PPM = 32'd995000
) (
    input  logic                  activation_i,
    input  logic                  state_reset_i,
    input  logic                  harvest_pulse_i,
    input  logic [THERMAL_W-1:0] thermal_input_milliK_i,
    input  logic [7:0]            defect_density_i,
    input  logic [2:0]            chakra_band_i,
    input  logic [3:0]            cultivation_stage_i,
    output logic [THERMAL_W-1:0] thermal_delta_milliK_o,
    output logic [31:0]           work_multiplier_ppm_o,
    output logic [31:0]           loop_gain_ppm_o,
    output logic [31:0]           conversion_efficiency_ppm_o,
    output logic [15:0]           entropy_gain_ppm_o
);

  localparam int unsigned ONE_PPM = 32'd1_000_000;

  function automatic logic [31:0] exp10_multiplier_ppm(
      input logic [THERMAL_W-1:0] delta_mk,
      input int unsigned          step_mk
  );
    int unsigned decade;
    int unsigned remainder;
    int unsigned in_decade_scale_ppm;
    logic [63:0] base_mult_ppm;
    logic [63:0] scaled;
    begin
      decade = int'(delta_mk) / step_mk;
      remainder = int'(delta_mk) % step_mk;

      // Interpolate 1x..10x inside each decade.
      in_decade_scale_ppm = ONE_PPM + ((remainder * 9 * ONE_PPM) / step_mk);

      unique case (decade)
        0: base_mult_ppm = 64'(ONE_PPM);
        1: base_mult_ppm = 64'(ONE_PPM * 10);
        2: base_mult_ppm = 64'(ONE_PPM * 100);
        default: base_mult_ppm = 64'(ONE_PPM * 1000);
      endcase

      scaled = (base_mult_ppm * in_decade_scale_ppm) / ONE_PPM;
      if (scaled > 64'(ONE_PPM * 1000)) begin
        exp10_multiplier_ppm = ONE_PPM * 1000;
      end else begin
        exp10_multiplier_ppm = logic'(scaled[31:0]);
      end
    end
  endfunction

  function automatic logic [31:0] nonlinear_loop_gain_ppm(
      input logic [THERMAL_W-1:0] delta_mk
  );
    logic [63:0] gain_ppm;
    logic [31:0] slope_ppm;
    int idx;
    begin
      // Bounded slope in [1.0, 1.95].
      slope_ppm = ONE_PPM
        + ((int'(delta_mk) * 950_000) / (int'(HARVEST_TARGET_MK) + 1));
      if (slope_ppm > 32'd1_950_000) begin
        slope_ppm = 32'd1_950_000;
      end

      gain_ppm = ONE_PPM;
      for (idx = 0; idx < FEEDBACK_LOOPS; idx++) begin
        gain_ppm = (gain_ppm * slope_ppm) / ONE_PPM;
      end

      if (gain_ppm > 64'd20_000_000) begin
        nonlinear_loop_gain_ppm = 32'd20_000_000;
      end else begin
        nonlinear_loop_gain_ppm = logic'(gain_ppm[31:0]);
      end
    end
  endfunction

  always_comb begin
    logic [THERMAL_W-1:0] thermal_delta_mk;
    logic [THERMAL_W-1:0] bounded_thermal_input_mk;
    logic [31:0] work_mult_ppm;
    logic [31:0] loop_gain_ppm;
    logic [63:0] eff_ppm;

    if (thermal_input_milliK_i > MAX_HEAT_LOAD_MK) begin
      bounded_thermal_input_mk = MAX_HEAT_LOAD_MK;
    end else begin
      bounded_thermal_input_mk = thermal_input_milliK_i;
    end

    if (bounded_thermal_input_mk > HARVEST_TARGET_MK) begin
      thermal_delta_mk = bounded_thermal_input_mk - HARVEST_TARGET_MK;
    end else begin
      thermal_delta_mk = '0;
    end

    work_mult_ppm = exp10_multiplier_ppm(thermal_delta_mk, EXP_STEP_MK);
    loop_gain_ppm = nonlinear_loop_gain_ppm(thermal_delta_mk);

    eff_ppm = (64'(BASE_EFF_PPM) * work_mult_ppm) / ONE_PPM;
    eff_ppm = (eff_ppm * loop_gain_ppm) / ONE_PPM;

    if (eff_ppm > MAX_EFF_PPM) begin
      eff_ppm = MAX_EFF_PPM;
    end

    thermal_delta_milliK_o = activation_i ? thermal_delta_mk : '0;
    work_multiplier_ppm_o = activation_i ? work_mult_ppm : ONE_PPM;
    loop_gain_ppm_o = activation_i ? loop_gain_ppm : ONE_PPM;
    conversion_efficiency_ppm_o = activation_i ? logic'(eff_ppm[31:0]) : '0;

    entropy_gain_ppm_o = activation_i
      ? 16'(
          16'd1200
          + 16'(conversion_efficiency_ppm_o[31:16])
          + 16'(defect_density_i * 16'd7)
          + 16'(chakra_band_i * 16'd13)
          + 16'(cultivation_stage_i * 16'd11)
        )
      : 16'd0;
  end

endmodule
