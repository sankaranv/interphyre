#!/bin/bash
#SBATCH --job-name=robust_regen
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/robust_regen_%x_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/robust_regen_%x_%j.err

# Required env vars: LEVEL_NAME, SEEDS_FILE, CHUNK_IDX, N_CHUNKS
# Optional: N_VERIFY (default 5), N_ATTEMPTS (default 200), MAX_TRIES (default 10)
# Two-stage oracle: tries ORACLE_STEPS_FAST (default 500) first, falls back to ORACLE_STEPS_FULL (default 1000).
# Solutions robust at 500 steps are guaranteed robust at 1000 (goal contact within 500 => still succeeds at 1000).

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate
cd $PROJECT

N_VERIFY=${N_VERIFY:-5}
N_ATTEMPTS=${N_ATTEMPTS:-200}
MAX_TRIES=${MAX_TRIES:-10}
ORACLE_STEPS_FAST=${ORACLE_STEPS_FAST:-500}
ORACLE_STEPS_FULL=${ORACLE_STEPS_FULL:-1000}
OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/robust_regen/${LEVEL_NAME}
mkdir -p $OUTDIR
OUTFILE=$OUTDIR/${LEVEL_NAME}_chunk${CHUNK_IDX}_${SLURM_JOB_ID}.json.lzma

echo "[robust_regen] ${LEVEL_NAME} chunk=${CHUNK_IDX}/${N_CHUNKS} N_VERIFY=${N_VERIFY} N_ATTEMPTS=${N_ATTEMPTS} MAX_TRIES=${MAX_TRIES} fast=${ORACLE_STEPS_FAST} full=${ORACLE_STEPS_FULL} at $(date)"

python -u -c "
import lzma, json, numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from interphyre.config import SimulationConfig
from interphyre.validation.oracles import get_solver, _run_attempt, Box2DEngine, get_default_max_variants
from interphyre.levels import load_level

LEVEL = '${LEVEL_NAME}'
SEEDS_FILE = '${SEEDS_FILE}'
CHUNK_IDX = int('${CHUNK_IDX}')
N_CHUNKS = int('${N_CHUNKS}')
OUTFILE = '${OUTFILE}'
N_VERIFY = int('${N_VERIFY}')
N_ATTEMPTS = int('${N_ATTEMPTS}')
MAX_TRIES = int('${MAX_TRIES}')   # max oracle calls per variant trying to find a robust solution
ORACLE_STEPS_FAST = int('${ORACLE_STEPS_FAST}')
ORACLE_STEPS_FULL = int('${ORACLE_STEPS_FULL}')

with open(SEEDS_FILE) as f:
    all_seeds = [int(l.strip()) for l in f if l.strip()]
chunk_seeds = [s for i, s in enumerate(all_seeds) if i % N_CHUNKS == CHUNK_IDX]
print(f'[{LEVEL}] chunk {CHUNK_IDX}/{N_CHUNKS}: {len(chunk_seeds)} seeds')

config = SimulationConfig()
solver = get_solver(LEVEL)
try:
    max_variants = get_default_max_variants(LEVEL)
except Exception:
    max_variants = 10

def find_robust_solution(level, rng, oracle_steps):
    '''Run oracle up to MAX_TRIES times, accepting only solutions that pass all N_VERIFY replays.
    Solutions robust at oracle_steps=500 are guaranteed robust at 1000 (goal contact within 500
    steps is sufficient condition for success within 1000 steps).'''
    for _ in range(MAX_TRIES):
        sol = solver(level, config, n_attempts=N_ATTEMPTS, oracle_steps=oracle_steps, rng=rng)
        if sol is None:
            return None
        robust = all(
            _run_attempt(Box2DEngine(level=level, config=config), level, sol, oracle_steps=oracle_steps)
            for _ in range(N_VERIFY)
        )
        if robust:
            return sol
    return None

def validate_seed(seed):
    rng = np.random.default_rng(seed * 999983 + 31)
    for variant in range(max_variants):
        level = load_level(LEVEL, seed=seed, variant=variant)
        # Stage 1: fast search at ORACLE_STEPS_FAST — half the simulation cost per attempt.
        sol = find_robust_solution(level, rng, oracle_steps=ORACLE_STEPS_FAST)
        if sol is None:
            # Stage 2: fall back to full horizon for seeds that need more simulation time.
            sol = find_robust_solution(level, rng, oracle_steps=ORACLE_STEPS_FULL)
        if sol is not None:
            return {
                'seed': seed, 'variant': variant, 'status': 'valid',
                'scene': {k: v.__dict__ for k, v in level.objects.items()},
                'solution': [list(s) for s in sol],
            }
    return {'seed': seed, 'variant': max_variants - 1, 'status': 'impossible', 'scene': None, 'solution': None}

entries = []
with ProcessPoolExecutor(max_workers=16) as pool:
    futures = {pool.submit(validate_seed, s): s for s in chunk_seeds}
    for i, fut in enumerate(as_completed(futures)):
        entry = fut.result()
        entries.append(entry)
        if (i + 1) % 100 == 0:
            valid = sum(1 for e in entries if e['status'] == 'valid')
            print(f'  {i+1}/{len(chunk_seeds)}: valid={valid}', flush=True)

valid = sum(1 for e in entries if e['status'] == 'valid')
impossible = sum(1 for e in entries if e['status'] == 'impossible')
print(f'[{LEVEL}] chunk {CHUNK_IDX} done: {valid} valid, {impossible} impossible of {len(chunk_seeds)}')

with lzma.open(OUTFILE, 'wb') as f:
    f.write(json.dumps({'schema_hash': '', 'oracle_commit': '', 'entries': entries}).encode())
print(f'Written: {OUTFILE}')
"

echo "[robust_regen] ${LEVEL_NAME} chunk=${CHUNK_IDX}/${N_CHUNKS} done at $(date)"

