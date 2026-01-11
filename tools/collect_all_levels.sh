#!/bin/bash
# Collect evaluation data for all levels with classic seeds

# Configuration
SEEDS="42,69,123,256,314,420,512,666,777,1337"
OUTPUT_DIR="data/eval"
WORKERS=4
MAX_ATTEMPTS=10000

# List of all levels
LEVELS=(
    "basket_case"
    "catapult"
    "cliffhanger"
    "dive_bomb"
    "down_to_earth"
    "end_of_line"
    "falling_into_place"
)

echo "================================================"
echo "Collecting evaluation data for all levels"
echo "Seeds: ${SEEDS}"
echo "Workers: ${WORKERS}"
echo "Max attempts per seed: ${MAX_ATTEMPTS}"
echo "Output directory: ${OUTPUT_DIR}"
echo "================================================"
echo ""

# Track results
SUCCESSFUL_LEVELS=()
FAILED_LEVELS=()

# Process each level
for level in "${LEVELS[@]}"; do
    echo "========================================"
    echo "Processing level: ${level}"
    echo "========================================"

    python tools/collect_data.py \
        --level "${level}" \
        --output-dir "${OUTPUT_DIR}" \
        --seeds "${SEEDS}" \
        --workers ${WORKERS} \
        --max-attempts ${MAX_ATTEMPTS}

    if [ $? -eq 0 ]; then
        SUCCESSFUL_LEVELS+=("${level}")
        echo ""
        echo "✓ ${level} completed successfully"
        echo ""
    else
        FAILED_LEVELS+=("${level}")
        echo ""
        echo "✗ ${level} failed"
        echo ""
    fi

    # Small pause between levels
    sleep 2
done

echo ""
echo "================================================"
echo "SUMMARY"
echo "================================================"
echo "Total levels: ${#LEVELS[@]}"
echo "Successful: ${#SUCCESSFUL_LEVELS[@]}"
echo "Failed: ${#FAILED_LEVELS[@]}"
echo ""

if [ ${#SUCCESSFUL_LEVELS[@]} -gt 0 ]; then
    echo "Successful levels:"
    for level in "${SUCCESSFUL_LEVELS[@]}"; do
        echo "  ✓ ${level}"
    done
    echo ""
fi

if [ ${#FAILED_LEVELS[@]} -gt 0 ]; then
    echo "Failed levels:"
    for level in "${FAILED_LEVELS[@]}"; do
        echo "  ✗ ${level}"
    done
    echo ""
fi

echo "Results saved to: ${OUTPUT_DIR}"
echo "================================================"
