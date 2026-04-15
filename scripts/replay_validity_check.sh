#!/bin/bash
#SBATCH --job-name=replay_check
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/replay_check_%x_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/replay_check_%x_%j.err

# Required env var: LEVEL_NAME
# Optional: N_REPLAYS (default 5), ORACLE_STEPS (default 500)

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate
cd $PROJECT

N_REPLAYS=${N_REPLAYS:-5}
ORACLE_STEPS=${ORACLE_STEPS:-500}
OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/replay_validity
mkdir -p $OUTDIR

echo "[replay_check] Level=${LEVEL_NAME} N_REPLAYS=${N_REPLAYS} ORACLE_STEPS=${ORACLE_STEPS} at $(date)"

python -u -c "
import lzma, json
from concurrent.futures import ProcessPoolExecutor, as_completed
from interphyre.config import SimulationConfig
from interphyre.validation.oracles import _run_attempt, Box2DEngine
from interphyre.levels import load_level

LEVEL = '${LEVEL_NAME}'
N_REPLAYS = ${N_REPLAYS}
ORACLE_STEPS = ${ORACLE_STEPS}
OUTDIR = '${OUTDIR}'

BUNDLE_PATH = f'interphyre/data/levels/{LEVEL}.json.lzma'
with lzma.open(BUNDLE_PATH, 'rb') as f:
    data = json.load(f)

entries = data['entries']
valid_entries = [e for e in entries if e['status'] == 'valid']
print(f'[{LEVEL}] {len(valid_entries)} valid entries, {N_REPLAYS} replays each at oracle_steps={ORACLE_STEPS}')

def check_entry(entry):
    seed = entry['seed']
    variant = entry['variant']
    sol = [tuple(s) for s in entry['solution']]
    config = SimulationConfig()
    passes = 0
    for _ in range(N_REPLAYS):
        level = load_level(LEVEL, seed=seed, variant=variant)
        engine = Box2DEngine(level=level, config=config)
        if _run_attempt(engine, level, sol, oracle_steps=ORACLE_STEPS):
            passes += 1
    return seed, variant, passes

robust = []
fragile = []
with ProcessPoolExecutor(max_workers=16) as pool:
    futures = {pool.submit(check_entry, e): e['seed'] for e in valid_entries}
    for i, fut in enumerate(as_completed(futures)):
        seed, variant, passes = fut.result()
        if passes == N_REPLAYS:
            robust.append((seed, variant, passes))
        else:
            fragile.append((seed, variant, passes))
        if (i + 1) % 1000 == 0:
            print(f'  {i+1}/{len(valid_entries)}: robust={len(robust)}, fragile={len(fragile)}', flush=True)

fragile_seeds = sorted(s for s, v, p in fragile)
all_seeds = {e['seed'] for e in entries}
impossible_seeds = sorted(all_seeds - {e['seed'] for e in entries if e['status'] == 'valid'})
regen_seeds = sorted(set(fragile_seeds) | set(impossible_seeds))

pass_rates = [p for _, _, p in fragile]
avg_passes = sum(p for _, _, p in fragile) / len(fragile) if fragile else 0

print(f'')
print(f'=== {LEVEL} REPLAY VALIDITY REPORT ===')
print(f'  Valid entries: {len(valid_entries)}')
print(f'  Robust (pass {N_REPLAYS}/{N_REPLAYS}): {len(robust)} ({100*len(robust)/len(valid_entries):.1f}%)')
print(f'  Fragile (fail >=1 replay): {len(fragile)} ({100*len(fragile)/len(valid_entries):.1f}%)')
print(f'    Pass rate distribution among fragile: ' + str({i: pass_rates.count(i) for i in range(N_REPLAYS+1) if pass_rates.count(i) > 0}))
print(f'  Impossible seeds (no valid variant): {len(impossible_seeds)}')
print(f'  Total seeds to regen: {len(regen_seeds)}')
if fragile_seeds:
    print(f'  First 20 fragile seeds: {fragile_seeds[:20]}')

# Write regen seeds list
regen_path = f'{OUTDIR}/{LEVEL}_regen_seeds.txt'
with open(regen_path, 'w') as f:
    for s in regen_seeds:
        f.write(f'{s}\n')
print(f'  Regen seeds written to {regen_path}')

# Write summary JSON for aggregation
import json as json2
summary = {
    'level': LEVEL,
    'n_valid': len(valid_entries),
    'n_robust': len(robust),
    'n_fragile': len(fragile),
    'fragile_rate': len(fragile) / len(valid_entries) if valid_entries else 0,
    'n_impossible': len(impossible_seeds),
    'n_regen': len(regen_seeds),
    'fragile_seeds': fragile_seeds,
    'impossible_seeds': impossible_seeds,
}
summary_path = f'{OUTDIR}/{LEVEL}_summary.json'
with open(summary_path, 'w') as f:
    json2.dump(summary, f)
print(f'  Summary written to {summary_path}')
"

echo "[replay_check] ${LEVEL_NAME} done at $(date)"
