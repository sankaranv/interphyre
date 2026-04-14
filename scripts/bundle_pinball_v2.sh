#!/bin/bash
#SBATCH --job-name=bundle_pinball_machine_v2
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_pinball_machine_v2_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_pinball_machine_v2_%j.err

# Bundle regen for pinball_machine v3: level change applied (star count 3-7 → 3-5).
# Prior regen (55545952): 8713/10001 = 87.1% at n=200. 1288 impossible — dense obstacle rows.
# Fix: num_stars capped at rng.integers(3,6). Expected ≥95%.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_pinball_machine_v2] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels pinball_machine \
    --seeds 0:10001 \
    --workers 16 \
    --attempts 200

echo "[bundle_pinball_machine_v2] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/pinball_machine.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'pinball_machine: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if pct < 95:
    print(f'WARN: below expected 95% threshold')
    sys.exit(1)
print('OK')
"
