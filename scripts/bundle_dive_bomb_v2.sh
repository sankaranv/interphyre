#!/bin/bash
#SBATCH --job-name=bundle_dive_bomb_v2
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_dive_bomb_v2_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_dive_bomb_v2_%j.err

# Bundle regen for dive_bomb v3: bumped to n_attempts=200.
# Prior regen (55545959): 9689/10001 = 96.9% at n=100. 312 impossible seeds.
# Increasing attempts to probe oracle false-negative rate at correct radius (0.3-0.6).

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_dive_bomb_v2] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels dive_bomb \
    --seeds 0:10001 \
    --workers 16 \
    --attempts 200

echo "[bundle_dive_bomb_v2] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/dive_bomb.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'dive_bomb: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if pct < 95:
    print(f'WARN: below expected 95% threshold')
    sys.exit(1)
print('OK')
"
