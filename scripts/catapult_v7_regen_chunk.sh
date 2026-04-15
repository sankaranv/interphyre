#!/bin/bash
#SBATCH --job-name=cat_v7_regen
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cat_v7_regen_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cat_v7_regen_%j.err

# Required env vars:
#   CHUNK_IDX   — 0-based chunk index
#   N_CHUNKS    — total number of chunks
#   SEEDS_FILE  — path to seeds_to_regen.txt

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate
cd $PROJECT
echo "[cat_v7_regen chunk=${CHUNK_IDX}/${N_CHUNKS}] Starting at $(date)"

OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/catapult_v7
mkdir -p $OUTDIR
OUTFILE=$OUTDIR/cat_v7_chunk_${CHUNK_IDX}_${SLURM_JOB_ID}.json.lzma

python -u -c "
import lzma, json, sys, numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from interphyre.config import SimulationConfig
from interphyre.validation.oracles import get_solver
from interphyre.levels import load_level

SEEDS_FILE = '${SEEDS_FILE}'
CHUNK_IDX = int('${CHUNK_IDX}')
N_CHUNKS = int('${N_CHUNKS}')
OUTFILE = '${OUTFILE}'
MAX_VARIANTS = 10
N_ATTEMPTS = 300
ORACLE_STEPS = 500

with open(SEEDS_FILE) as f:
    all_seeds = [int(line.strip()) for line in f if line.strip()]

# This chunk's slice
chunk_seeds = [s for i, s in enumerate(all_seeds) if i % N_CHUNKS == CHUNK_IDX]
print(f'Chunk {CHUNK_IDX}/{N_CHUNKS}: {len(chunk_seeds)} seeds (of {len(all_seeds)} total)')

config = SimulationConfig()
solver = get_solver('catapult')

def validate_seed(seed):
    rng = np.random.default_rng(seed * 999983 + 13)
    for variant in range(MAX_VARIANTS):
        level = load_level('catapult', seed=seed, variant=variant)
        sol = solver(level, config, n_attempts=N_ATTEMPTS, oracle_steps=ORACLE_STEPS, rng=rng)
        if sol is not None:
            return {'seed': seed, 'variant': variant, 'status': 'valid',
                    'scene': {k: v.__dict__ for k, v in level.objects.items()},
                    'solution': [list(s) for s in sol]}
    return {'seed': seed, 'variant': MAX_VARIANTS - 1, 'status': 'impossible', 'scene': None, 'solution': None}

entries = []
with ProcessPoolExecutor(max_workers=16) as pool:
    futures = {pool.submit(validate_seed, s): s for s in chunk_seeds}
    for i, fut in enumerate(as_completed(futures)):
        entry = fut.result()
        entries.append(entry)
        if (i + 1) % 50 == 0:
            valid = sum(1 for e in entries if e['status'] == 'valid')
            print(f'  {i+1}/{len(chunk_seeds)}: valid={valid}', flush=True)

valid = sum(1 for e in entries if e['status'] == 'valid')
impossible = sum(1 for e in entries if e['status'] == 'impossible')
print(f'Chunk {CHUNK_IDX} done: {valid} valid, {impossible} impossible')

with lzma.open(OUTFILE, 'wb') as f:
    f.write(json.dumps({'schema_hash': '', 'oracle_commit': '', 'entries': entries}).encode())
print(f'Written: {OUTFILE}')
"

echo "[cat_v7_regen chunk=${CHUNK_IDX}/${N_CHUNKS}] Done at $(date)"
