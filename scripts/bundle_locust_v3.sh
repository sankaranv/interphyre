#!/bin/bash
#SBATCH --job-name=bundle_locust_v3
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_locust_v3_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_locust_v3_%j.err

# Bundle regen for locust_swarm v3: oracle x-range anchored to green_ball.x.
# Prior bundle (v2): 96.6% at k=10, n=500. ~297 impossible seeds (p≈0.143 per variant).
# Root cause (oracle_physics_audit 2026-04-14):
#   Zone A used full-board x [-4.5, 4.5] but 94.4% of solutions ±1.5 of green_ball.x.
#   66.7% of x-budget wasted on near-zero-density regions → p=0.143 per variant.
# Fix: Zone A narrowed to [gb.x-1.5, gb.x+1.5]; Zone B (20%) full-board fallback.
# Expected p≈0.35; k=20 → model(k=20,p=0.35) ≈ 3 impossible seeds.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_locust_v3] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels locust_swarm \
    --seeds 0:10001 \
    --workers 16

echo "[bundle_locust_v3] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/locust_swarm.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'locust_swarm: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if pct < 98.5:
    print(f'WARN: below expected 98.5% threshold — investigate further')
    sys.exit(1)
print('OK')
"
