/*
 * PRIMAL ORIGINS: GLOBAL PARAMETERS & CONSTANTS
 * Production Release v3.0
 * Brand: Primal Origins SoC IP Core
 * ARM-Methodology Compliant
 */

`ifndef ORIGIN_V_PARAMS_SVH
`define ORIGIN_V_PARAMS_SVH

// ============================================================================
// ARCHITECTURAL PARAMETERS
// ============================================================================

// Core Configuration
parameter int NUM_CORES = 1024;
parameter int CORES_PER_DIM = 4; // 4^4 = 256 clusters, expandable to 1024
parameter int PUF_BITS = 4096;
parameter int BIO_ENTROPY_BITS = 512;
parameter int OMEGA_ID_BITS = 4096;

// Financial Constants (HARD-CODED METAL MASK - IMMUTABLE)
parameter logic [127:0] SCALER = 128'd10000;
parameter logic [127:0] FOUNDER_RATE = 128'd100;      // 1.00%
parameter logic [127:0] SYSTEM_RATE = 128'd518;       // 5.18%
parameter logic [127:0] TOTAL_TAX_RATE = 128'd618;    // 6.18%
parameter logic [127:0] LIQUIDITY_RATE = 128'd300;    // 3.00% of 6.18%
parameter logic [127:0] MESH_MAINT_RATE = 128'd218;   // 2.18% of 6.18%

// Timing Constants
parameter int CLK_PERIOD_PS = 1000;  // 1GHz base clock (3nm capable of 5GHz+)
parameter int BIO_WATCHDOG_MS = 1000; // 1 second entropy refresh window
parameter int MORTALITY_PERIOD_HOURS = 720; // 30 days = 720 hours
parameter int MORTALITY_CLOCKS = 2_592_000_000; // 720h * 3600s * 1GHz

// Network-on-Chip
parameter int NOC_DATA_WIDTH = 128;
parameter int NOC_ADDR_WIDTH = 32;
parameter int AXI_DATA_WIDTH = 128;
parameter int AXI_ADDR_WIDTH = 64;

// Storage & Encryption
parameter int AES_KEY_WIDTH = 256;
parameter int AES_BLOCK_WIDTH = 128;

// Governance
parameter int GOVERNANCE_WEIGHT_BITS = 64;
parameter int VOTE_WEIGHT_SCALE = 4; // Logarithmic scaling shift

// Civilization States
typedef enum logic [31:0] {
    CIV_STATE_CITIZEN_OK  = 32'hCITIZEN_OK,
    CIV_STATE_FOUNDER     = 32'hGOD_MODE,
    CIV_STATE_EXCOMM      = 32'hDEAD_DEAD,
    CIV_STATE_ROGUE       = 32'hROGUE_01
} civilization_state_e;

// ============================================================================
// OMEGA-V ISA EXTENSIONS (RISC-V RV128I Base)
// ============================================================================

// Custom Opcodes (7-bit opcode field)
localparam logic [6:0] OP_SETTLE_ATOM = 7'h7B; // Atomic 6.18% split
localparam logic [6:0] OP_LATCH_SYNC  = 7'h7C; // Bio-entropy sync
localparam logic [6:0] OP_MERIT_CHECK = 7'h7D; // ZK proof verification
localparam logic [6:0] OP_XFER_PULSE  = 7'h7E; // Pulse transfer
localparam logic [6:0] OP_SOV_VOTE    = 7'h7F; // Sovereign vote

// ============================================================================
// ERROR CODES & STATUS
// ============================================================================

typedef enum logic [7:0] {
    ERR_NONE           = 8'h00,
    ERR_UNAUTHORIZED   = 8'h01,
    ERR_BIO_TIMEOUT    = 8'h02,
    ERR_INTEGRITY_FAIL = 8'h03,
    ERR_NOC_OVERFLOW   = 8'h04,
    ERR_DOUBLE_SPEND   = 8'h05
} error_code_e;

// ============================================================================
// UNIVERSAL PROCESS CONFIGURATION (Mass Adoption Support)
// ============================================================================
// Process-agnostic parameters - automatically adapts to any manufacturer's process

// Supported process nodes (in nanometers)
parameter int SUPPORTED_PROCESS_NODES[] = {7, 5, 3, 2};  // Common nodes
parameter int DEFAULT_PROCESS_NODE = 3;  // Default 3nm

// Process-dependent scaling factors
parameter real BASE_CLK_FREQ_GHZ = 1.0;  // Base 1GHz for 3nm
parameter real PROCESS_FREQ_SCALE[] = {0.5, 0.75, 1.0, 1.5};  // Frequency scaling per node
parameter real DEFAULT_SUPPLY_VOLTAGE = 0.65;  // Nominal voltage for 3nm (V)

// Universal timing calculation
// Actual clock period = BASE_CLK_PERIOD_NS / PROCESS_FREQ_SCALE[process_index]
parameter real BASE_CLK_PERIOD_NS = 1.0;  // 1ns = 1GHz base

// Performance scaling (for different process nodes)
// 3nm: 1.0x, 5nm: 0.75x, 7nm: 0.5x, 2nm: 1.5x
parameter real MAX_TPS_SCALE_FACTOR = 1.5;  // 2nm can achieve higher TPS

// ============================================================================
// PERFORMANCE TARGETS (Theoretical Maximums)
// ============================================================================
// Calculated for 1024-core 4D Hyper-Torus topology

// Single core performance
parameter real SINGLE_CORE_MAX_TPS = 1.0e12;  // 1 Trillion TPS per core

// System performance (1024 cores, accounting for NoC overhead)
parameter real SYSTEM_MAX_TPS = 20.0e12;  // 20 Trillion TPS (theoretical)
parameter real REALISTIC_TPS = 15.0e12;   // 15 Trillion TPS (accounting for overhead)

`endif // ORIGIN_V_PARAMS_SVH
