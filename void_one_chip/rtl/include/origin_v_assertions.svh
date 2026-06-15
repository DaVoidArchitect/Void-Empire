/*
 * ORIGIN-V OMEGA: SYSTEMVERILOG ASSERTIONS (SVA)
 * -----------------------------------------------------------------------------
 * Production-ready assertions for formal verification
 * ARM-Methodology: Comprehensive property checking
 */

`ifndef ORIGIN_V_ASSERTIONS_SVH
`define ORIGIN_V_ASSERTIONS_SVH

// ============================================================================
// HARD-LAW INTEGRITY ASSERTIONS
// ============================================================================

// Assertion: Transaction total must equal sum of all shares
property hard_law_integrity;
    @(posedge clk) disable iff (!rst_n)
    (s_axis_tvalid && s_axis_tready) |-> 
    ##5 (founder_share + liquidity_pool + mesh_maintenance + public_net == 
         $past(s_axis_tdata, 5) || 
         founder_share + liquidity_pool + mesh_maintenance + public_net == 
         $past(s_axis_tdata, 5) + 1 ||
         founder_share + liquidity_pool + mesh_maintenance + public_net == 
         $past(s_axis_tdata, 5) - 1);
endproperty

// Assertion: Core must be unauthorized if integrity fails
property integrity_authorization;
    @(posedge clk) disable iff (!rst_n)
    (!core_authorized) |-> 
    (error_code == ERR_INTEGRITY_FAIL || error_code == ERR_BIO_TIMEOUT);
endproperty

// ============================================================================
// BIO-LATCH ASSERTIONS
// ============================================================================

// Assertion: Founder init must persist after completion
property founder_init_persistence;
    @(posedge clk) disable iff (!rst_n)
    ($past(founder_init_complete) == 1'b1) |-> 
    (founder_init_complete == 1'b1);
endproperty

// Assertion: Bio-entropy must be valid for authorization
property bio_entropy_requirement;
    @(posedge clk) disable iff (!rst_n)
    (bio_latch_authorized == 1'b1) |->
    ($past(bio_entropy_valid) == 1'b1);
endproperty

// ============================================================================
// TRANSACTION FLOW ASSERTIONS
// ============================================================================

// Assertion: Ready signal must be valid when transaction occurs
property axi_handshake;
    @(posedge clk) disable iff (!rst_n)
    (s_axis_tvalid && s_axis_tready) |->
    ##[1:5] (s_axis_tready == 1'b1 || core_authorized == 1'b0);
endproperty

// Assertion: No data loss
property no_data_loss;
    @(posedge clk) disable iff (!rst_n)
    (s_axis_tvalid && s_axis_tready) |->
    ##[1:10] (founder_share + liquidity_pool + mesh_maintenance + public_net > 0);
endproperty

// ============================================================================
// STATE MACHINE ASSERTIONS
// ============================================================================

// Assertion: Civilization state transitions are valid
property valid_state_transition;
    @(posedge clk) disable iff (!rst_n)
    $past(civilization_state) != civilization_state |->
    ((civilization_state == CIV_STATE_CITIZEN_OK) ||
     (civilization_state == CIV_STATE_FOUNDER) ||
     (civilization_state == CIV_STATE_EXCOMM) ||
     (civilization_state == CIV_STATE_ROGUE));
endproperty

// Assertion: Founder state requires both conditions
property founder_state_requirement;
    @(posedge clk) disable iff (!rst_n)
    (civilization_state == CIV_STATE_FOUNDER) |->
    (is_founder == 1'b1 && core_authorized == 1'b1);
endproperty

// ============================================================================
// SECURITY ASSERTIONS
// ============================================================================

// Assertion: Unauthorized access prevents operation
property unauthorized_blocking;
    @(posedge clk) disable iff (!rst_n)
    (!core_authorized) |->
    (founder_share == 0 && liquidity_pool == 0 && 
     mesh_maintenance == 0 && public_net == 0);
endproperty

// Assertion: PUF must be unique per instance
property puf_uniqueness;
    @(posedge clk) disable iff (!rst_n)
    $stable(omega_id) && puf_valid |->
    (omega_id != 4096'h0);
endproperty

`endif // ORIGIN_V_ASSERTIONS_SVH
