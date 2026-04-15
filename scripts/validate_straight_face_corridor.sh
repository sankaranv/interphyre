#!/bin/bash
# 500-seed validation for straight_face corridor oracle (v3).
# Baseline avg_var: 1.362 (old oracle, full-board x).
# v3 fix: 70% corridor sampling between green_ball.x and purple_pad.x, 30% fallback.
# Expected p improvement: 0.42 → 0.60-0.65 per variant → avg_var ~0.54-0.67.
# Threshold for full regen: >=15% improvement = avg_var <= 1.158.

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/straight_face_corridor_val
mkdir -p "$OUTDIR"
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

sbatch \
    --job-name="sf_corridor_val" \
    --partition=cpu-preempt \
    --account=pi_jensen_umass_edu \
    --cpus-per-task=16 \
    --mem=16G \
    --time=01:00:00 \
    --output="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/sf_corridor_val_%j.out" \
    --error="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/sf_corridor_val_%j.err" \
    --wrap="
        . $PROJECT/.venv/bin/activate
        python -u -m interphyre.validation._bundle \
            --levels straight_face \
            --seeds 0:500 \
            --workers 16 \
            --attempts 100 \
            --output $OUTDIR/sf_corridor_val.json.lzma

        python -u -c \"
import lzma, json, numpy as np
with lzma.open('$OUTDIR/sf_corridor_val.json.lzma') as f:
    data = json.load(f)
entries = data['entries']
valid   = [e for e in entries if e['status'] == 'valid']
imp     = [e for e in entries if e['status'] == 'impossible']
avg_var = sum(e['variant'] for e in valid) / len(valid) if valid else float('inf')
print(f'Seeds: {len({e[\"seed\"] for e in entries})}, Valid: {len(valid)}, Impossible: {len(imp)}, avg_var={avg_var:.3f}')
BASELINE = 1.362
THRESHOLD = BASELINE * 0.85
print(f'Baseline: {BASELINE:.3f}, 15%% threshold: {THRESHOLD:.3f}')
if avg_var <= THRESHOLD:
    print(f'PASSED: avg_var {avg_var:.3f} <= {THRESHOLD:.3f} — trigger full regen')
else:
    print(f'BELOW THRESHOLD: avg_var {avg_var:.3f} > {THRESHOLD:.3f}')
\"
    "

echo "Submitted straight_face corridor validation. Monitor: squeue -u \$USER"
echo "Log: /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/sf_corridor_val_*.out"
