#!/bin/bash
#SBATCH --job-name=bundle_catapult_v2
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_catapult_v2_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_catapult_v2_%j.err

# Full regeneration of catapult bundle with improved oracle (2026-04-12).
#
# Oracle changes vs prior run (a73b341, 7.5% valid):
#   - Zone B changed from full-board (81 sq units) to right-side only
#     (x ∈ [arm_right, 4.5], y ∈ [arm_top+0.5, 4.5] ≈ 15-20 sq units).
#     This concentrates Zone B sampling on the 13.1% of solutions with x > 0.2,
#     giving ~4× better hit rate for those seeds.
#   - n_attempts increased to 200 (from 50) to improve hit rate in sparse
#     solution regions (bundle analysis: valid regions estimated very small,
#     ~0.1-0.5 sq units per solvable seed in a 27 sq unit zone).
#
# Expected outcome: ~20-40% valid rate (up from 7.5%) if true solvable rate
# is ~60% and oracle efficiency improves from ~12.5% to ~33-67%.
# Full regen over the canonical seed universe (0:10000) with the new oracle.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_catapult_v2] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels catapult \
    --seeds 0:10000 \
    --workers 16 \
    --attempts 200 \
    --oracle-steps 500

echo "[bundle_catapult_v2] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/catapult.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'catapult: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if n_valid < 3000:
    print('WARN: fewer than 3000 valid — oracle may still be under-performing')
    print('Recommend: increase n_attempts to 500 or investigate further')
elif n_valid < 9000:
    print('PARTIAL: good improvement but may need more seeds for 10k valid target')
    print('Run --extend --target-valid 10000 to top up')
else:
    print('OK: 10k valid target met or exceeded')
"
