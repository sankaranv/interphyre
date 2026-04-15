#!/bin/bash
#SBATCH --job-name=bundle_flagpole_v2
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_flagpole_v2_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_flagpole_v2_%j.err

# Bundle regen for flagpole_sitta v2: cap oracle_steps at config.max_steps=1000.
# Prior bundle used _MIN_ORACLE_STEPS=1200, certifying solutions at steps 1001-1200
# that users cannot achieve within the 1000-step game window. Those are false positives.
# Fix: oracle now uses min(oracle_steps, config.max_steps). Passing --oracle-steps 1000
# ensures full user-visible coverage without exceeding the game time limit.
# Expected: ~100% (seeds needing >1000 steps are not user-achievable and correctly excluded).

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_flagpole_v2] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels flagpole_sitta \
    --seeds 0:10001 \
    --workers 16 \
    --oracle-steps 1000

echo "[bundle_flagpole_v2] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/flagpole_sitta.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
impossible = [e['seed'] for e in entries if e['status'] == 'impossible']
print(f'flagpole_sitta: {n_valid} valid / {n_seeds} seeds = {pct:.2f}%')
if impossible:
    print(f'  Impossible seeds ({len(impossible)}): {impossible[:20]}')
if pct < 99.5:
    print(f'WARN: below expected 99.5% threshold — investigate impossible seeds')
    sys.exit(1)
print('OK')
"
