#!/bin/bash
#SBATCH --job-name=bundle_cradle_v4
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_cradle_v4_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_cradle_v4_%j.err

# Full regen of the_cradle with the original level design (restored from d44fee9~1).
# Prior bundle (v3) reflected the y-clamped redesign which was rolled back.
# This run uses the canonical seed universe (0:10001) and original oracle.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_cradle_v4] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels the_cradle \
    --seeds 0:10001 \
    --workers 16 \
    --attempts 50 \
    --oracle-steps 500

echo "[bundle_cradle_v4] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/the_cradle.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = sum(1 for e in entries if e['status'] == 'valid')
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'the_cradle v4: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if n_seeds != 10001:
    print(f'WARN: expected 10001 seeds, got {n_seeds}')
    sys.exit(1)
print('OK: seed universe correct (0-10000)')
"
