#!/bin/bash
#SBATCH --job-name=bundle_cradle_v3
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_cradle_v3_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_cradle_v3_%j.err

# Full regen of the_cradle with y-clamped level design (2026-04-12).
#
# Level change (committed d44fee9):
#   - green_ball_y clamped to uniform(MIN_Y + 0.2*WORLD_HEIGHT, -1.5) = [-2.7, -1.5]
#   - Prototype test (1000 seeds) confirmed: 78.4% valid (up from 60.3%)
#   - The remaining 21.6% impossibility is geometric (holder/ball combinations);
#     oracle zone coverage is unchanged (Zone A y ∈ [2.59, 4.40] still applies).
#
# Seeds 0:13000 estimated to yield ~10 000 valid at 78.4% valid rate.
# Run produces the definitive bundle for the redesigned level.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_cradle_v3] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels the_cradle \
    --seeds 0:13000 \
    --workers 16 \
    --attempts 50 \
    --oracle-steps 500

echo "[bundle_cradle_v3] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/the_cradle.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'the_cradle v3: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if n_valid >= 10000:
    print('OK: 10k valid target met')
elif n_valid >= 8000:
    print(f'PARTIAL: {n_valid} valid — run topup to reach 10k')
else:
    print(f'WARN: only {n_valid} valid — oracle may need recalibration for new y range')
"
