#!/bin/bash
#
# ORIGIN-V OMEGA: SIMULATION RUN SCRIPT
# -----------------------------------------------------------------------------
# Runs comprehensive verification suite
#

echo "=========================================="
echo "ORIGIN-V OMEGA: SIMULATION SUITE"
echo "=========================================="

# Tool selection (Modify based on available simulator)
SIMULATOR=${SIMULATOR:-vcs}  # Options: vcs, vlog, xrun

# Directories
RTL_DIR="rtl"
TB_DIR="tb"
LOG_DIR="logs"
WAVE_DIR="waves"

mkdir -p $LOG_DIR $WAVE_DIR

# ============================================================================
# COMPILE
# ============================================================================

echo "Compiling RTL and Testbenches..."

if [ "$SIMULATOR" == "vcs" ]; then
    vcs -full64 -sverilog \
        -timescale=1ns/1ps \
        -debug_access+all \
        +incdir+$RTL_DIR/include \
        $RTL_DIR/include/origin_v_params.svh \
        $RTL_DIR/stack01_puf/sram_puf.sv \
        $RTL_DIR/stack02_hardlaw/smf_unit.sv \
        $RTL_DIR/stack03_biolatch/bio_latch.sv \
        $RTL_DIR/stack04_noc/noc_router_4d.sv \
        $RTL_DIR/stack05_storage/aes256_engine.sv \
        $RTL_DIR/stack06_mesh/mesh_excommunication.sv \
        $RTL_DIR/stack07_pulse/pulse_velocity.sv \
        $RTL_DIR/seu/seu_core.sv \
        $RTL_DIR/top/origin_v_grand_core.sv \
        $TB_DIR/tb_smf_unit.sv \
        $TB_DIR/tb_grand_core.sv \
        -o simv \
        -l $LOG_DIR/compile.log

elif [ "$SIMULATOR" == "vlog" ]; then
    vlog -sv -timescale 1ns/1ps \
        +incdir+$RTL_DIR/include \
        $RTL_DIR/include/origin_v_params.svh \
        $RTL_DIR/stack*/*.sv \
        $RTL_DIR/seu/*.sv \
        $RTL_DIR/top/*.sv \
        $TB_DIR/*.sv \
        -l $LOG_DIR/compile.log

elif [ "$SIMULATOR" == "xrun" ]; then
    xrun -sv -timescale 1ns/1ps \
        -incdir $RTL_DIR/include \
        $RTL_DIR/include/origin_v_params.svh \
        $RTL_DIR/stack*/*.sv \
        $RTL_DIR/seu/*.sv \
        $RTL_DIR/top/*.sv \
        $TB_DIR/*.sv \
        -l $LOG_DIR/compile.log

else
    echo "Unknown simulator: $SIMULATOR"
    exit 1
fi

if [ $? -ne 0 ]; then
    echo "Compilation failed. Check $LOG_DIR/compile.log"
    exit 1
fi

echo "Compilation successful!"

# ============================================================================
# RUN TESTS
# ============================================================================

echo ""
echo "Running Testbenches..."

# Test 1: SMF Unit
echo "  [1/2] Testing SMF Unit..."
if [ "$SIMULATOR" == "vcs" ]; then
    ./simv +testname=smf_unit -l $LOG_DIR/test_smf.log
elif [ "$SIMULATOR" == "vlog" ]; then
    vsim -c tb_smf_unit -do "run -all; quit" -l $LOG_DIR/test_smf.log
fi

# Test 2: Grand Core
echo "  [2/2] Testing Grand Core..."
if [ "$SIMULATOR" == "vcs" ]; then
    ./simv +testname=grand_core -l $LOG_DIR/test_grand_core.log
elif [ "$SIMULATOR" == "vlog" ]; then
    vsim -c tb_grand_core -do "run -all; quit" -l $LOG_DIR/test_grand_core.log
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "=========================================="
echo "SIMULATION COMPLETE"
echo "=========================================="
echo "Logs: $LOG_DIR/"
echo ""

# Check for errors
ERROR_COUNT=$(grep -i "error\|fail" $LOG_DIR/*.log | wc -l)
if [ $ERROR_COUNT -gt 0 ]; then
    echo "WARNING: $ERROR_COUNT errors found in logs"
    exit 1
else
    echo "All tests passed!"
    exit 0
fi
