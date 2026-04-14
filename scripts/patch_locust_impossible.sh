#!/bin/bash
#SBATCH --job-name=patch_locust
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/patch_locust_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/patch_locust_%j.err

# Targeted patch for 5 remaining impossible seeds in locust_swarm v5.
# Analysis (2026-04-14):
#   The 5 seeds (1063, 2317, 4365, 4451, 8467) exhausted max_variants=50 in v5.
#   Cause: some seeds have 30-60% trivial-variant rate, leaving few non-trivial
#   variants out of 50 trials. At p=0.35/non-trivial variant, P(all 20 non-trivial
#   variants miss) ≈ (0.65)^20 ≈ 0.0003 per seed → ~3 expected failures in 10001.
#   Fix: n_attempts=2000 (raises p per variant from 0.35→~0.70) and
#   max_variants=100 (doubles non-trivial variant budget for high-trivial-rate seeds).
# Seeds 4451 (found at v=47) and 8467 (found at v=40) confirmed solvable in prior
# targeted tests but slipped through probabilistic failure in full bundle regen.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate

echo "[patch_locust] Starting at $(date)"

for seed_start in 1063 2317 4365 4451 8467; do
    seed_stop=$((seed_start + 1))
    echo "  locust_swarm seed $seed_start..."
    python -u -m interphyre.validation._bundle \
        --levels locust_swarm \
        --seeds ${seed_start}:${seed_stop} \
        --merge \
        --workers 1 \
        --attempts 2000 \
        --max-variants 100
done

echo "[patch_locust] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/locust_swarm.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
impossible = [e['seed'] for e in entries if e['status'] == 'impossible']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'locust_swarm: {n_valid}/{n_seeds} = {pct:.4f}%')
if impossible:
    print(f'  Still impossible: {impossible}')
    sys.exit(1)
print('OK — 0 impossible seeds')
"
