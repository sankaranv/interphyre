#!/bin/bash
#SBATCH --job-name=bundle_keyhole_v2
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_keyhole_v2_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_keyhole_v2_%j.err

# Bundle regen for keyhole v3: level change applied (bottom_divider_length cap at 1.2).
# Prior regen (55545961): 9907/10001 = 99.1% (94 impossible — bd.top > -3.8 → gap too narrow).
# Cap fixes: bd.top = MIN_Y + 1.2 = -3.8 < -3.5 impossibility threshold.
# Expected: ≥99.8% with n_attempts=200 max_variants=10.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_keyhole_v2] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels keyhole \
    --seeds 0:10001 \
    --workers 16 \
    --attempts 200 --max-variants 10

echo "[bundle_keyhole_v2] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/keyhole.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'keyhole: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if pct < 99.5:
    print(f'WARN: below expected 99.5% threshold')
    sys.exit(1)
print('OK')
"
