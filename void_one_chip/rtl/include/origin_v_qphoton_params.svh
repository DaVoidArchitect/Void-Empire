/*
 * PRIMAL ORIGINS: QUANTUM-PHOTONIC PARAMETERS
 * -----------------------------------------------------------------------------
 * Quantum-Photonic Architecture Enhancements
 * Fractal Light/Photonics Integration Throughout Design
 * Production Release v3.0 (Quantum-Photonic Edition)
 * Brand: Primal Origins SoC IP Core
 */

`ifndef ORIGIN_V_QPHOTON_PARAMS_SVH
`define ORIGIN_V_QPHOTON_PARAMS_SVH

`include "origin_v_params.svh"

// ============================================================================
// PHOTONIC PARAMETERS
// ============================================================================

// Optical Wavelengths (nm) - Standard telecom C-band and L-band
parameter real PHOTON_WAVELENGTH_CBAND = 1550.0;  // C-band primary (1550nm)
parameter real PHOTON_WAVELENGTH_LBAND = 1310.0;  // L-band secondary (1310nm)
parameter real PHOTON_WAVELENGTH_O_BAND = 850.0;  // O-band for on-chip (850nm)

// Wavelength Division Multiplexing (WDM)
parameter int NUM_WDM_CHANNELS = 32;              // 32-channel WDM
parameter real WDM_CHANNEL_SPACING = 0.8;         // 0.8nm spacing (100GHz ITU grid)

// Photonic Waveguide Parameters
parameter real WG_WIDTH_NM = 450.0;               // Waveguide width (nm)
parameter real WG_HEIGHT_NM = 220.0;              // Waveguide height (nm)
parameter real WG_BEND_RADIUS_UM = 5.0;           // Minimum bend radius (um)
parameter real WG_LOSS_DB_PER_CM = 0.5;           // Propagation loss (dB/cm)

// Photonic Device Parameters
parameter real MZI_LENGTH_UM = 100.0;             // Mach-Zehnder Interferometer length
parameter real RING_RADIUS_UM = 10.0;             // Microring resonator radius
parameter real RING_COUPLING_COEFF = 0.1;         // Ring coupling coefficient
parameter real RING_Q_FACTOR = 10000.0;           // Ring resonator Q-factor

// Optical Power Budget
parameter real TX_OPTICAL_POWER_DBM = 0.0;        // Transmit power (0 dBm)
parameter real RX_SENSITIVITY_DBM = -20.0;        // Receiver sensitivity (-20 dBm)
parameter real LINK_MARGIN_DB = 3.0;              // System margin (3 dB)

// ============================================================================
// QUANTUM PARAMETERS
// ============================================================================

// Quantum State Dimensions
parameter int QUBIT_COUNT = 128;                  // Quantum register size (qubits)
parameter int QUANTUM_STATE_DIM = 2**QUBIT_COUNT; // Hilbert space dimension

// Quantum Entanglement
parameter int MAX_ENTANGLED_PAIRS = 64;           // Maximum Bell pairs
parameter int ENTANGLEMENT_FIDELITY_PPM = 999900; // 99.99% fidelity (ppm)

// Quantum Error Correction
parameter int QEC_CODE_DISTANCE = 7;              // Surface code distance
parameter int QEC_LOGICAL_QUBITS = QUBIT_COUNT / QEC_CODE_DISTANCE;

// Quantum Key Distribution (QKD)
parameter int QKD_KEY_BITS = 256;                 // QKD key length
parameter int QKD_BASE_BITS = 512;                // QKD basis selection bits
parameter int QKD_ERROR_THRESHOLD_PPM = 11000;    // 1.1% error threshold

// Quantum Random Number Generation (QRNG)
parameter int QRNG_BITS_PER_PHOTON = 2;           // Bits per photon (dual-rail encoding)
parameter int QRNG_RATE_GHZ = 10;                 // QRNG generation rate (10 GHz)

// ============================================================================
// FRACTAL PHOTONIC PARAMETERS
// ============================================================================

// Fractal H-Tree Clock Distribution
parameter int FRACTAL_H_TREE_LEVELS = 10;         // H-tree recursion levels (2^10 = 1024 leaves)
parameter real FRACTAL_SCALE_FACTOR = 2.0;        // Scaling factor per level
parameter int FRACTAL_SEGMENT_LENGTH_UM = 100;    // Base segment length (um)

// Fractal Resonator Cavities (Photonic Storage)
parameter int FRACTAL_RING_LEVELS = 6;            // Nested ring levels
parameter real FRACTAL_RING_SCALE = 1.618;        // Golden ratio scaling (Phi)
parameter int FRACTAL_RING_COUNT = 64;            // Total nested rings

// Fractal Waveguide Routing
parameter int FRACTAL_WG_LEVELS = 8;              // Recursive routing levels
parameter real FRACTAL_WG_BRANCH_ANGLE = 45.0;    // Branch angle (degrees)

// Self-Similar Photonic Structures
parameter int KOCH_CURVE_ITERATIONS = 6;          // Koch curve fractal iterations
parameter int MANDELBROT_ITERATIONS = 64;         // Mandelbrot set iterations (quantum states)

// ============================================================================
// PHOTONIC ARITHMETIC UNITS
// ============================================================================

// Optical Adder/Multiplier
parameter int PHOTON_ALU_PRECISION = 128;         // Optical ALU bit-width
parameter real PHOTON_ALU_LATENCY_PS = 50.0;      // Optical computation latency (50ps)
parameter int PHOTON_ALU_THROUGHPUT_GHZ = 20.0;   // Optical ALU throughput (20 GHz)

// Photonic Fixed-Point Multiplier (for Hard-Law)
parameter int PHOTON_MULT_PIPELINE_STAGES = 3;    // Optical multiplier stages
parameter real PHOTON_MULT_LATENCY_PS = 150.0;    // Total latency (150ps)

// ============================================================================
// PHOTONIC INTERCONNECT (NoC)
// ============================================================================

// Optical Network-on-Chip
parameter int PHOTON_NOC_CHANNELS = 8;            // Parallel optical channels
parameter int PHOTON_NOC_BANDWIDTH_TBPS = 8;      // Per-channel bandwidth (8 Tbps)
parameter real PHOTON_NOC_LATENCY_PS = 100.0;     // Optical link latency (100ps)

// WDM-Based Routing
parameter int PHOTON_NOC_WDM_CHANNELS = NUM_WDM_CHANNELS; // WDM channels per link
parameter real PHOTON_NOC_TOTAL_BW_PETABPS = PHOTON_NOC_CHANNELS * PHOTON_NOC_WDM_CHANNELS * PHOTON_NOC_BANDWIDTH_TBPS / 1000.0;

// Optical Switch Parameters
parameter int PHOTON_SWITCH_SIZE = 16;            // 16x16 optical switch
parameter real PHOTON_SWITCH_LOSS_DB = 2.0;       // Switch insertion loss (2 dB)
parameter real PHOTON_SWITCH_CROSSTALK_DB = -40.0; // Switch crosstalk (-40 dB)

// ============================================================================
// QUANTUM-PHOTONIC PUF ENHANCEMENTS
// ============================================================================

// Quantum-Enhanced PUF
parameter int QUANTUM_PUF_QUBITS = 512;           // Quantum PUF qubits
parameter int QUANTUM_PUF_PHOTONS = 1024;         // Photon count per measurement
parameter real QUANTUM_PUF_ENTROPY_BITS = 4096.0; // Entropy bits from quantum noise

// Photonic PUF (Ring Resonator Variations)
parameter int PHOTON_PUF_RINGS = 1024;            // Number of ring resonators
parameter real PHOTON_PUF_VARIATION_PPM = 1000.0; // Process variation (0.1%)

// ============================================================================
// QUANTUM-ENCRYPTED STORAGE
// ============================================================================

// Quantum Key Distribution for Storage
parameter int QKD_STORAGE_KEY_BITS = AES_KEY_WIDTH; // 256-bit QKD key
parameter int QKD_KEY_REFRESH_RATE_HZ = 1000;    // Key refresh rate (1 kHz)
parameter int QKD_KEY_LIFETIME_SEC = 3600;        // Key lifetime (1 hour)

// Photonic Encrypted Memory
parameter int PHOTON_MEM_CAPACITY_KB = 64;        // Optical memory capacity (64 KB)
parameter real PHOTON_MEM_ACCESS_TIME_PS = 200.0; // Access latency (200ps)

// ============================================================================
// PHOTONIC CLOCK DISTRIBUTION
// ============================================================================

// Optical Clock Tree
parameter real PHOTON_CLK_FREQ_GHZ = 5.0;         // Optical clock frequency (5 GHz)
parameter real PHOTON_CLK_JITTER_FS = 10.0;       // Optical clock jitter (10 fs)
parameter real PHOTON_CLK_SKEW_PS = 5.0;          // Maximum clock skew (5ps)

// H-Tree Fractal Clock
parameter int PHOTON_H_TREE_FANOUT = 4;           // H-tree fanout (4 branches)
parameter real PHOTON_H_TREE_UNIFORMITY = 0.99;   // Path length uniformity (99%)

// ============================================================================
// PERFORMANCE ENHANCEMENTS
// ============================================================================

// Theoretical Maximum with Quantum-Photonic
parameter real PHOTON_MAX_TPS_PER_CORE = 5.0e12;  // 5 Trillion TPS per core (optical)
parameter real QUANTUM_MAX_TPS_PER_CORE = 10.0e12; // 10 Trillion TPS per core (quantum)
parameter real SYSTEM_MAX_TPS_QPHOTON = 50.0e12;   // 50 Trillion TPS (quantum-photonic)

// Energy Efficiency
parameter real PHOTON_ENERGY_PER_BIT_FJ = 10.0;   // Photonic energy per bit (10 fJ)
parameter real QUANTUM_ENERGY_PER_BIT_FJ = 5.0;   // Quantum energy per bit (5 fJ)

// ============================================================================
// MANUFACTURING CONSTRAINTS
// ============================================================================

// Silicon Photonics Process
parameter int PHOTON_LAYER_STACK_HEIGHT_NM = 220; // Silicon photonic layer thickness
parameter int PHOTON_BURIED_OXIDE_NM = 2000;      // Buried oxide (BOX) thickness
parameter real PHOTON_WAFER_SIZE_MM = 300.0;      // Wafer size (300mm)

// Hybrid Integration (Electronics + Photonics)
parameter int HYBRID_BONDING_PITCH_UM = 10.0;     // Hybrid bonding pitch
parameter int PHOTON_ELECTRONIC_LAYERS = 2;       // Number of interconnect layers

`endif // ORIGIN_V_QPHOTON_PARAMS_SVH
