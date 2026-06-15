/*
 * FRACTAL H-TREE PHOTONIC CLOCK DISTRIBUTION
 * -----------------------------------------------------------------------------
 * Self-Similar H-Tree Optical Clock Network
 * Ensures identical path lengths from root to all 1024 leaves
 * Quantum-Photonic Edition v3.0
 */

`include "origin_v_params.svh"
`include "origin_v_qphoton_params.svh"

module fractal_photonic_clock_tree #(
    parameter int TREE_LEVELS = 10,  // 2^10 = 1024 leaves
    parameter int FANOUT = 4,        // H-tree fanout (4 branches)
    parameter int NUM_CORES = 1024,  // Number of cores to distribute clock to
    parameter real BASE_SEGMENT_UM = 100.0
)(
    input  wire                      clk_photonic_in,     // Optical clock input
    input  wire                      clk_enable,          // Clock enable
    
    output wire [NUM_CORES-1:0]      clk_photonic_out,    // Clock to each core
    output wire                      clk_tree_locked,     // Clock tree locked
    
    // Photonic status
    output wire [7:0]                clock_power_level,   // Optical power per branch
    output wire [7:0]                clock_skew_ps        // Measured skew (ps)
);

    // ========================================================================
    // FRACTAL H-TREE STRUCTURE
    // ========================================================================
    // Recursive H-tree: Each level splits into 4 branches (2x2 grid)
    // Level 0: Root (1 node)
    // Level 1: 4 nodes
    // Level 2: 16 nodes
    // ...
    // Level 10: 1024 leaves (cores)
    
    localparam int NODES_PER_LEVEL [0:TREE_LEVELS] = '{1, 4, 16, 64, 256, 1024, 4096, 16384, 65536, 262144, 1048576};
    
    // H-tree nodes: [level][node_index]
    reg [TREE_LEVELS-1:0] photonic_clock [0:NUM_CORES-1];
    reg [TREE_LEVELS-1:0] clock_delay_stages [0:NUM_CORES-1];
    
    // Optical power distribution (each split reduces power by 3dB)
    reg [15:0] optical_power_level [0:TREE_LEVELS];  // Power level per tree level
    reg tree_locked;
    
    // ========================================================================
    // FRACTAL SEGMENT LENGTH CALCULATION
    // ========================================================================
    // Each H-tree segment length = BASE_SEGMENT_UM * (FRACTAL_SCALE_FACTOR ^ level)
    // This ensures self-similar structure at all scales
    
    function automatic real fractal_segment_length(int level);
        real length;
        length = BASE_SEGMENT_UM;
        for (int i = 0; i < level; i++) begin
            length = length * FRACTAL_SCALE_FACTOR;
        end
        fractal_segment_length = length;
    endfunction
    
    // ========================================================================
    // OPTICAL CLOCK PROPAGATION
    // ========================================================================
    // Model optical delay through waveguides
    // Delay = (segment_length_um * refractive_index) / (speed_of_light_um_per_ps)
    // refractive_index_si ~ 3.48, c ~ 300 um/ps
    // Delay per segment ~ (length_um * 3.48) / 300 ps
    
    localparam real REFRACTIVE_INDEX_SI = 3.48;
    localparam real SPEED_OF_LIGHT_UM_PER_PS = 300.0;
    
    function automatic int optical_delay_ps(int level);
        real segment_length;
        real delay;
        segment_length = fractal_segment_length(level);
        delay = (segment_length * REFRACTIVE_INDEX_SI) / SPEED_OF_LIGHT_UM_PER_PS;
        optical_delay_ps = int'(delay);
    endfunction
    
    // ========================================================================
    // H-TREE ROUTING FUNCTION
    // ========================================================================
    // Maps core index to H-tree path (level-by-level routing)
    // Each level chooses one of 4 branches: 00, 01, 10, 11
    
    function automatic [TREE_LEVELS*2-1:0] get_htree_path(int core_index);
        reg [TREE_LEVELS*2-1:0] path;
        int temp_index;
        temp_index = core_index;
        
        for (int level = TREE_LEVELS-1; level >= 0; level--) begin
            path[level*2+1:level*2] = temp_index % FANOUT;
            temp_index = temp_index / FANOUT;
        end
        
        get_htree_path = path;
    endfunction
    
    // ========================================================================
    // CLOCK TREE GENERATION
    // ========================================================================
    
    genvar core_idx;
    generate
        for (core_idx = 0; core_idx < NUM_CORES; core_idx++) begin : gen_clock_tree
            // Calculate path for this core
            wire [TREE_LEVELS*2-1:0] core_path;
            assign core_path = get_htree_path(core_idx);
            
            // Build clock path through tree levels
            reg [TREE_LEVELS-1:0] clk_stage [0:TREE_LEVELS];
            
            // Root
            always_ff @(posedge clk_photonic_in or negedge clk_enable) begin
                if (!clk_enable) begin
                    clk_stage[0] <= 1'b0;
                end else begin
                    clk_stage[0] <= clk_photonic_in;
                end
            end
            
            // Propagate through tree levels
            for (genvar level = 1; level <= TREE_LEVELS; level++) begin : gen_tree_level
                always_ff @(posedge clk_photonic_in) begin
                    if (clk_enable) begin
                        // Select branch based on path
                        // Delay model: Simulate optical propagation delay
                        clk_stage[level] <= #(optical_delay_ps(level-1)) clk_stage[level-1];
                    end else begin
                        clk_stage[level] <= 1'b0;
                    end
                end
            end
            
            // Output clock for this core
            assign clk_photonic_out[core_idx] = clk_stage[TREE_LEVELS];
        end
    endgenerate
    
    // ========================================================================
    // CLOCK SKEW MEASUREMENT
    // ========================================================================
    // Measure maximum clock skew across all cores
    
    reg [7:0] max_skew_ps;
    reg [NUM_CORES-1:0] clock_edge_detected;
    reg [31:0] clock_edge_time [0:NUM_CORES-1];
    reg [31:0] earliest_edge, latest_edge;
    
    always_ff @(posedge clk_photonic_in) begin
        for (int i = 0; i < NUM_CORES; i++) begin
            if (clk_photonic_out[i]) begin
                clock_edge_detected[i] <= 1'b1;
                clock_edge_time[i] <= $time;
            end
        end
        
        // Find earliest and latest edge
        earliest_edge = clock_edge_time[0];
        latest_edge = clock_edge_time[0];
        for (int i = 1; i < NUM_CORES; i++) begin
            if (clock_edge_time[i] < earliest_edge) earliest_edge = clock_edge_time[i];
            if (clock_edge_time[i] > latest_edge) latest_edge = clock_edge_time[i];
        end
        
        max_skew_ps <= (latest_edge - earliest_edge) / 1000; // Convert to ps
    end
    
    assign clock_skew_ps = max_skew_ps;
    
    // ========================================================================
    // OPTICAL POWER BUDGET
    // ========================================================================
    // Each H-tree split: Power reduced by 3dB (50% per branch)
    // Level 0: 100% power
    // Level 1: 25% power per branch
    // Level 2: 6.25% power per branch
    // ...
    
    always_comb begin
        optical_power_level[0] = 16'hFFFF;  // 100% at root
        
        for (int level = 1; level <= TREE_LEVELS; level++) begin
            // Power = 100% / (4^level)
            optical_power_level[level] = 16'hFFFF >> (level * 2);
        end
    end
    
    assign clock_power_level = optical_power_level[TREE_LEVELS][15:8];
    
    // ========================================================================
    // CLOCK TREE LOCK
    // ========================================================================
    // Lock when all cores receive stable clock
    
    reg [15:0] lock_counter;
    always_ff @(posedge clk_photonic_in) begin
        if (clk_enable) begin
            if (&clk_photonic_out) begin
                if (lock_counter < 16'hFFFF) begin
                    lock_counter <= lock_counter + 1;
                end else begin
                    tree_locked <= 1'b1;
                end
            end else begin
                lock_counter <= '0;
                tree_locked <= 1'b0;
            end
        end else begin
            tree_locked <= 1'b0;
            lock_counter <= '0;
        end
    end
    
    assign clk_tree_locked = tree_locked;

endmodule
