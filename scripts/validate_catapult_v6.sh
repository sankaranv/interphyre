#!/bin/bash
# 500-seed validation for catapult v6 (basket x = arm_right + 2.5).
# If impossible rate ≈ 0%, proceed to full 10001-seed regen.

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/catapult_v6_val
mkdir -p "$OUTDIR"
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

sbatch \
    --job-name="catapult_v6_val" \
    --partition=cpu-preempt \
    --account=pi_jensen_umass_edu \
    --cpus-per-task=16 \
    --mem=16G \
    --time=01:00:00 \
    --output="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/catapult_v6_val_%j.out" \
    --error="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/catapult_v6_val_%j.err" \
    --wrap="
        . $PROJECT/.venv/bin/activate
        python -u -m interphyre.validation._bundle \
            --levels catapult \
            --seeds 0:500 \
            --workers 16 \
            --attempts 500 \
            --oracle-steps 1000 \
            --output $OUTDIR/catapult_v6_val.json.lzma

        python -u -c \"
import lzma, json
with lzma.open('$OUTDIR/catapult_v6_val.json.lzma') as f:
    data = json.load(f)
entries = data['entries']
valid   = [e for e in entries if e['status'] == 'valid']
imp     = [e for e in entries if e['status'] == 'impossible']
seeds   = {e['seed'] for e in entries}
avg_var = sum(e['variant'] for e in valid) / len(valid) if valid else float('inf')
print(f'Seeds: {len(seeds)}, Valid: {len(valid)}, Impossible: {len(imp)}, avg_var={avg_var:.3f}')
print(f'Impossible rate: {100.0*len(imp)/len(seeds):.2f}%')
if imp:
    print(f'Impossible seeds: {sorted(e[\"seed\"] for e in imp)[:20]} ...')
    assert False, f'FAIL: {len(imp)} impossible seeds remain'
print('VALIDATION PASSED: 0 impossible seeds in 500-seed test')
\"
    "

echo "Submitted catapult v6 validation job. Monitor: squeue -u \$USER"
echo "Log: /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/catapult_v6_val_*.out"
