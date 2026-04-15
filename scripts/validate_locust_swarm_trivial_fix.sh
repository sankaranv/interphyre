#!/bin/bash
# 500-seed validation for locust_swarm trivial-rate fix.
# Prior trivial rate: 48.2% (measured 200 seeds × 10 variants).
# Prior avg_var: 2.332 (10001-seed bundle).
# Fix: chain 1 anchored to green_ball.x instead of fixed MIN_X + 0.2*W.
# Expected: trivial rate < 25%, avg_var < 2.0.

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/locust_trivial_val
mkdir -p "$OUTDIR"
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

sbatch \
    --job-name="locust_triv_val" \
    --partition=cpu-preempt \
    --account=pi_jensen_umass_edu \
    --cpus-per-task=16 \
    --mem=16G \
    --time=01:00:00 \
    --output="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/locust_triv_val_%j.out" \
    --error="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/locust_triv_val_%j.err" \
    --wrap="
        . $PROJECT/.venv/bin/activate
        cd $PROJECT

        # Step 1: Measure trivial rate on 200 seeds x 10 variants
        python -u -c \"
import numpy as np
from interphyre.levels import load_level
from interphyre.validation.checks import is_trivial
from interphyre.config import SimulationConfig

N_SEEDS = 200
N_VARIANTS = 10
config = SimulationConfig()

trivial_count = 0
total = 0
for seed in range(N_SEEDS):
    for variant in range(N_VARIANTS):
        level = load_level('locust_swarm', seed=seed, variant=variant)
        trivial = is_trivial(level, config)
        if trivial:
            trivial_count += 1
        total += 1
    if (seed + 1) % 50 == 0:
        print(f'  {seed+1}/{N_SEEDS} seeds — trivial so far: {trivial_count}/{total} ({trivial_count/total*100:.1f}%)')

trivial_rate = trivial_count / total
print(f'Trivial rate: {trivial_count}/{total} = {trivial_rate*100:.1f}%')
BASELINE_TRIVIAL = 0.482
print(f'Baseline: {BASELINE_TRIVIAL*100:.1f}% — improvement: {(BASELINE_TRIVIAL - trivial_rate)*100:.1f}pp')
min_avg_var = trivial_rate / (1 - trivial_rate) if trivial_rate < 1 else float('inf')
print(f'New min achievable avg_var (perfect oracle): {min_avg_var:.3f}')
\" 2>&1 | tee $OUTDIR/trivial_rate.txt

        # Step 2: Run 500-seed bundle with new level
        python -u -m interphyre.validation._bundle \
            --levels locust_swarm \
            --seeds 0:500 \
            --workers 16 \
            --attempts 500 \
            --output $OUTDIR/locust_trivial_val.json.lzma

        python -u -c \"
import lzma, json
with lzma.open('$OUTDIR/locust_trivial_val.json.lzma') as f:
    data = json.load(f)
entries = data['entries']
valid   = [e for e in entries if e['status'] == 'valid']
imp     = [e for e in entries if e['status'] == 'impossible']
seeds   = {e['seed'] for e in entries}
avg_var = sum(e['variant'] for e in valid) / len(valid) if valid else float('inf')
print(f'Seeds: {len(seeds)}, Valid: {len(valid)}, Impossible: {len(imp)}, avg_var={avg_var:.3f}')
BASELINE = 2.332
print(f'Baseline avg_var: {BASELINE:.3f}, improvement: {(BASELINE - avg_var):.3f} ({(BASELINE - avg_var)/BASELINE*100:.1f}%)')
if avg_var < BASELINE * 0.85:
    print(f'PASSED: >=15% improvement — trigger full regen')
else:
    print(f'BELOW THRESHOLD: avg_var {avg_var:.3f} > {BASELINE*0.85:.3f}')
\" 2>&1 | tee -a $OUTDIR/trivial_rate.txt
    "

echo "Submitted locust_swarm trivial-rate validation. Monitor: squeue -u \$USER"
echo "Log: /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/locust_triv_val_*.out"
