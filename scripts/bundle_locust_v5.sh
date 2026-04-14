#!/bin/bash
#SBATCH --job-name=bundle_locust_v5
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_locust_v5_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_locust_v5_%j.err

# Bundle regen for locust_swarm v5: step range [0.5,1.55] → [1.5,3.0].
# Prior regen (v4): 9916/10001 = 99.2% (85 impossible seeds).
# Root cause (audit 2026-04-14):
#   - 85 impossible seeds confirmed genuine geometric barriers via 500-attempt full-board
#     grid search across 10+ variants — 0/85 seeds found any solution.
#   - Step distribution IDENTICAL between impossible and valid seeds (~93% steps < 1.5).
#   - Root: random walk sometimes generates chains spanning full width at some y-height.
#   - Passability threshold: gap = step - 2*star_radius = step - 0.5 > 1.0 (ball diameter).
#     Requires step > 1.5. Old min_step=0.5 meant 93% of gaps were impassable.
# Fix: step = rng.uniform(1.5, 3.0) — min_step=1.5 guarantees adjacent stars passable.
#   max_step=3.0 allows natural sparse-to-dense variation.
#   Full regen required (RNG sequence changes).
# Expected: ~99.9%+ valid (complete barriers nearly eliminated).

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_locust_v5] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels locust_swarm \
    --seeds 0:10001 \
    --workers 16

echo "[bundle_locust_v5] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/locust_swarm.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
impossible = [e for e in entries if e['status'] == 'impossible']
print(f'locust_swarm: {n_valid} valid / {n_seeds} seeds = {pct:.2f}%')
if impossible:
    print(f'  Impossible count: {len(impossible)}, first few: {[e[\"seed\"] for e in impossible[:10]]}')
if pct < 99.5:
    print(f'WARN: below expected 99.5% threshold')
    sys.exit(1)
print('OK')
"
