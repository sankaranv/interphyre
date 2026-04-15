#!/bin/bash
#SBATCH --job-name=bundle_cradle_v6
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_cradle_v6_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_cradle_v6_%j.err

# Bundle regen for the_cradle with k=20 (up from k=10).
# Geometric-decay analysis (2026-04-14): p per variant is constant across all variants
# — impossible seeds are purely Bernoulli sampling artifacts, not level design issues.
# model(k=10)=51.1 impossible; model(k=20)=0.3 impossible.
# Expected: ~100% valid.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_cradle_v6] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels the_cradle \
    --seeds 0:10001 \
    --workers 16 \
    --attempts 100 --max-variants 20

echo "[bundle_cradle_v6] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/the_cradle.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'the_cradle: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if pct < 99.9:
    print(f'WARN: below expected 99.9% threshold')
    sys.exit(1)
print('OK')
"
