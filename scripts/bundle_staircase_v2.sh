#!/bin/bash
#SBATCH --job-name=bundle_staircase_v2
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_staircase_v2_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_staircase_v2_%j.err

# Bundle regen for staircase. Root cause was n_attempts=50 and narrow 0.05-unit valid
# windows. Gaussian+uniform mixture oracle. Expected ~99.7-99.8% with n_attempts=150
# and max-variants=10.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_staircase_v2] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels staircase \
    --seeds 0:10001 \
    --workers 16 \
    --attempts 150 --max-variants 10

echo "[bundle_staircase_v2] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/staircase.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'staircase: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if pct < 99:
    print(f'WARN: below expected 99% threshold')
    sys.exit(1)
print('OK')
"
