#!/bin/bash
#SBATCH --job-name=bundle_dive_bomb_v5
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_dive_bomb_v5_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_dive_bomb_v5_%j.err

# Bundle regen for dive_bomb v5: n_attempts 200→500.
# Prior regen (v4): 10000/10001 = 99.99% (1 impossible: seed 1223).
# Root cause (audit 2026-04-14): seed 1223 has 3 solvable non-trivial variants (v=3,9,14)
# each with ~70% per-trial success at n=200. P(all 3 fail with exact oracle rng) ≈ 2.7%.
# Fix: n_attempts 200→500 raises per-trial success to ~95%, P(all 3 fail) → 0.015%.
# Expected: 100.0% valid.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_dive_bomb_v5] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels dive_bomb \
    --seeds 0:10001 \
    --workers 16

echo "[bundle_dive_bomb_v5] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/dive_bomb.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
impossible = [e for e in entries if e['status'] == 'impossible']
print(f'dive_bomb: {n_valid} valid / {n_seeds} seeds = {pct:.2f}%')
if impossible:
    print(f'  Impossible seeds: {[e[\"seed\"] for e in impossible]}')
if n_valid < n_seeds:
    print(f'WARN: {n_seeds - n_valid} impossible seeds remain')
    sys.exit(1)
print('OK')
"
