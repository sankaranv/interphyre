#!/bin/bash
#SBATCH --job-name=staircase_v2_val
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/staircase_v2_val_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/staircase_v2_val_%j.err

# Re-validates staircase oracle after revert to uniform x sampling.
# Two-Gaussian x gave only 4.3% improvement (solution x std=2.22, nearly uniform).
# Reverted to full-board uniform x; validates the reverted oracle is at least as good.

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate
echo "[staircase_v2_val] Starting at $(date)"

OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs
OUTFILE=$OUTDIR/staircase_v2_val_${SLURM_JOB_ID}.json.lzma

python -u -m interphyre.validation._bundle \
    --levels staircase \
    --seeds 0:500 \
    --workers 8 \
    --output $OUTFILE

echo "[staircase_v2_val] Done at $(date)"

python -u -c "
import lzma, json, numpy as np
with lzma.open('$OUTFILE', 'rb') as f:
    data = json.load(f)
entries = data['entries']
valid = [e for e in entries if e['status'] == 'valid']
variants = [e['variant'] for e in valid]
avg_var = np.mean(variants)
pct_v0 = 100.0 * sum(1 for v in variants if v == 0) / len(variants)
p_eff = 1.0 / (1.0 + avg_var)
print(f'staircase v2 (uniform x) oracle validation (500 seeds):')
print(f'  valid: {len(valid)}/500')
print(f'  avg_var: {avg_var:.3f} (original baseline: 1.957, Gaussian x: 1.872)')
print(f'  pct_var0: {pct_v0:.1f}%, p_eff: {p_eff:.3f}')
"
