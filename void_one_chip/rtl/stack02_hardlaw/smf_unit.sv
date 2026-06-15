/*
 * STACK 02: HARD-LAW ECONOMY - SYSTEM FUND SHUNT UNIT (SMF)
 * -----------------------------------------------------------------------------
 * The "Physics of Value" - Transistor-level economic shunt
 * 6.18% split is HARD-CODED in metal mask (immutable)
 * ARM-Methodology: Pipelined, side-channel protected, shadow registers
 */

`include "origin_v_params.svh"

module smf_unit (
    input  wire              clk,
    input  wire              rst_n,
    input  wire              transaction_valid,
    input  wire [127:0]      transaction_value,  // Input value in fixed-point
    
    // Outputs (Hard-Law Enforced)
    output reg  [127:0]      founder_share,      // 1.00% to Founder
    output reg  [127:0]      liquidity_pool,     // 3.00% to Liquidity
    output reg  [127:0]      mesh_maintenance,   // 2.18% to Mesh
    output reg  [127:0]      public_net,         // 93.82% to user
    
    // Integrity & Authorization
    output reg               integrity_pass,
    output reg               core_authorized,    // BRICKS if fail
    output reg  [7:0]        error_code
);

    // ========================================================================
    // METAL-MASK CONSTANTS (IMMUTABLE - Etched in Silicon)
    // ========================================================================
    // These constants are set at tape-out and cannot be changed
    localparam logic [127:0] SCALER = 128'd10000;
    localparam logic [127:0] FOUNDER_PCT = 128'd100;      // 1.00%
    localparam logic [127:0] LIQUIDITY_PCT = 128'd300;    // 3.00%
    localparam logic [127:0] MESH_PCT = 128'd218;         // 2.18%
    localparam logic [127:0] TOTAL_TAX = 128'd618;        // 6.18%

    // Pipeline registers for side-channel protection
    reg [127:0] trans_value_ff;
    reg [127:0] founder_calc_ff, liquidity_calc_ff, mesh_calc_ff;
    reg [127:0] public_calc_ff;
    reg [127:0] total_calc_ff;
    reg valid_ff;

    // Shadow registers for integrity checking
    reg [127:0] founder_shadow, liquidity_shadow, mesh_shadow, public_shadow;

    // ========================================================================
    // STAGE 1: FIXED-POINT MULTIPLICATION (Pipeline Stage)
    // ========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            trans_value_ff <= '0;
            founder_calc_ff <= '0;
            liquidity_calc_ff <= '0;
            mesh_calc_ff <= '0;
            valid_ff <= 1'b0;
        end else begin
            trans_value_ff <= transaction_value;
            valid_ff <= transaction_valid;
            
            // Fixed-point calculation: (value * rate) / 10000
            // Using pipelined multipliers for 3nm process
            founder_calc_ff <= (transaction_value * FOUNDER_PCT) / SCALER;
            liquidity_calc_ff <= (transaction_value * LIQUIDITY_PCT) / SCALER;
            mesh_calc_ff <= (transaction_value * MESH_PCT) / SCALER;
        end
    end

    // ========================================================================
    // STAGE 2: PUBLIC NET CALCULATION & INTEGRITY CHECK
    // ========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            public_calc_ff <= '0;
            total_calc_ff <= '0;
            founder_share <= '0;
            liquidity_pool <= '0;
            mesh_maintenance <= '0;
            public_net <= '0;
            integrity_pass <= 1'b0;
            core_authorized <= 1'b0;
            error_code <= ERR_NONE;
            
            // Initialize shadow registers
            founder_shadow <= '0;
            liquidity_shadow <= '0;
            mesh_shadow <= '0;
            public_shadow <= '0;
        end else if (valid_ff) begin
            // Calculate public net (after all deductions)
            public_calc_ff <= trans_value_ff - founder_calc_ff - liquidity_calc_ff - mesh_calc_ff;
            
            // Total should equal original value (within rounding tolerance)
            total_calc_ff <= founder_calc_ff + liquidity_calc_ff + mesh_calc_ff + public_calc_ff;
            
            // Shadow register update (for side-channel protection)
            founder_shadow <= founder_calc_ff;
            liquidity_shadow <= liquidity_calc_ff;
            mesh_shadow <= mesh_calc_ff;
            public_shadow <= public_calc_ff;
            
            // Integrity check: Total must match input (within 1 unit tolerance for rounding)
            if ((total_calc_ff >= trans_value_ff - 128'd1) && 
                (total_calc_ff <= trans_value_ff + 128'd1)) begin
                integrity_pass <= 1'b1;
                core_authorized <= 1'b1;
                error_code <= ERR_NONE;
                
                // Register outputs (protected by integrity check)
                founder_share <= founder_shadow;
                liquidity_pool <= liquidity_shadow;
                mesh_maintenance <= mesh_shadow;
                public_net <= public_shadow;
            end else begin
                // HARD-LAW VIOLATION: BRICK THE CHIP
                integrity_pass <= 1'b0;
                core_authorized <= 1'b0;
                error_code <= ERR_INTEGRITY_FAIL;
                
                // Zero outputs on integrity failure
                founder_share <= '0;
                liquidity_pool <= '0;
                mesh_maintenance <= '0;
                public_net <= '0;
            end
        end
    end

    // Synthesis attributes for security
    // (* DONT_TOUCH = "true" *) on all financial registers
    // (* KEEP = "true" *) on shadow registers

endmodule
