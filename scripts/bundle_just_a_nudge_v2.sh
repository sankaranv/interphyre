#!/bin/bash
#SBATCH --job-name=bundle_nudge_v2
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_nudge_v2_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_nudge_v2_%j.err

# Full regeneration of just_a_nudge bundle with improved oracle (2026-04-12).
#
# Oracle changes vs prior run (92a5c0d, 6.5% valid):
#   - x_max_a expanded from green_ball.x + 3.5 to 4.5 (always).
#     Bundle analysis shows 44.2% of valid seeds have dx > 3.5 and were entirely
#     missed by old Zone A; x_max = 4.5 covers all right-side solutions.
#   - y_min_a expanded from green_ball.y - 1.5 to green_ball.y - 5.0.
#     Solutions exist with dy as low as -5.99; old y_min missed low-y solutions.
#   - These changes bring Zone A coverage from 54.8% → 98.8% of observed solutions.
#
# Expected outcome: ~9-12% valid rate (up from 6.5%) assuming true solvable rate
# is ~10% and Zone A coverage improvement increases oracle efficiency proportionally.
# NOTE: Level still flagged for design review — 90% genuine impossibility means
# 10k valid would require ~100k seeds which is not justified before redesign.
# This 10k-seed run documents the true solvability rate after oracle calibration.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_just_a_nudge_v2] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels just_a_nudge \
    --seeds 0:10000 \
    --workers 16 \
    --attempts 50 \
    --oracle-steps 500

echo "[bundle_just_a_nudge_v2] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/just_a_nudge.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'just_a_nudge: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if pct < 7.0:
    print('WARN: valid rate lower than previous oracle (6.5%) — oracle regression')
    print('Zone A expansion may have diluted sampling density too much')
elif pct >= 9.0:
    print(f'OK: improved from 6.5% to {pct:.1f}% — oracle calibration successful')
    print('Level still needs design review for 10k valid target')
else:
    print(f'PARTIAL: modest improvement from 6.5% to {pct:.1f}%')
"
