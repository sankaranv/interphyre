#!/bin/bash
# Exhaustive oracle search on the 253 catapult impossible seeds from v5 bundle.
# Tests expanded oracle (Zones A+B+C+D) with 2000 attempts and oracle_steps=1000.
# Goal: identify which seeds are genuinely impossible vs oracle misses.

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/catapult_impossible_audit
mkdir -p "$OUTDIR"
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

sbatch \
    --job-name="cat_imp_audit" \
    --partition=cpu-preempt \
    --account=pi_jensen_umass_edu \
    --cpus-per-task=16 \
    --mem=24G \
    --time=02:00:00 \
    --output="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cat_imp_audit_%j.out" \
    --error="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cat_imp_audit_%j.err" \
    --wrap="
        . $PROJECT/.venv/bin/activate
        cd $PROJECT

        # Extract impossible seeds from current catapult bundle
        python -u -c \"
import lzma, json
with lzma.open('$PROJECT/interphyre/data/levels/catapult.json.lzma') as f:
    data = json.load(f)
impossible = sorted({e['seed'] for e in data['entries'] if e['status'] == 'impossible'})
print(f'Impossible seeds: {len(impossible)}')
# Write seed list for the audit
with open('$OUTDIR/impossible_seeds.txt', 'w') as f:
    f.write('\n'.join(map(str, impossible)))
print('Wrote impossible_seeds.txt')
\"

        # Run exhaustive oracle on each impossible seed with 2000 attempts
        python -u -c \"
import lzma, json, numpy as np
from interphyre.config import SimulationConfig
from interphyre.validation.oracles import get_solver
from interphyre.levels import load_level

with open('$OUTDIR/impossible_seeds.txt') as f:
    seeds = [int(s.strip()) for s in f if s.strip()]

print(f'Auditing {len(seeds)} impossible seeds with expanded oracle (2000 attempts, oracle_steps=1000)...')

config = SimulationConfig()
solver = get_solver('catapult')

results = []
found = 0
for i, seed in enumerate(seeds):
    level = load_level('catapult', seed=seed)
    rng = np.random.default_rng(seed * 999983 + 42)
    # Use 2000 attempts for exhaustive search
    sol = solver(level, config, n_attempts=2000, oracle_steps=1000, rng=rng)
    status = 'found' if sol is not None else 'impossible'
    if sol is not None:
        found += 1
    results.append({'seed': seed, 'status': status, 'solution': sol})
    if (i + 1) % 25 == 0:
        pct_found = found / (i + 1) * 100
        print(f'  {i+1}/{len(seeds)} — found {found} solutions so far ({pct_found:.1f}% recovery)')

with open('$OUTDIR/impossible_audit_results.json', 'w') as f:
    json.dump(results, f)

found_seeds = [r['seed'] for r in results if r['status'] == 'found']
still_impossible = [r['seed'] for r in results if r['status'] == 'impossible']
print(f'\\nSummary: {len(seeds)} audited seeds')
print(f'  Found solutions: {len(found_seeds)} ({len(found_seeds)/len(seeds)*100:.1f}%)')
print(f'  Still impossible: {len(still_impossible)} ({len(still_impossible)/len(seeds)*100:.1f}%)')
print(f'  Recovery rate: {len(found_seeds)/len(seeds)*100:.1f}%')
print(f'Found seeds: {found_seeds[:20]}...' if len(found_seeds) > 20 else f'Found seeds: {found_seeds}')
\"
    "

echo "Submitted catapult impossible-seed audit. Monitor: squeue -u \$USER"
echo "Log: /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cat_imp_audit_*.out"
