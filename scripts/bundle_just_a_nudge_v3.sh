#!/bin/bash
#SBATCH --job-name=bundle_nudge_v3
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_nudge_v3_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_nudge_v3_%j.err

# Prototype test for just_a_nudge level redesign (2026-04-12).
#
# Level change vs v2 (c428780, 8.3% valid):
#   - basket_x sampling changed from uniform(-1.0, platform.right+0.39-half_width)
#     to centered on fall_x = platform.left + ball_offset + green_ball_radius ± 0.3.
#   - Root cause of old constraint: basket was kept LEFT of platform.right + 0.39,
#     but the green ball falls at platform.left + ball_offset + radius, which sits
#     0.5-0.8 units RIGHT of platform.right. The constraint caused systematic
#     basket/ball misalignment in ~90% of seeds.
#
# Expected outcome: 30-60% valid rate (up from 8.3%) if the basket alignment
# is the primary cause of impossibility.
# Seeds 0:1000 (prototype test — full regen to follow if valid rate >= 30%).

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_just_a_nudge_v3] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels just_a_nudge \
    --seeds 0:1000 \
    --workers 16 \
    --attempts 50 \
    --oracle-steps 500

echo "[bundle_just_a_nudge_v3] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/just_a_nudge.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
# Only count seeds in 0:1000 range (bundle may contain v2 seeds 1000:10000)
entries_test = [e for e in entries if e['seed'] < 1000]
n_valid = len(set(e['seed'] for e in entries_test if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries_test))
pct = 100.0 * n_valid / n_seeds if n_seeds > 0 else 0.0
print(f'just_a_nudge v3 (seeds 0:1000): {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if pct < 15.0:
    print('FAIL: basket alignment did not help — investigate further')
    print('Check: is green_ball_x formula correct? Does the ball actually land in basket?')
elif pct < 30.0:
    print(f'PARTIAL: improvement to {pct:.1f}% but below target (30%+)')
    print('Consider widening the ±0.3 alignment window or checking oracle coverage')
else:
    print(f'OK: basket alignment fix successful ({pct:.1f}% valid)')
    print('Proceed with full 10k-seed regen with expanded oracle and aligned basket')
"
