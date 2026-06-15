/*
 * TESTBENCH: SMF UNIT (Stack 02)
 * -----------------------------------------------------------------------------
 * Verification of Hard-Law economic shunt
 */

`include "origin_v_params.svh"

module tb_smf_unit;

    parameter CLK_PERIOD = 10;

    reg clk;
    reg rst_n;
    reg transaction_valid;
    reg [127:0] transaction_value;
    
    wire [127:0] founder_share;
    wire [127:0] liquidity_pool;
    wire [127:0] mesh_maintenance;
    wire [127:0] public_net;
    wire integrity_pass;
    wire core_authorized;
    wire [7:0] error_code;

    smf_unit dut (
        .clk(clk),
        .rst_n(rst_n),
        .transaction_valid(transaction_valid),
        .transaction_value(transaction_value),
        .founder_share(founder_share),
        .liquidity_pool(liquidity_pool),
        .mesh_maintenance(mesh_maintenance),
        .public_net(public_net),
        .integrity_pass(integrity_pass),
        .core_authorized(core_authorized),
        .error_code(error_code)
    );

    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    initial begin
        $display("SMF Unit Testbench");
        
        rst_n = 0;
        transaction_valid = 0;
        transaction_value = 0;
        
        #(CLK_PERIOD * 10);
        rst_n = 1;
        #(CLK_PERIOD * 5);
        
        // Test 1: 1000 units
        transaction_value = 128'd10000;  // 100.00 in fixed-point
        transaction_valid = 1;
        
        #(CLK_PERIOD * 5);
        transaction_valid = 0;
        
        #(CLK_PERIOD * 10);
        
        $display("Transaction: %0d", transaction_value);
        $display("Founder (1%%): %0d", founder_share);
        $display("Liquidity (3%%): %0d", liquidity_pool);
        $display("Mesh (2.18%%): %0d", mesh_maintenance);
        $display("Public (93.82%%): %0d", public_net);
        $display("Total: %0d", founder_share + liquidity_pool + mesh_maintenance + public_net);
        $display("Integrity: %b, Authorized: %b", integrity_pass, core_authorized);
        
        if (founder_share == 100 && liquidity_pool == 300 && 
            (founder_share + liquidity_pool + mesh_maintenance + public_net == transaction_value)) begin
            $display("TEST PASSED");
        end else begin
            $display("TEST FAILED");
        end
        
        #(CLK_PERIOD * 10);
        $finish;
    end

endmodule
