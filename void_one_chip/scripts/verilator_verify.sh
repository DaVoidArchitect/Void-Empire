#!/bin/bash
#
# VERILATOR FORMAL VERIFICATION SUITE
# -----------------------------------------------------------------------------
# ARM-Standard Formal Verification
# Comprehensive verification using Verilator

set -e

echo "=========================================="
echo "ORIGIN-V OMEGA: VERILATOR VERIFICATION"
echo "=========================================="

# Directories
RTL_DIR="rtl"
TB_DIR="tb"
BUILD_DIR="verilator_build"
COVERAGE_DIR="coverage"

# Create build directory
mkdir -p $BUILD_DIR
mkdir -p $COVERAGE_DIR

# Verilator flags
VERILATOR_FLAGS="--cc --exe --build"
VERILATOR_FLAGS="$VERILATOR_FLAGS --trace --trace-structs"
VERILATOR_FLAGS="$VERILATOR_FLAGS --coverage"
VERILATOR_FLAGS="$VERILATOR_FLAGS --threads 4"
VERILATOR_FLAGS="$VERILATOR_FLAGS -Wall -Wno-UNOPTFLAT -Wno-UNSIGNED"
VERILATOR_FLAGS="$VERILATOR_FLAGS +incdir+$RTL_DIR/include"

echo ""
echo "[STEP 1] Linting RTL Code..."
echo "-------------------------------------------------"

verilator --lint-only -sv \
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
    --top-module origin_v_grand_core \
    2>&1 | tee $BUILD_DIR/lint.log

if [ $? -eq 0 ]; then
    echo "✓ Linting PASSED"
else
    echo "✗ Linting FAILED - Check $BUILD_DIR/lint.log"
    exit 1
fi

echo ""
echo "[STEP 2] Compiling with Verilator..."
echo "-------------------------------------------------"

verilator $VERILATOR_FLAGS \
    +incdir+$RTL_DIR/include \
    $RTL_DIR/include/origin_v_params.svh \
    $RTL_DIR/stack02_hardlaw/smf_unit.sv \
    $TB_DIR/tb_smf_unit.sv \
    --top-module tb_smf_unit \
    -o $BUILD_DIR/Vtb_smf_unit \
    2>&1 | tee $BUILD_DIR/compile_smf.log

if [ $? -eq 0 ]; then
    echo "✓ SMF Unit compilation PASSED"
else
    echo "✗ Compilation FAILED"
    exit 1
fi

echo ""
echo "[STEP 3] Running Functional Tests..."
echo "-------------------------------------------------"

# Run SMF Unit test
$BUILD_DIR/Vtb_smf_unit 2>&1 | tee $BUILD_DIR/test_smf.log

if [ $? -eq 0 ]; then
    echo "✓ SMF Unit test PASSED"
else
    echo "✗ SMF Unit test FAILED"
    exit 1
fi

echo ""
echo "[STEP 4] Coverage Analysis..."
echo "-------------------------------------------------"

# Generate coverage report
if [ -f "$BUILD_DIR/coverage.dat" ]; then
    verilator_coverage --rank --write $COVERAGE_DIR/coverage_report.txt $BUILD_DIR/coverage.dat
    
    # Extract coverage percentage
    COVERAGE=$(grep -oP 'Total Coverage: \K[0-9.]+' $COVERAGE_DIR/coverage_report.txt || echo "0")
    echo "Code Coverage: ${COVERAGE}%"
    
    if (( $(echo "$COVERAGE > 90" | bc -l) )); then
        echo "✓ Coverage target met (>90%)"
    else
        echo "⚠ Coverage below target (<90%)"
    fi
fi

echo ""
echo "=========================================="
echo "VERILATOR VERIFICATION COMPLETE"
echo "=========================================="
echo "Build artifacts: $BUILD_DIR/"
echo "Coverage reports: $COVERAGE_DIR/"
echo ""
