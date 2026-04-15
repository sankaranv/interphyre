#!/bin/bash
#SBATCH --job-name=bundle_catapult_v4
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=06:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_catapult_v4_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_catapult_v4_%j.err

# Bundle regen for catapult v4: oracle_steps 500→1000.
# Prior regen (v3): 5192/10001 = 51.9% (4809 impossible seeds).
# Root cause (audit 2026-04-14):
#   - Full-board test with oracle_steps=1000 recovered 8/20 = 40% of impossible seeds.
#   - 5/8 recoveries FAILED at oracle_steps=500 — trajectory not completed in time.
#   - Catapult throw takes 8-17s simulated (arm rotation + green ball flight to basket).
#   - 500 steps × (1/60)s = 8.3s is insufficient for slow-launch trajectories.
# Fix: oracle_steps 500→1000 (16.7s simulation per attempt).
#   n_attempts 400→500, max_variants 10→20 (register_defaults updated).
# Expected: ~70-75% valid (40%+ of 4809 false negatives recovered).
# Note: time limit raised to 6h (1000 oracle_steps × 500 attempts × 20 variants = 10M steps/seed).

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_catapult_v4] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels catapult \
    --seeds 0:10001 \
    --workers 16 \
    --oracle-steps 1000

echo "[bundle_catapult_v4] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/catapult.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
impossible = [e for e in entries if e['status'] == 'impossible']
print(f'catapult: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if impossible:
    print(f'  Impossible count: {len(impossible)}, first few: {[e[\"seed\"] for e in impossible[:10]]}')
if pct < 60.0:
    print(f'WARN: below expected 60% threshold')
    sys.exit(1)
print('OK')
"
