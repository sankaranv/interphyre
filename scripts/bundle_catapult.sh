#!/bin/bash
#SBATCH --job-name=bundle_catapult
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_catapult_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_catapult_%j.err

# Full regeneration of catapult bundle with fixed oracle (ef5ed6b).
# Old bundle: 194 valid / 1000 seeds (stale oracle 8f3cee9).
# Fixed oracle (high-drop mechanism): ~60% valid rate expected.
# Seeds 0:17000 estimated to yield ~10 000 valid at 60% valid rate.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_catapult] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels catapult \
    --seeds 0:17000 \
    --workers 16 \
    --attempts 50 \
    --oracle-steps 500

echo "[bundle_catapult] Done at $(date)"

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
if n_valid < 9000:
    print('WARN: fewer than 9000 valid — may need wider seed range')
else:
    print('OK')
"
