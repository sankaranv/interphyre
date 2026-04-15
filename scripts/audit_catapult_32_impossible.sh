#!/bin/bash
#SBATCH --job-name=cat32_audit
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cat32_audit_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cat32_audit_%j.err

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate
cd $PROJECT
echo "[cat32_audit] Starting at $(date)"

python -u -c "
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from interphyre.config import SimulationConfig
from interphyre.validation.oracles import get_solver
from interphyre.levels import load_level

config = SimulationConfig()

# The 32 catapult impossible seeds from v6 bundle
IMPOSSIBLE_SEEDS = [183, 634, 838, 1053, 1122, 1382, 1492, 1613, 1702, 2817, 3165, 4073, 5120, 5240, 5300, 5312, 5319, 5497, 6414, 6506, 6588, 6610, 6761, 6883, 6980, 7004, 7230, 7467, 7580, 7670, 8444, 8915]

def try_seed(seed, n_attempts=5000, oracle_steps=1000):
    level = load_level('catapult', seed=seed)
    solver = get_solver('catapult')
    rng = np.random.default_rng(seed * 999983 + 42)
    sol = solver(level, config, n_attempts=n_attempts, oracle_steps=oracle_steps, rng=rng)
    return seed, sol

print(f'Auditing {len(IMPOSSIBLE_SEEDS)} impossible catapult seeds with n_attempts=5000, oracle_steps=1000...')
found = []
impossible = []

with ProcessPoolExecutor(max_workers=8) as pool:
    futures = {pool.submit(try_seed, s): s for s in IMPOSSIBLE_SEEDS}
    for fut in as_completed(futures):
        seed, sol = fut.result()
        if sol:
            print(f'  FOUND: seed {seed} at {sol}', flush=True)
            found.append(seed)
        else:
            print(f'  IMPOSSIBLE: seed {seed}', flush=True)
            impossible.append(seed)

print(f'\\n=== SUMMARY ===')
print(f'Found: {len(found)}/{len(IMPOSSIBLE_SEEDS)} ({100*len(found)/len(IMPOSSIBLE_SEEDS):.1f}%)')
print(f'Impossible: {sorted(impossible)}')
"

echo "[cat32_audit] Done at $(date)"
