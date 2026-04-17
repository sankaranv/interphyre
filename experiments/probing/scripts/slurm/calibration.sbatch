#!/bin/bash
# §9.4 Magnitude calibration — CPU only, one job per level.
# Runs 200 seeds × 8 magnitudes × (target, direction) combos for one level.
# Submit 4 jobs (one per level) in parallel.
#
# Usage:
#   for level in down_to_earth end_of_line two_body_problem keyhole; do
#     sbatch --export=ALL,LEVEL=$level \
#       --output=scratch/probing/logs/calibration_${level}_%j.out \
#       --error=scratch/probing/logs/calibration_${level}_%j.err \
#       experiments/probing/scripts/slurm/calibration.sbatch
#   done
#
# Estimated time: ~45 min per level (28,800 Box2D rollouts / 4 levels ≈ 7,200 each).

#SBATCH --job-name=probing_calib
#SBATCH --partition=cpu
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=01:30:00
#SBATCH --output=scratch/probing/logs/calibration_%j.out
#SBATCH --error=scratch/probing/logs/calibration_%j.err

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p scratch/probing/logs scratch/probing

cd "$PROJECT"
source .venv/bin/activate

LEVEL="${LEVEL:-down_to_earth}"

echo "=== Calibration: level=$LEVEL, job=$SLURM_JOB_ID ==="
echo "Start: $(date)"

python -u -m experiments.probing.scripts.run_calibration \
    --level "$LEVEL" \
    --output-json scratch/probing/calibration.json

echo "End: $(date)"

# --- Inline verification ---
python -u -c "
import json, sys
with open('scratch/probing/calibration.json') as f:
    data = json.load(f)
level = '$LEVEL'
if level not in data:
    print(f'FAIL: {level} not in calibration.json', file=sys.stderr)
    sys.exit(1)
n_combos = sum(
    1 for t in data[level].values() for v in t.values() if v is not None
)
print(f'OK: {level} calibrated, {n_combos} valid (target, direction) combinations.')
"
