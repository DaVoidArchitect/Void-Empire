#!/bin/bash
#
# COMPREHENSIVE TEST RUNNER - ARM STANDARD
# -----------------------------------------------------------------------------
# Runs all verification tests: Functional, Economic, Performance, Security
#

set -e

echo "=========================================="
echo "ORIGIN-V OMEGA: COMPREHENSIVE TEST SUITE"
echo "ARM/Intel/NVIDIA Standard Methodology"
echo "=========================================="

LOG_DIR="test_results"
mkdir -p $LOG_DIR

TEST_RESULTS=0
TOTAL_TESTS=0
PASSED_TESTS=0

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# TEST 1: Verilator Linting & Formal Verification
# ============================================================================
echo ""
echo "[TEST SUITE 1] Verilator Verification..."
echo "-------------------------------------------------"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if bash scripts/verilator_verify.sh 2>&1 | tee $LOG_DIR/verilator.log; then
    echo -e "${GREEN}✓ Verilator Verification PASSED${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Verilator Verification FAILED${NC}"
    TEST_RESULTS=1
fi

# ============================================================================
# TEST 2: Economic Stability
# ============================================================================
echo ""
echo "[TEST SUITE 2] Economic Stability Tests..."
echo "-------------------------------------------------"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if vcs -sverilog +incdir+rtl/include \
    rtl/include/origin_v_params.svh \
    rtl/stack02_hardlaw/smf_unit.sv \
    tb/tb_economic_stability.sv \
    -o simv_econ \
    -l $LOG_DIR/econ_compile.log && \
   ./simv_econ 2>&1 | tee $LOG_DIR/econ_test.log; then
    
    if grep -q "ECONOMIC SYSTEM STABLE" $LOG_DIR/econ_test.log; then
        echo -e "${GREEN}✓ Economic Stability PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ Economic Stability FAILED${NC}"
        TEST_RESULTS=1
    fi
else
    echo -e "${RED}✗ Economic Stability Test Compilation FAILED${NC}"
    TEST_RESULTS=1
fi

# ============================================================================
# TEST 3: Performance Analysis
# ============================================================================
echo ""
echo "[TEST SUITE 3] Performance Analysis (20T TPS Target)..."
echo "-------------------------------------------------"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if vcs -sverilog +incdir+rtl/include \
    rtl/include/origin_v_params.svh \
    tb/tb_performance_tps.sv \
    -o simv_perf \
    -l $LOG_DIR/perf_compile.log && \
   ./simv_perf 2>&1 | tee $LOG_DIR/perf_test.log; then
    
    if grep -q "TARGET ACHIEVED" $LOG_DIR/perf_test.log; then
        echo -e "${GREEN}✓ Performance Target PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${YELLOW}⚠ Performance Target Not Met (Check log)${NC}"
    fi
else
    echo -e "${RED}✗ Performance Test FAILED${NC}"
    TEST_RESULTS=1
fi

# ============================================================================
# TEST 4: Comprehensive Functional Tests
# ============================================================================
echo ""
echo "[TEST SUITE 4] Comprehensive Functional Tests..."
echo "-------------------------------------------------"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if vcs -sverilog +incdir+rtl/include \
    rtl/include/origin_v_params.svh \
    rtl/**/*.sv \
    tb/tb_grand_core.sv \
    -o simv_func \
    -l $LOG_DIR/func_compile.log && \
   ./simv_func 2>&1 | tee $LOG_DIR/func_test.log; then
    
    if grep -q "ALL TESTS PASSED" $LOG_DIR/func_test.log; then
        echo -e "${GREEN}✓ Functional Tests PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ Functional Tests FAILED${NC}"
        TEST_RESULTS=1
    fi
else
    echo -e "${RED}✗ Functional Test Compilation FAILED${NC}"
    TEST_RESULTS=1
fi

# ============================================================================
# FINAL SUMMARY
# ============================================================================
echo ""
echo "=========================================="
echo "TEST SUITE SUMMARY"
echo "=========================================="
echo "Total Test Suites: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $((TOTAL_TESTS - PASSED_TESTS))"
echo "Pass Rate: $((PASSED_TESTS * 100 / TOTAL_TESTS))%"
echo "=========================================="

if [ $TEST_RESULTS -eq 0 ] && [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo -e "${GREEN}STATUS: PRODUCTION READY${NC}"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo -e "${RED}STATUS: NOT PRODUCTION READY${NC}"
    echo ""
    echo "Check logs in $LOG_DIR/ for details"
    exit 1
fi
