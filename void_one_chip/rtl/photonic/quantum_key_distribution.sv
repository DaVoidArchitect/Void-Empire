/*
 * QUANTUM KEY DISTRIBUTION (QKD) MODULE
 * -----------------------------------------------------------------------------
 * BB84 Protocol Implementation for Quantum-Secure Storage Keys
 * Quantum-Photonic Edition v3.0
 */

`include "origin_v_params.svh"
`include "origin_v_qphoton_params.svh"

module quantum_key_distribution #(
    parameter int KEY_BITS = QKD_KEY_BITS,
    parameter int BASE_BITS = QKD_BASE_BITS,
    parameter int ERROR_THRESHOLD = QKD_ERROR_THRESHOLD_PPM
)(
    input  wire                          clk,
    input  wire                          rst_n,
    input  wire                          qkd_initiate,
    
    // Quantum Channel (Photon Transmission)
    input  wire [QUBIT_COUNT-1:0]        quantum_photon_state,  // Photon quantum states
    input  wire [QUBIT_COUNT-1:0]        quantum_basis_choice,  // Measurement basis (0=Z, 1=X)
    input  wire                          quantum_photon_valid,
    
    // Output Quantum Key
    output reg  [KEY_BITS-1:0]           quantum_key,
    output reg                           quantum_key_valid,
    output reg                           quantum_key_secure,
    
    // QKD Status
    output reg  [15:0]                   qkd_error_rate_ppm,    // Quantum bit error rate
    output reg  [7:0]                    qkd_privacy_amplification_factor,
    output reg  [7:0]                    qkd_key_rate_hz        // Key generation rate
);

    // ========================================================================
    // BB84 QUANTUM KEY DISTRIBUTION PROTOCOL
    // ========================================================================
    // 1. Alice sends photons in random bases (Z or X)
    // 2. Bob measures in random bases
    // 3. Public discussion: Compare bases, keep matching bits
    // 4. Error estimation: Compare subset of bits
    // 5. Privacy amplification: Extract secure key
    
    // Phase 1: Raw Key Collection
    reg [BASE_BITS-1:0] raw_key_alice;      // Alice's transmitted bits
    reg [BASE_BITS-1:0] raw_key_bob;        // Bob's measured bits
    reg [BASE_BITS-1:0] basis_alice;        // Alice's basis choices
    reg [BASE_BITS-1:0] basis_bob;          // Bob's basis choices
    reg [BASE_BITS-1:0] matching_basis_mask; // Bits where bases match
    
    // Phase 2: Sifted Key
    reg [BASE_BITS-1:0] sifted_key;
    reg [15:0] sifted_key_count;
    
    // Phase 3: Error Estimation
    reg [BASE_BITS-1:0] error_test_bits;
    reg [15:0] error_count;
    reg [15:0] total_test_bits;
    
    // Phase 4: Privacy Amplification
    reg [KEY_BITS-1:0] privacy_amplified_key;
    
    // QKD State Machine
    typedef enum logic [3:0] {
        QKD_IDLE,
        QKD_COLLECT_RAW_KEY,
        QKD_SIFT_BASES,
        QKD_ESTIMATE_ERROR,
        QKD_PRIVACY_AMPLIFY,
        QKD_KEY_READY,
        QKD_ERROR_TOO_HIGH
    } qkd_state_e;
    
    qkd_state_e qkd_state;
    reg [31:0] qkd_counter;
    
    // ========================================================================
    // QUANTUM MEASUREMENT MODEL
    // ========================================================================
    // Photon in |0> or |1> (Z basis) or |+> or |-> (X basis)
    // Measurement collapses quantum state
    
    function automatic bit quantum_measure(
        input bit photon_state,      // Photon quantum state (0 or 1)
        input bit measurement_basis, // 0=Z basis, 1=X basis
        input bit transmitted_basis  // Alice's basis
    );
        bit measured_bit;
        
        if (measurement_basis == transmitted_basis) begin
            // Bases match: Measurement is deterministic
            measured_bit = photon_state;
        end else begin
            // Bases differ: Random measurement (50/50)
            // In real quantum: True randomness from quantum mechanics
            measured_bit = $random() % 2;
        end
        
        quantum_measure = measured_bit;
    endfunction
    
    // ========================================================================
    // PRIVACY AMPLIFICATION
    // ========================================================================
    // Universal hashing to extract secure key from partially secret raw key
    // Uses Toeplitz matrix multiplication
    
    function automatic [KEY_BITS-1:0] privacy_amplify(
        input [BASE_BITS-1:0] sifted_key_in,
        input int key_length
    );
        reg [KEY_BITS-1:0] amplified_key;
        reg [BASE_BITS-1:0] hash_matrix_row;
        
        amplified_key = '0;
        
        // Toeplitz hashing: Each output bit = XOR of selected input bits
        for (int i = 0; i < key_length && i < KEY_BITS; i++) begin
            // Generate Toeplitz row (pseudo-random selection)
            hash_matrix_row = (sifted_key_in << i) ^ (sifted_key_in >> (BASE_BITS - i));
            
            // Output bit = parity of selected input bits
            amplified_key[i] = ^hash_matrix_row;
        end
        
        privacy_amplify = amplified_key;
    endfunction
    
    // ========================================================================
    // QKD PROTOCOL STATE MACHINE
    // ========================================================================
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            qkd_state <= QKD_IDLE;
            raw_key_alice <= '0;
            raw_key_bob <= '0;
            basis_alice <= '0;
            basis_bob <= '0;
            sifted_key <= '0;
            sifted_key_count <= '0;
            error_test_bits <= '0;
            error_count <= '0;
            total_test_bits <= '0;
            quantum_key <= '0;
            quantum_key_valid <= 1'b0;
            quantum_key_secure <= 1'b0;
            qkd_counter <= '0;
            qkd_error_rate_ppm <= '0;
            qkd_privacy_amplification_factor <= 8'h0;
            qkd_key_rate_hz <= 8'h0;
        end else begin
            case (qkd_state)
                QKD_IDLE: begin
                    if (qkd_initiate) begin
                        qkd_state <= QKD_COLLECT_RAW_KEY;
                        qkd_counter <= '0;
                    end
                end
                
                QKD_COLLECT_RAW_KEY: begin
                    // Collect quantum photons
                    if (quantum_photon_valid) begin
                        // Store Alice's transmission (from quantum channel)
                        raw_key_alice[qkd_counter[7:0]] <= quantum_photon_state[0];
                        basis_alice[qkd_counter[7:0]] <= quantum_basis_choice[0];
                        
                        // Bob's measurement (simulated here, real system: separate node)
                        raw_key_bob[qkd_counter[7:0]] <= quantum_measure(
                            quantum_photon_state[0],
                            quantum_basis_choice[0],  // Bob's basis (random)
                            basis_alice[qkd_counter[7:0]]  // Alice's basis
                        );
                        basis_bob[qkd_counter[7:0]] <= quantum_basis_choice[0];
                        
                        qkd_counter <= qkd_counter + 1;
                        
                        if (qkd_counter >= BASE_BITS - 1) begin
                            qkd_state <= QKD_SIFT_BASES;
                            qkd_counter <= '0;
                        end
                    end
                end
                
                QKD_SIFT_BASES: begin
                    // Public discussion: Compare bases, keep matching bits
                    matching_basis_mask[qkd_counter[7:0]] = 
                        (basis_alice[qkd_counter[7:0]] == basis_bob[qkd_counter[7:0]]);
                    
                    if (matching_basis_mask[qkd_counter[7:0]]) begin
                        sifted_key[sifted_key_count] <= raw_key_bob[qkd_counter[7:0]];
                        sifted_key_count <= sifted_key_count + 1;
                    end
                    
                    qkd_counter <= qkd_counter + 1;
                    
                    if (qkd_counter >= BASE_BITS - 1) begin
                        qkd_state <= QKD_ESTIMATE_ERROR;
                        qkd_counter <= '0;
                    end
                end
                
                QKD_ESTIMATE_ERROR: begin
                    // Estimate quantum bit error rate (QBER)
                    if (matching_basis_mask[qkd_counter[7:0]]) begin
                        if (raw_key_alice[qkd_counter[7:0]] != raw_key_bob[qkd_counter[7:0]]) begin
                            error_count <= error_count + 1;
                        end
                        total_test_bits <= total_test_bits + 1;
                    end
                    
                    qkd_counter <= qkd_counter + 1;
                    
                    if (qkd_counter >= BASE_BITS - 1) begin
                        // Calculate error rate
                        if (total_test_bits > 0) begin
                            qkd_error_rate_ppm <= (error_count * 1000000) / total_test_bits;
                        end
                        
                        // Check error threshold
                        if (qkd_error_rate_ppm < ERROR_THRESHOLD) begin
                            qkd_state <= QKD_PRIVACY_AMPLIFY;
                        end else begin
                            qkd_state <= QKD_ERROR_TOO_HIGH;
                        end
                        qkd_counter <= '0;
                    end
                end
                
                QKD_PRIVACY_AMPLIFY: begin
                    // Privacy amplification to extract secure key
                    quantum_key <= privacy_amplify(sifted_key, KEY_BITS);
                    
                    // Calculate privacy amplification factor
                    if (sifted_key_count > 0) begin
                        qkd_privacy_amplification_factor <= (sifted_key_count * 100) / BASE_BITS;
                    end
                    
                    quantum_key_valid <= 1'b1;
                    quantum_key_secure <= 1'b1;
                    qkd_state <= QKD_KEY_READY;
                    
                    // Calculate key generation rate (simplified)
                    qkd_key_rate_hz <= 8'd100;  // 100 Hz (placeholder)
                end
                
                QKD_KEY_READY: begin
                    // Key ready for use
                    // Maintain key until refresh requested
                    if (!qkd_initiate) begin
                        // Key can be refreshed
                        qkd_state <= QKD_IDLE;
                        quantum_key_valid <= 1'b0;
                        quantum_key_secure <= 1'b0;
                    end
                end
                
                QKD_ERROR_TOO_HIGH: begin
                    // Error rate too high: Eavesdropper detected or channel noise
                    quantum_key <= '0;
                    quantum_key_valid <= 1'b0;
                    quantum_key_secure <= 1'b0;
                    
                    // Reset for retry
                    if (!qkd_initiate) begin
                        qkd_state <= QKD_IDLE;
                        error_count <= '0;
                        total_test_bits <= '0;
                    end
                end
                
                default: qkd_state <= QKD_IDLE;
            endcase
        end
    end

endmodule
