#!/bin/bash
#SBATCH --job-name=oracle_test
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/oracle_test_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/oracle_test_%j.err

# Validates Gaussian x-sampling oracle improvement for locust_swarm and pinball_machine.
# Tests on seeds 0:200 with n_attempts=500 and measures per-variant hit rate p.
# Expected: locust_swarm p: 0.35→~0.52; pinball_machine p: 0.332→~0.55.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs
source $PROJECT/.venv/bin/activate

echo "[oracle_test] Starting at $(date)"

# Run 200-seed test bundles into temp files (not overwriting production bundles).
TMPDIR=$(mktemp -d)
echo "Temp dir: $TMPDIR"

for level in locust_swarm pinball_machine; do
    echo "Testing $level (seeds 0:200, workers=8)..."
    python -u -m interphyre.validation._bundle \
        --levels $level \
        --seeds 0:200 \
        --workers 8 \
        --output $TMPDIR/${level}_test.json.lzma
    echo "Done: $level"
done

echo "[oracle_test] Done at $(date)"

# Compute per-variant hit rates from test bundles.
python -u -c "
import lzma, json, sys
import numpy as np

tmpdir = '$TMPDIR'
results = {}
for level in ['locust_swarm', 'pinball_machine']:
    path = tmpdir + '/' + level + '_test.json.lzma'
    with lzma.open(path, 'rb') as f:
        data = json.load(f)
    entries = data['entries']
    valid = [e for e in entries if e['status'] == 'valid']
    impossible = [e for e in entries if e['status'] == 'impossible']
    n_total = len(entries)
    n_valid = len(valid)

    # Per-variant distribution
    variants = [e['variant'] for e in valid]
    pct_v0 = 100.0 * sum(1 for v in variants if v == 0) / n_valid if n_valid > 0 else 0
    avg_var = sum(variants) / n_valid if n_valid > 0 else 0

    # Effective p per variant from geometric decay model
    # E[variant] = (1-p)/p => p = 1/(1+E[variant])
    p_effective = 1.0 / (1.0 + avg_var) if avg_var >= 0 else 0

    print(f'{level}: {n_valid}/{n_total} valid ({100.0*n_valid/n_total:.1f}%)')
    print(f'  var=0: {pct_v0:.1f}%, avg_var={avg_var:.2f}')
    print(f'  Inferred p_effective per variant: {p_effective:.3f}')
    print(f'  Impossible: {[e[\"seed\"] for e in impossible]}')
    results[level] = {'p': p_effective, 'avg_var': avg_var, 'pct_v0': pct_v0}
    print()

# Check improvements
print('=== Summary ===')
expected = {'locust_swarm': {'old_p': 0.35, 'new_p_expected': 0.50},
            'pinball_machine': {'old_p': 0.332, 'new_p_expected': 0.50}}
all_ok = True
for level, exp in expected.items():
    p = results[level]['p']
    print(f'{level}: p={p:.3f} (was {exp[\"old_p\"]}, expected ~{exp[\"new_p_expected\"]}+)')
    if p < exp['old_p']:
        print(f'  WARNING: p DECREASED — Gaussian sampling may have hurt coverage!')
        all_ok = False
    elif p >= exp['new_p_expected']:
        print(f'  OK: improvement confirmed')
    else:
        print(f'  MARGINAL: some improvement but below expected')

rm -rf '$TMPDIR'
sys.exit(0 if all_ok else 1)
"
