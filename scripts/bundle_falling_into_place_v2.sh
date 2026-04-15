#!/bin/bash
#SBATCH --job-name=bundle_falling_into_place_v2
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_falling_into_place_v2_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_falling_into_place_v2_%j.err

# Bundle regen for falling_into_place. Fix: oracle enforces oracle_steps=1000 (was 500, missed ~75% of solvable seeds). Expected ~100% with n_attempts=100.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_falling_into_place_v2] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels falling_into_place \
    --seeds 0:10001 \
    --workers 16 \
    --attempts 100 --oracle-steps 1000

echo "[bundle_falling_into_place_v2] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/falling_into_place.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'falling_into_place: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if pct < 99:
    print(f'WARN: below expected 99% threshold')
    sys.exit(1)
print('OK')
"
