#!/bin/bash
#SBATCH --job-name=bundle_cradle_v2
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_cradle_v2_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_cradle_v2_%j.err

# Prototype test for the_cradle level redesign (2026-04-12).
#
# Level change vs current bundle (60.3% valid):
#   - green_ball_y upper bound clamped from 0.5*WORLD_HEIGHT+MIN_Y (=0.0)
#     to -1.5.
#   - Root cause: seeds with green_ball_y > -1.5 have 60-93% impossibility rate
#     because the ball lacks the energy from a higher drop to escape the V-cradle.
#     These are geometrically impossible configurations, not oracle gaps.
#   - New range: y ∈ [MIN_Y + 0.2*WORLD_HEIGHT, -1.5] = [-2.7, -1.5].
#
# Expected outcome: ~98%+ valid rate (up from 60.3%) if y-clamping eliminates
# the impossible zone without disrupting solvable-zone seeds.
# Seeds 0:1000 (prototype test — full regen to follow if valid rate >= 90%).

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_cradle_v2] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels the_cradle \
    --seeds 0:1000 \
    --workers 16 \
    --attempts 50 \
    --oracle-steps 500

echo "[bundle_cradle_v2] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/the_cradle.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
# Only count seeds in 0:1000 range
entries_test = [e for e in entries if e['seed'] < 1000]
n_valid = len(set(e['seed'] for e in entries_test if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries_test))
pct = 100.0 * n_valid / n_seeds if n_seeds > 0 else 0.0
print(f'the_cradle v2 (seeds 0:1000): {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if pct < 80.0:
    print('FAIL: y-clamping did not significantly improve solvability')
    print('Check: is the impossible zone threshold (-1.5) correct?')
    print('Check: does the oracle cover the clamped y range?')
elif pct < 90.0:
    print(f'PARTIAL: improvement to {pct:.1f}% but oracle may still have gaps')
    print('Recommend: grid sweep to find remaining oracle misses')
else:
    print(f'OK: y-clamping successful ({pct:.1f}% valid)')
    print('Proceed with full regen over the new seed range')
"
