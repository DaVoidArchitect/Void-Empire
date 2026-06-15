/*
 * E-FUSE MODEL - For One-Time Initialization Storage
 * -----------------------------------------------------------------------------
 * This is a model for simulation. Real hardware requires actual e-fuse IP.
 * Manufacturer must integrate foundry-provided e-fuse IP core.
 */

module efuse_model #(
    parameter int EFUSE_WIDTH = 64,
    parameter int EFUSE_ADDR_WIDTH = 8
)(
    input  wire                          clk,
    input  wire                          rst_n,
    
    // E-Fuse Interface
    input  wire                          efuse_program_en,  // One-time program enable
    input  wire [EFUSE_ADDR_WIDTH-1:0]  efuse_addr,
    input  wire [EFUSE_WIDTH-1:0]       efuse_data_in,
    input  wire                          efuse_program,     // Program pulse
    
    // Read Interface
    output reg  [EFUSE_WIDTH-1:0]       efuse_data_out,
    output reg                          efuse_programmed    // Indicates if programmed
);

    // E-Fuse Storage (in real HW: one-time programmable)
    reg [EFUSE_WIDTH-1:0] efuse_storage [0:255];  // 256 e-fuse words
    reg [255:0] efuse_programmed_flags;  // Track which addresses are programmed
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // E-fuses are non-volatile - they persist across reset
            // In simulation: preserve state
            // In real HW: stored in physical e-fuse cells
            efuse_data_out <= efuse_storage[efuse_addr];
            efuse_programmed <= efuse_programmed_flags[efuse_addr];
        end else begin
            // Read operation (always available)
            efuse_data_out <= efuse_storage[efuse_addr];
            efuse_programmed <= efuse_programmed_flags[efuse_addr];
            
            // Program operation (one-time only)
            if (efuse_program_en && efuse_program && !efuse_programmed_flags[efuse_addr]) begin
                // One-time programming - cannot be erased
                efuse_storage[efuse_addr] <= efuse_data_in;
                efuse_programmed_flags[efuse_addr] <= 1'b1;
            end
            // If already programmed, ignore program attempts (one-time only)
        end
    end

endmodule
