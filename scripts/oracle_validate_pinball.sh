#!/bin/bash
#SBATCH --job-name=oracle_val_pinball
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/oracle_val_pinball_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/oracle_val_pinball_%j.err

# Validates Gaussian x oracle improvement for pinball_machine.
# Tests on seeds 0:500 and measures avg_var vs baseline (2.055).
# 200-seed test already showed avg_var=1.60 (22% reduction).
# Decision criterion: avg_var drop >= 15% (to < 1.75) -> trigger full bundle regen.

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate
echo "[oracle_val_pinball] Starting at $(date)"

OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs
OUTFILE=$OUTDIR/pinball_val_${SLURM_JOB_ID}.json.lzma

python -u -m interphyre.validation._bundle \
    --levels pinball_machine \
    --seeds 0:500 \
    --workers 8 \
    --output $OUTFILE

echo "[oracle_val_pinball] Bundle done at $(date)"

python -u -c "
import lzma, json, numpy as np, sys
with lzma.open('$OUTFILE', 'rb') as f:
    data = json.load(f)
entries = data['entries']
valid = [e for e in entries if e['status'] == 'valid']
impossible = [e['seed'] for e in entries if e['status'] == 'impossible' and e['seed'] not in {e2['seed'] for e2 in valid}]
variants = [e['variant'] for e in valid]
avg_var = np.mean(variants)
pct_v0 = 100.0 * sum(1 for v in variants if v == 0) / len(variants)
p_eff = 1.0 / (1.0 + avg_var)
baseline = 2.055
pct_change = 100.0 * (baseline - avg_var) / baseline
print(f'pinball_machine oracle validation (500 seeds):')
print(f'  valid: {len(valid)}/500, impossible: {len(impossible)}')
print(f'  avg_var: {avg_var:.3f} (baseline: {baseline}, change: {pct_change:+.1f}%)')
print(f'  pct_var0: {pct_v0:.1f}%, p_eff: {p_eff:.3f}')
if impossible:
    print(f'  Impossible seeds: {impossible}')
if pct_change >= 15.0:
    print(f'  RESULT: IMPROVEMENT CONFIRMED (>= 15% drop) -> trigger bundle regen')
    sys.exit(0)
elif pct_change >= 5.0:
    print(f'  RESULT: MARGINAL improvement ({pct_change:.1f}%) -> investigate further')
    sys.exit(2)
else:
    print(f'  RESULT: NO IMPROVEMENT ({pct_change:.1f}%) -> oracle may need redesign')
    sys.exit(1)
"
