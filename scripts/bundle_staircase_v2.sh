#!/bin/bash
#SBATCH --job-name=bundle_staircase_v2
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_staircase_v2_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_staircase_v2_%j.err

# Bundle regen for staircase v3: n_attempts=500 to probe ceiling.
# Prior regen (55545953): 9595/10001 = 95.9% at n=150. Spot-check running to
# estimate false-negative rate at correct radius (0.33-0.48). If 95.9% is
# the true ceiling, accept. Otherwise higher attempts should improve it.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_staircase_v2] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels staircase \
    --seeds 0:10001 \
    --workers 16 \
    --attempts 500 --max-variants 10

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
if pct < 95:
    print(f'WARN: below expected 95% threshold')
    sys.exit(1)
print('OK')
"
