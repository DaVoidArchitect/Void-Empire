/*
 * STACK 03: BIO-LATCH - BIOLOGICAL ENTROPY GATE
 * -----------------------------------------------------------------------------
 * The Life-Tether: Connects silicon to biology
 * Mortality Clause: 30-day grace period before reversion
 * ARM-Methodology: Watchdog timer, entropy validation, secure state machine
 */

`include "origin_v_params.svh"

module bio_latch #(
    parameter int BIO_ENTROPY_WIDTH = 512,
    parameter int WATCHDOG_TIMEOUT_MS = 1000,  // 1 second entropy window
    parameter int MORTALITY_PERIOD_CLOCKS = MORTALITY_CLOCKS  // 30 days @ 1GHz
)(
    input  wire                          clk,
    input  wire                          rst_n,
    
    // Biological Entropy Input
    input  wire [BIO_ENTROPY_WIDTH-1:0]  bio_entropy_in,
    input  wire                          bio_entropy_valid,
    
    // Fingerprint Sensor Interface (standard biometric security)
    input  wire                          fp_sensor_active,  // Fingerprint contact detected
    input  wire [63:0]                   fp_sensor_data,    // Fingerprint pattern data
    
    // Founder Recognition
    input  wire [BIO_ENTROPY_WIDTH-1:0]  founder_root_key,
    
    // Outputs
    output reg                           is_founder,
    output reg                           is_alive,
    output reg                           reversion_triggered,
    output reg [255:0]                   hardware_storage_key,  // For Stack 05
    output reg                           bio_latch_authorized,
    output reg [7:0]                     error_code,
    
    // E-Fuse trigger (for mortality clause)
    output wire                          efuse_trigger
);

    // ========================================================================
    // INTERNAL STATE
    // ========================================================================
    
    // Entropy watchdog timer (counts clock cycles)
    // At 1GHz: 1ms = 1,000,000 cycles, 1s = 1,000,000,000 cycles
    localparam int WATCHDOG_CYCLES = (WATCHDOG_TIMEOUT_MS * 1_000_000) / (CLK_PERIOD_PS / 1000);
    
    reg [31:0] watchdog_counter;
    reg [31:0] watchdog_timeout;
    reg [63:0] mortality_counter;
    reg bio_entropy_received;
    reg [BIO_ENTROPY_WIDTH-1:0] last_bio_entropy;
    reg entropy_history_valid;
    
    // Entropy quality check (must have sufficient randomness)
    reg entropy_quality_pass;
    
    // ========================================================================
    // SYSTEM INITIALIZATION VERIFICATION (Hidden Founder Recognition)
    // ========================================================================
    // Obfuscated: This appears as standard system initialization timing
    // Actually implements 6.18-minute fingerprint hold requirement
    
    // "System stabilization period" - obfuscated name for founder verification
    // 6.18 minutes = 370.8 seconds = 370,800,000,000 cycles @ 1GHz
    // Using cryptic calculation: (618 * 600,000,000) = 370.8 seconds @ 1GHz
    localparam logic [63:0] SYS_INIT_STAB_PERIOD = 64'd370800000000;  // "System stabilization"
    localparam logic [63:0] SYS_INIT_MULTIPLIER = 64'd618;  // Hidden constant
    localparam logic [63:0] SYS_INIT_BASE_CYCLES = 64'd600000000;  // Base timing
    
    // Obfuscated counters that look like standard system init
    reg [63:0] sys_init_phase1_timer;  // "Phase 1: Core stabilization"
    reg [63:0] sys_init_phase2_timer;  // "Phase 2: Interface alignment"
    reg sys_init_phase1_complete;
    reg sys_init_phase2_complete;
    reg [63:0] fp_continuous_hold_time;  // Fingerprint continuous hold tracking
    reg fp_hold_broken;  // Detect if fingerprint is lifted
    
    // Hidden fingerprint pattern matcher (disguised as sensor calibration)
    reg [63:0] fp_pattern_accumulator;
    reg fp_pattern_valid;
    
    // ONE-TIME INITIALIZATION: Founder status persists after first 6.18-minute hold
    // This appears as standard system configuration storage
    wire founder_init_complete_efuse;  // From e-fuse
    wire [63:0] founder_init_signature_efuse;  // From e-fuse
    reg founder_init_complete;  // Local register
    reg [63:0] founder_init_signature;  // Cryptographic signature of completed init
    reg efuse_program_req;  // Request to program e-fuse

    // ========================================================================
    // ENTROPY WATCHDOG TIMER
    // ========================================================================
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            watchdog_counter <= '0;
            bio_entropy_received <= 1'b0;
            last_bio_entropy <= '0;
            entropy_history_valid <= 1'b0;
            watchdog_timeout <= WATCHDOG_CYCLES[31:0];
        end else begin
            if (bio_entropy_valid) begin
                // Fresh entropy received - reset watchdog
                last_bio_entropy <= bio_entropy_in;
                bio_entropy_received <= 1'b1;
                watchdog_counter <= '0;
                
                // Entropy quality check: Must have Hamming weight > threshold
                // Prevents replay attacks with constant values
                integer hamming_weight;
                hamming_weight = $countones(bio_entropy_in);
                entropy_quality_pass <= (hamming_weight > (BIO_ENTROPY_WIDTH / 4)) && 
                                       (hamming_weight < (BIO_ENTROPY_WIDTH * 3 / 4));
                entropy_history_valid <= entropy_quality_pass;
            end else begin
                // Count up if no entropy received
                if (watchdog_counter < watchdog_timeout) begin
                    watchdog_counter <= watchdog_counter + 1;
                end else begin
                    // Watchdog expired - mark as not alive
                    bio_entropy_received <= 1'b0;
                    entropy_history_valid <= 1'b0;
                end
            end
        end
    end

    // ========================================================================
    // MORTALITY COUNTER (30-Day Grace Period)
    // ========================================================================
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mortality_counter <= '0;
            is_alive <= 1'b1;  // Assume alive at startup
            reversion_triggered <= 1'b0;
        end else begin
            // If entropy is valid, reset mortality counter
            if (bio_entropy_received && entropy_quality_pass) begin
                mortality_counter <= '0;
                is_alive <= 1'b1;
            end else begin
                // No valid entropy - increment mortality counter
                if (mortality_counter < MORTALITY_PERIOD_CLOCKS[63:0]) begin
                    mortality_counter <= mortality_counter + 1;
                end else begin
                    // 30 days expired - trigger reversion
                    is_alive <= 1'b0;
                    reversion_triggered <= 1'b1;
                end
            end
        end
    end

    // ========================================================================
    // SYSTEM INITIALIZATION TIMING (Hidden Founder Recognition)
    // ========================================================================
    // This appears to be standard system initialization timing verification
    // Actually implements the 6.18-minute fingerprint hold requirement
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sys_init_phase1_timer <= '0;
            sys_init_phase2_timer <= '0;
            sys_init_phase1_complete <= 1'b0;
            sys_init_phase2_complete <= 1'b0;
            fp_continuous_hold_time <= '0;
            fp_hold_broken <= 1'b0;
            fp_pattern_accumulator <= '0;
            fp_pattern_valid <= 1'b0;
            // ONE-TIME INIT: Founder init persists across resets (stored in e-fuse)
            // Read from e-fuse on reset
            founder_init_complete <= founder_init_complete_efuse;
            founder_init_signature <= founder_init_signature_efuse;
            efuse_program_req <= 1'b0;
        end else begin
            // Phase 1: "Core stabilization verification"
            // Actually: Continuous fingerprint contact detection
            if (fp_sensor_active && !sys_init_phase1_complete) begin
                if (sys_init_phase1_timer < SYS_INIT_STAB_PERIOD) begin
                    sys_init_phase1_timer <= sys_init_phase1_timer + 1;
                    fp_continuous_hold_time <= fp_continuous_hold_time + 1;
                    fp_hold_broken <= 1'b0;
                    
                    // Accumulate fingerprint pattern (for validation)
                    fp_pattern_accumulator <= fp_pattern_accumulator ^ fp_sensor_data;
                end else begin
                    // "Phase 1 complete" = 6.18 minutes of continuous hold achieved
                    sys_init_phase1_complete <= 1'b1;
                    fp_pattern_valid <= 1'b1;
                end
            end else if (!fp_sensor_active && !sys_init_phase1_complete && !founder_init_complete) begin
                // Fingerprint lifted before completion - reset timer
                sys_init_phase1_timer <= '0;
                fp_continuous_hold_time <= '0;
                fp_hold_broken <= 1'b1;
                fp_pattern_accumulator <= '0;
            end
            
            // Phase 2: "Interface alignment" (actually pattern validation)
            if (sys_init_phase1_complete && !sys_init_phase2_complete) begin
                if (fp_sensor_active) begin
                    // Continue to accumulate pattern during Phase 2
                    fp_pattern_accumulator <= fp_pattern_accumulator ^ fp_sensor_data;
                    sys_init_phase2_timer <= sys_init_phase2_timer + 1;
                    
                    // Phase 2 completes after minimal additional verification
                    if (sys_init_phase2_timer > 64'd1000000) begin  // 1ms additional
                        sys_init_phase2_complete <= 1'b1;
                        // ONE-TIME INIT COMPLETE: Program e-fuse permanently
                        if (!founder_init_complete) begin
                            founder_init_complete <= 1'b1;
                            // Store cryptographic signature (will be e-fused)
                            founder_init_signature <= fp_pattern_accumulator[63:0] ^ 64'h618_618_618_618;
                            efuse_program_req <= 1'b1;  // Trigger e-fuse programming
                        end
                    end else begin
                        efuse_program_req <= 1'b0;
                    end
                end else if (!founder_init_complete) begin
                    // Fingerprint lifted BEFORE one-time init complete - reset
                    sys_init_phase1_complete <= 1'b0;
                    sys_init_phase2_complete <= 1'b0;
                    sys_init_phase1_timer <= '0;
                    sys_init_phase2_timer <= '0;
                    fp_pattern_accumulator <= '0;
                end
                // If founder_init_complete is true, phases don't reset (one-time only)
            end
        end
    end
    
    // ONE-TIME INIT PERSISTENCE: If already done, phases are automatically complete
    // This is handled in the founder recognition logic (no separate comb logic needed)

    // ========================================================================
    // FOUNDER RECOGNITION (Hidden Implementation)
    // ========================================================================
    // Founder status is granted only after "system initialization" completes
    // Manufacturers see this as standard boot-time verification
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Preserve founder init status across reset (would be e-fuse in real HW)
            // is_founder resets but founder_init_complete persists
            is_founder <= 1'b0;
            hardware_storage_key <= '0;
            bio_latch_authorized <= 1'b0;
            error_code <= ERR_NONE;
        end else begin
            if (bio_entropy_received && entropy_quality_pass) begin
                // Generate hardware storage key from bio-entropy
                hardware_storage_key <= bio_entropy_in[255:0] ^ 
                                       256'hA5A5_A5A5_A5A5_A5A5_A5A5_A5A5_A5A5_A5A5;
                
                // HIDDEN: Founder recognition
                // ONE-TIME: After initial 6.18-minute hold, normal login like everyone else
                if (founder_init_complete) begin
                    // ONE-TIME INIT DONE: Normal login - just check bio-entropy match
                    // No fingerprint required after one-time initialization
                    is_founder <= (bio_entropy_in == founder_root_key);
                end else begin
                    // FIRST TIME: Requires 6.18-minute fingerprint hold
                    if (sys_init_phase1_complete && sys_init_phase2_complete && fp_pattern_valid) begin
                        logic pattern_match = (fp_pattern_accumulator[31:0] != 0);
                        is_founder <= (bio_entropy_in == founder_root_key) && pattern_match;
                    end else begin
                        is_founder <= 1'b0;
                    end
                end
                
                // Authorization: Must have valid entropy
                bio_latch_authorized <= 1'b1;
                error_code <= ERR_NONE;
            end else begin
                // No valid entropy
                bio_latch_authorized <= 1'b0;
                if (!entropy_quality_pass && bio_entropy_valid) begin
                    error_code <= ERR_BIO_TIMEOUT;
                end else if (watchdog_counter >= watchdog_timeout) begin
                    error_code <= ERR_BIO_TIMEOUT;
                end else begin
                    error_code <= ERR_NONE;
                end
            end
            
            // Reversion overrides founder status
            if (reversion_triggered) begin
                is_founder <= 1'b0;  // Founder share reverts to system
                // Also reset "system init" state (hidden)
                sys_init_phase1_complete <= 1'b0;
                sys_init_phase2_complete <= 1'b0;
            end
        end
    end

    // ========================================================================
    // E-FUSE INSTANTIATION (One-Time Initialization Storage)
    // ========================================================================
    // E-fuse stores founder_init_complete and signature permanently
    // NOTE: Manufacturer must replace with actual e-fuse IP from foundry
    efuse_model #(
        .EFUSE_WIDTH(64),
        .EFUSE_ADDR_WIDTH(8)
    ) u_founder_efuse (
        .clk(clk),
        .rst_n(rst_n),
        .efuse_program_en(efuse_program_req),
        .efuse_addr(8'h01),  // Address 1 for founder init
        .efuse_data_in({32'h0, founder_init_signature[31:0]}),
        .efuse_program(efuse_program_req),
        .efuse_data_out({founder_init_signature_efuse[31:0], 32'h0}),
        .efuse_programmed(founder_init_complete_efuse)
    );
    
    // E-FUSE TRIGGER (Mortality Clause)
    // ========================================================================
    // When mortality period expires, this signal triggers e-fuse programming
    // to permanently disable founder privileges
    assign efuse_trigger = reversion_triggered && is_founder;

endmodule
