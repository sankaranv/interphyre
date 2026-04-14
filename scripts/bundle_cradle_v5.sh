#!/bin/bash
#SBATCH --job-name=bundle_cradle_v5
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_cradle_v5_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_cradle_v5_%j.err

# Bundle regen for the_cradle after level parameter changes.
# Level changes (fix/solvability commit 3eccf1a):
#   - red_ball_radius: [0.3, 0.6] -> [0.45, 0.6]
#   - holder_length: [0.5, 1.0] -> [0.5, 0.75]
#
# Diagnostic (2026-04-14): 40% of seeds solvable at variant=0 with n_attempts=200.
# With max_variants=10 (default), expected valid rate ~96%+ as independent variants
# greatly reduce per-seed failure rate: (1-0.40)^10 ≈ 0.6% failure.
#
# Prior run (bundle_cradle_v4.sh) used --attempts 50 which was insufficient for
# the oracle_rng: 0 valid / 10001 seeds. This script uses --attempts 200.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_cradle_v5] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels the_cradle \
    --seeds 0:10001 \
    --workers 16 \
    --attempts 200 \
    --max-variants 10

echo "[bundle_cradle_v5] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/the_cradle.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'the_cradle: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if pct < 80:
    print(f'WARN: below expected 80% threshold')
    sys.exit(1)
print('OK')
"
