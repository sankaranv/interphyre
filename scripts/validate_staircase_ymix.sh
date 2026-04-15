#!/bin/bash
# 500-seed validation for staircase y-mixture oracle.
# Baseline avg_var: 1.957. Threshold for full regen: >=15% improvement = avg_var <= 1.663.

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/staircase_ymix_val
mkdir -p "$OUTDIR"
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

sbatch \
    --job-name="staircase_ymix" \
    --partition=cpu-preempt \
    --account=pi_jensen_umass_edu \
    --cpus-per-task=16 \
    --mem=16G \
    --time=01:00:00 \
    --output="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/staircase_ymix_%j.out" \
    --error="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/staircase_ymix_%j.err" \
    --wrap="
        . $PROJECT/.venv/bin/activate
        python -u -m interphyre.validation._bundle \
            --levels staircase \
            --seeds 0:500 \
            --workers 16 \
            --attempts 500 \
            --output $OUTDIR/staircase_ymix.json.lzma

        python -u -c \"
import lzma, json
with lzma.open('$OUTDIR/staircase_ymix.json.lzma') as f:
    data = json.load(f)
entries = data['entries']
valid   = [e for e in entries if e['status'] == 'valid']
imp     = [e for e in entries if e['status'] == 'impossible']
seeds   = {e['seed'] for e in entries}
avg_var = sum(e['variant'] for e in valid) / len(valid) if valid else float('inf')
print(f'Seeds: {len(seeds)}, Valid: {len(valid)}, Impossible: {len(imp)}, avg_var={avg_var:.3f}')
BASELINE = 1.957
THRESHOLD = BASELINE * 0.85  # 15% improvement
print(f'Baseline avg_var: {BASELINE:.3f}, 15% threshold: {THRESHOLD:.3f}')
if avg_var <= THRESHOLD:
    print(f'PASSED: avg_var {avg_var:.3f} <= {THRESHOLD:.3f} — trigger full regen')
else:
    print(f'BELOW THRESHOLD: avg_var {avg_var:.3f} > {THRESHOLD:.3f} — oracle at floor')
\"
    "

echo "Submitted staircase y-mixture validation. Monitor: squeue -u \$USER"
echo "Log: /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/staircase_ymix_*.out"
