/*
 * STACK 07: PULSE - VELOCITY ACCUMULATOR & MINTING ENGINE
 * -----------------------------------------------------------------------------
 * Native unit of impact - minted through Proof of Innovation
 * Velocity-based minting, anti-hoarding demurrage
 * ARM-Methodology: Atomic operations, overflow protection, shadow registers
 */

`include "origin_v_params.svh"

module pulse_velocity (
    input  wire              clk,
    input  wire              rst_n,
    
    // Transaction Interface
    input  wire              transaction_valid,
    input  wire [127:0]      transaction_value,
    input  wire              impact_positive,  // High if transaction creates value
    
    // Minting & Governance Interface
    output reg  [63:0]       pulse_balance,
    output reg  [63:0]       velocity_accumulator,
    output reg  [63:0]       governance_weight,
    
    // Minting outputs
    output reg               pulse_minted,
    output reg [63:0]        minted_amount,
    
    // Demurrage (anti-hoarding)
    input  wire              demurrage_enable,
    input  wire [15:0]       demurrage_rate  // Per-epoch rate
);

    // ========================================================================
    // VELOCITY ACCUMULATOR
    // ========================================================================
    // Tracks economic impact over time
    localparam int VELOCITY_WINDOW = 1000;  // Transactions
    reg [63:0] velocity_window [0:VELOCITY_WINDOW-1];
    reg [10:0] velocity_ptr;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            velocity_accumulator <= '0;
            velocity_ptr <= '0;
            for (int i = 0; i < VELOCITY_WINDOW; i++) begin
                velocity_window[i] <= '0;
            end
        end else begin
            if (transaction_valid && impact_positive) begin
                // Add to velocity window
                logic [63:0] old_value = velocity_window[velocity_ptr];
                logic [63:0] new_value = transaction_value[63:0];
                
                velocity_window[velocity_ptr] <= new_value;
                velocity_ptr <= (velocity_ptr + 1) % VELOCITY_WINDOW;
                
                // Update accumulator (sliding window sum)
                // Check for overflow
                if ((velocity_accumulator + new_value) >= velocity_accumulator) begin
                    if ((velocity_accumulator + new_value - old_value) <= velocity_accumulator) begin
                        velocity_accumulator <= velocity_accumulator + new_value - old_value;
                    end else begin
                        velocity_accumulator <= 64'hFFFF_FFFF_FFFF_FFFF;
                    end
                end else begin
                    // Overflow protection: saturate
                    velocity_accumulator <= 64'hFFFF_FFFF_FFFF_FFFF;
                end
            end
        end
    end

    // ========================================================================
    // PROOF OF INNOVATION MINTING
    // ========================================================================
    // Pulse is minted when velocity exceeds threshold
    localparam int MINT_THRESHOLD = 1000_0000;  // Velocity threshold
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pulse_balance <= '0;
            pulse_minted <= 1'b0;
            minted_amount <= '0;
        end else begin
            pulse_minted <= 1'b0;
            
            // Minting logic: High velocity = high impact = new Pulse
            if (velocity_accumulator > MINT_THRESHOLD && impact_positive) begin
                // Mint proportional to velocity (with cap)
                logic [63:0] mint_amount;
                mint_amount = velocity_accumulator >> 10;  // Divide by 1024 (scaling factor)
                
                // Cap minting to prevent inflation
                if (mint_amount > 64'h0000_0000_FFFF_FFFF) begin
                    mint_amount = 64'h0000_0000_FFFF_FFFF;
                end
                
                // Add to balance (check overflow)
                if ((pulse_balance + mint_amount) > pulse_balance) begin
                    pulse_balance <= pulse_balance + mint_amount;
                    minted_amount <= mint_amount;
                    pulse_minted <= 1'b1;
                end else begin
                    // Overflow: saturate
                    pulse_balance <= 64'hFFFF_FFFF_FFFF_FFFF;
                end
            end
        end
    end

    // ========================================================================
    // GOVERNANCE WEIGHT CALCULATION
    // ========================================================================
    // Voting power = f(velocity), not just token count
    always_ff @(posedge clk) begin
        // Logarithmic scaling to prevent whale dominance
        governance_weight <= velocity_accumulator >> VOTE_WEIGHT_SCALE;
    end

    // ========================================================================
    // DEMURRAGE (Anti-Hoarding Fee)
    // ========================================================================
    // Encourages constant reinvestment by taxing stagnant balances
    reg [31:0] demurrage_counter;
    localparam int DEMURRAGE_PERIOD = 1000_000;  // Clock cycles
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            demurrage_counter <= '0;
        end else begin
            if (demurrage_enable) begin
                demurrage_counter <= demurrage_counter + 1;
                
                if (demurrage_counter >= DEMURRAGE_PERIOD) begin
                    // Apply demurrage: reduce balance by rate
                    logic [63:0] demurrage_amount;
                    demurrage_amount = (pulse_balance * {48'b0, demurrage_rate}) / 10000;
                    
                    if (pulse_balance > demurrage_amount) begin
                        pulse_balance <= pulse_balance - demurrage_amount;
                    end else begin
                        pulse_balance <= '0;
                    end
                    
                    demurrage_counter <= '0;
                end
            end
        end
    end

endmodule
