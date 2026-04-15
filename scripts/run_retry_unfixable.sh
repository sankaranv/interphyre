#!/bin/bash
#SBATCH --job-name=retry_catapult
#SBATCH --partition=cpu
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=scratch/bundle_regen/logs/retry_%x_%j.out
#SBATCH --error=scratch/bundle_regen/logs/retry_%x_%j.err

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
cd "$PROJECT"

source "$PROJECT/.venv/bin/activate"

mkdir -p scratch/bundle_regen/logs

LEVEL="${LEVEL:-catapult}"
ATTEMPTS="${ATTEMPTS:-300}"
MAX_VARIANTS="${MAX_VARIANTS:-}"

echo "=== retry_unfixable: $LEVEL (attempts=$ATTEMPTS, max_variants=${MAX_VARIANTS:-default}) ==="
echo "Node: $(hostname)"
echo "Start: $(date)"

EXTRA_ARGS=""
if [ -n "$MAX_VARIANTS" ]; then
    EXTRA_ARGS="--max-variants $MAX_VARIANTS"
fi

python -u scripts/retry_unfixable.py --level "$LEVEL" --attempts "$ATTEMPTS" --workers 8 $EXTRA_ARGS

echo "End: $(date)"
echo "=== Done ==="
