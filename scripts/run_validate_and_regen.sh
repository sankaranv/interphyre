#!/bin/bash
#SBATCH --job-name=bundle_regen
#SBATCH --partition=cpu
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=scratch/bundle_regen/logs/%x_%j.out
#SBATCH --error=scratch/bundle_regen/logs/%x_%j.err

# Per-level validate-and-regen job.
# Submit for a specific level:
#   sbatch --job-name=regen_basket_case --export=ALL,LEVEL=basket_case scripts/run_validate_and_regen.sh
#
# Submit all 25 levels in parallel:
#   bash scripts/submit_all_regen.sh

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
cd "$PROJECT"

source "$PROJECT/.venv/bin/activate"

mkdir -p scratch/bundle_regen/logs

LEVEL="${LEVEL:-basket_case}"

echo "=== validate_and_regen: $LEVEL ==="
echo "Node: $(hostname)"
echo "Start: $(date)"

python -u scripts/validate_and_regen.py --level "$LEVEL" --workers 8

echo "End: $(date)"
echo "=== Done ==="
