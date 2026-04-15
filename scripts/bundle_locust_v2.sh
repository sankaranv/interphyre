#!/bin/bash
#SBATCH --job-name=bundle_locust_swarm_v2
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_locust_swarm_v2_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_locust_swarm_v2_%j.err

# Bundle regen for locust_swarm v3: n_attempts=500 --max-variants 10.
# Prior run (55545951): 6948/10001 = 69.5% at n=100. Spot-check shows 25% false-negative
# rate — seeds solvable at n=500 but missed at n=100. Oracle zones cover correct positions
# (calibrated analysis confirms radius=0.3-0.6 solutions in Zone A/B) — just need more
# attempts. Expected ~77% after improvement from false-negative recovery.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_locust_swarm_v2] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels locust_swarm \
    --seeds 0:10001 \
    --workers 16 \
    --attempts 500 --max-variants 10

echo "[bundle_locust_swarm_v2] Done at $(date)"

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
if pct < 70:
    print(f'WARN: below expected 70% threshold')
    sys.exit(1)
print('OK')
"
