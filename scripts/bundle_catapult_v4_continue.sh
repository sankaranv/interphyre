#!/bin/bash
#SBATCH --job-name=bundle_catapult_v4c
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_catapult_v4c_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_catapult_v4c_%j.err

# Continuation job for bundle_catapult_v4 (55559843).
# The main job hits the 6-hour wall at ~8640/10001 seeds (24 seeds/min).
# --merge skips seeds already in the checkpoint bundle and fills the rest.
# oracle-steps 1000 = config.max_steps — oracle self-caps at min(1000, 1000).

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_catapult_v4c] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels catapult \
    --seeds 0:10001 \
    --merge \
    --workers 16 \
    --oracle-steps 1000

echo "[bundle_catapult_v4c] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/catapult.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
impossible = [e['seed'] for e in entries if e['status'] == 'impossible']
print(f'catapult: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if impossible:
    print(f'  Impossible count: {len(impossible)}, first 20: {sorted(impossible)[:20]}')
if n_seeds < 10001:
    print(f'WARN: only {n_seeds} seeds in bundle — still missing {10001 - n_seeds}')
    sys.exit(1)
if pct < 60.0:
    print(f'WARN: below expected 60% threshold')
    sys.exit(1)
print('OK')
"
