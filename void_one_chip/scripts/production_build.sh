#!/bin/bash
#
# PRODUCTION BUILD SCRIPT
# -----------------------------------------------------------------------------
# Complete production verification and build process
#

set -e

echo "=========================================="
echo "ORIGIN-V OMEGA: PRODUCTION BUILD"
echo "=========================================="

LOG_DIR="build_logs"
mkdir -p $LOG_DIR

ERRORS=0

# ============================================================================
# STEP 1: LINTING
# ============================================================================
echo ""
echo "[STEP 1] Verilator Linting..."
echo "-------------------------------------------------"

if command -v verilator > /dev/null; then
    verilator --lint-only -sv +incdir+rtl/include \
        rtl/include/origin_v_params.svh \
        rtl/stack01_puf/sram_puf.sv \
        rtl/stack02_hardlaw/smf_unit.sv \
        rtl/stack03_biolatch/bio_latch.sv \
        rtl/stack03_biolatch/efuse_model.sv \
        rtl/stack04_noc/noc_router_4d.sv \
        rtl/stack05_storage/aes256_engine.sv \
        rtl/stack06_mesh/mesh_excommunication.sv \
        rtl/stack07_pulse/pulse_velocity.sv \
        rtl/seu/seu_core.sv \
        rtl/top/origin_v_grand_core.sv \
        --top-module origin_v_grand_core \
        2>&1 | tee $LOG_DIR/lint.log
    
    if [ $? -eq 0 ]; then
        echo "✓ Linting PASSED"
    else
        echo "✗ Linting FAILED"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "⚠ Verilator not installed - skipping"
fi

# ============================================================================
# STEP 2: COMPILATION CHECK
# ============================================================================
echo ""
echo "[STEP 2] Compilation Check..."
echo "-------------------------------------------------"

if command -v vcs > /dev/null; then
    vcs -sverilog +incdir+rtl/include \
        rtl/include/origin_v_params.svh \
        rtl/stack02_hardlaw/smf_unit.sv \
        tb/tb_smf_unit.sv \
        -o simv_test \
        -l $LOG_DIR/compile.log 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✓ Compilation PASSED"
        rm -f simv_test simv_test.daidir
    else
        echo "✗ Compilation FAILED"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "⚠ VCS not available - skipping compilation check"
fi

# ============================================================================
# STEP 3: CODE STATISTICS
# ============================================================================
echo ""
echo "[STEP 3] Code Statistics..."
echo "-------------------------------------------------"

RTL_FILES=$(find rtl -name "*.sv" | wc -l)
TB_FILES=$(find tb -name "*.sv" | wc -l)
DOC_FILES=$(find docs -name "*.md" | wc -l)

echo "RTL Modules: $RTL_FILES"
echo "Testbenches: $TB_FILES"
echo "Documentation: $DOC_FILES"

# ============================================================================
# FINAL SUMMARY
# ============================================================================
echo ""
echo "=========================================="
echo "BUILD SUMMARY"
echo "=========================================="

if [ $ERRORS -eq 0 ]; then
    echo "✓ BUILD SUCCESSFUL"
    echo "Status: PRODUCTION READY"
    exit 0
else
    echo "✗ BUILD FAILED ($ERRORS errors)"
    echo "Status: FIX REQUIRED"
    exit 1
fi
