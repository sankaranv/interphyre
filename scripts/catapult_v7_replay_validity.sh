#!/bin/bash
#SBATCH --job-name=cat_v7_replay
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cat_v7_replay_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cat_v7_replay_%j.err

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate
cd $PROJECT
echo "[cat_v7_replay] Starting at $(date)"

OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/catapult_v7
mkdir -p $OUTDIR

python -u -c "
import lzma, json, sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from interphyre.config import SimulationConfig
from interphyre.validation.oracles import _run_attempt, Box2DEngine
from interphyre.levels import load_level

BUNDLE_PATH = 'interphyre/data/levels/catapult.json.lzma'
REGEN_SEEDS_PATH = '$OUTDIR/seeds_to_regen.txt'
N_REPLAYS = 2   # evict if fails any replay
ORACLE_STEPS = 500

def check_entry(entry):
    seed = entry['seed']
    sol = [tuple(s) for s in entry['solution']]
    config = SimulationConfig()
    for _ in range(N_REPLAYS):
        level = load_level('catapult', seed=seed, variant=0)
        engine = Box2DEngine(level=level, config=config)
        if not _run_attempt(engine, level, sol, oracle_steps=ORACLE_STEPS):
            return seed, False
    return seed, True

with lzma.open(BUNDLE_PATH, 'rb') as f:
    data = json.load(f)

entries = data['entries']
valid_entries = [e for e in entries if e['status'] == 'valid']
print(f'Checking {len(valid_entries)} valid entries ({N_REPLAYS} replays each, oracle_steps={ORACLE_STEPS})...')

robust_seeds = set()
fragile_seeds = set()

with ProcessPoolExecutor(max_workers=16) as pool:
    futures = {pool.submit(check_entry, e): e['seed'] for e in valid_entries}
    for i, fut in enumerate(as_completed(futures)):
        seed, ok = fut.result()
        if ok:
            robust_seeds.add(seed)
        else:
            fragile_seeds.add(seed)
        if (i + 1) % 1000 == 0:
            print(f'  {i+1}/{len(valid_entries)}: robust={len(robust_seeds)}, fragile={len(fragile_seeds)}', flush=True)

all_seeds = {e['seed'] for e in entries}
impossible_seeds = all_seeds - {e['seed'] for e in entries if e['status'] == 'valid'}
regen_seeds = sorted(fragile_seeds | impossible_seeds)

print(f'Robust: {len(robust_seeds)}, Fragile: {len(fragile_seeds)}, Impossible: {len(impossible_seeds)}')
print(f'Total seeds to regen: {len(regen_seeds)}')
print(f'Fragile seeds: {sorted(fragile_seeds)[:30]}')

with open(REGEN_SEEDS_PATH, 'w') as f:
    for s in regen_seeds:
        f.write(f'{s}\n')
print(f'Regen seeds written to {REGEN_SEEDS_PATH}')

# Write cleaned bundle: keep only robust entries
seed_map = {}
for e in entries:
    seed = e['seed']
    if seed in fragile_seeds:
        continue
    existing = seed_map.get(seed)
    if existing is None:
        seed_map[seed] = e
    elif e['status'] == 'valid' and existing['status'] != 'valid':
        seed_map[seed] = e
    elif e['status'] == existing['status'] and e.get('variant', 999) < existing.get('variant', 999):
        seed_map[seed] = e

cleaned_entries = sorted(seed_map.values(), key=lambda e: e['seed'])
valid_after = sum(1 for e in cleaned_entries if e['status'] == 'valid')
print(f'Cleaned bundle: {len(cleaned_entries)} seeds, {valid_after} valid')

cleaned_data = {'schema_hash': data.get('schema_hash',''), 'oracle_commit': data.get('oracle_commit',''), 'entries': cleaned_entries}
with lzma.open(BUNDLE_PATH, 'wb') as f:
    f.write(json.dumps(cleaned_data).encode())
print('Cleaned bundle written.')
"

echo "[cat_v7_replay] Done at $(date)"
echo "Regen seeds: $OUTDIR/seeds_to_regen.txt"
