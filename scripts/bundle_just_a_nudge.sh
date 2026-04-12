#!/bin/bash
#SBATCH --job-name=bundle_nudge
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_just_a_nudge_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_just_a_nudge_%j.err

# Full regeneration of just_a_nudge bundle with fixed oracle (4e746df).
# Old bundle: 1 valid / 1000 seeds (stale oracle 97f5549).
# Fixed oracle (direct knockoff mechanism): ~10% valid rate expected.
# Seeds 0:10000 will yield ~1000 valid — establishing the true solvability rate.
# NOTE: This level is flagged for design review. Do NOT attempt to reach 10 000
# valid before redesign; 10 000-seed run (~1000 valid) documents the true rate.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_just_a_nudge] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels just_a_nudge \
    --seeds 0:10000 \
    --workers 16 \
    --attempts 50 \
    --oracle-steps 500

echo "[bundle_just_a_nudge] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/just_a_nudge.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'just_a_nudge: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
print('Flagged for design review — 10k valid requires redesign first.')
"
