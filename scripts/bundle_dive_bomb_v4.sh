#!/bin/bash
#SBATCH --job-name=bundle_dive_bomb_v4
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_dive_bomb_v4_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_dive_bomb_v4_%j.err

# Bundle regen for dive_bomb v4: Zone A y_max extended to board ceiling.
# Prior regen (v3): 10000/10001 = 100.0% (1 impossible: seed 1223).
# Root cause (oracle audit 2026-04-14): seed 1223 solution at y=4.25, but
# Zone A y_max = green_ball.y + 3.5 = -0.454 + 3.5 = 3.046 — missed by 1.2 units.
# Fix: y_max_a = 4.5 always (board ceiling); high drops needed for low-cannon seeds.
# Expected: 100% valid.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_dive_bomb_v4] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels dive_bomb \
    --seeds 0:10001 \
    --workers 16

echo "[bundle_dive_bomb_v4] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/dive_bomb.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'dive_bomb: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
impossible = [e for e in entries if e['status'] == 'impossible']
if impossible:
    print(f'  Impossible seeds: {[e[\"seed\"] for e in impossible]}')
if pct < 99.99:
    print(f'WARN: below expected 99.99% threshold')
    sys.exit(1)
print('OK')
"
