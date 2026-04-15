#!/bin/bash
#SBATCH --job-name=cat_v6_merge
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cat_v6_merge_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cat_v6_merge_%j.err

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate
echo "[cat_v6_merge] Starting at $(date)"

CHUNKDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/catapult_v6_chunks
CHUNKS=$(ls $CHUNKDIR/cat_v6_*_*.json.lzma 2>/dev/null | sort)
echo "Chunks to merge: $CHUNKS"

for chunk in $CHUNKS; do
    echo "Merging $chunk..."
    python -u -m interphyre.validation._bundle \
        --levels catapult \
        --merge \
        --input $chunk \
        --workers 1
done

echo "[cat_v6_merge] Merge complete at $(date)"

python -u -c "
import lzma, json, numpy as np, sys
path = '$PROJECT/interphyre/data/levels/catapult.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
seeds = set(e['seed'] for e in entries)
valid_seeds = set(e['seed'] for e in entries if e['status'] == 'valid')
truly_impossible = sorted(s for s in seeds if s not in valid_seeds)
valid = [e for e in entries if e['status'] == 'valid']
variants = [e['variant'] for e in valid]
avg_var = np.mean(variants)
pct_v0 = 100.0 * sum(1 for v in variants if v == 0) / len(variants)
p_eff = 1.0 / (1.0 + avg_var)
print(f'catapult v6 bundle:')
print(f'  seeds: {len(seeds)}, valid: {len(valid_seeds)}, impossible: {len(truly_impossible)}')
print(f'  avg_var: {avg_var:.3f} (v5 baseline: 2.021), pct_v0: {pct_v0:.1f}%, p_eff: {p_eff:.3f}')
if truly_impossible:
    print(f'  Remaining impossible seeds ({len(truly_impossible)}): {truly_impossible[:30]}')
else:
    print(f'  OK: 0 impossible seeds')
"
