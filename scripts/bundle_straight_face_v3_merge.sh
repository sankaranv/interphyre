#!/bin/bash
#SBATCH --job-name=sf_v3_merge
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/sf_v3_merge_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/sf_v3_merge_%j.err

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate
echo "[sf_v3_merge] Starting at $(date)"

CHUNKDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/sf_v3_chunks
CHUNKS=$(ls $CHUNKDIR/sf_v3_*_*.json.lzma 2>/dev/null | sort)
echo "Chunks to merge: $CHUNKS"

for chunk in $CHUNKS; do
    echo "Merging $chunk..."
    python -u -m interphyre.validation._bundle \
        --levels straight_face \
        --merge \
        --input $chunk \
        --workers 1
done

echo "[sf_v3_merge] Merge complete at $(date)"

python -u -c "
import lzma, json, numpy as np, sys
path = '$PROJECT/interphyre/data/levels/straight_face.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
seeds = set(e['seed'] for e in entries)
valid_seeds = set(e['seed'] for e in entries if e['status'] == 'valid')
truly_impossible = sorted(s for s in seeds if s not in valid_seeds)
valid = [e for e in entries if e['status'] == 'valid']
avg_var = np.mean([e['variant'] for e in valid])
p_eff = 1.0 / (1.0 + avg_var)
print(f'straight_face v3 bundle:')
print(f'  seeds: {len(seeds)}, valid: {len(valid_seeds)}, impossible: {len(truly_impossible)}')
print(f'  avg_var: {avg_var:.3f} (baseline: 1.362), p_eff: {p_eff:.3f}')
if truly_impossible:
    print(f'  Impossible seeds: {truly_impossible[:20]}')
else:
    print(f'  OK: 0 impossible seeds')
"
