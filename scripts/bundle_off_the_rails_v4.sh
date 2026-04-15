#!/bin/bash
#SBATCH --job-name=bundle_off_the_rails_v4
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_off_the_rails_v4_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_off_the_rails_v4_%j.err

# Bundle regen for off_the_rails v4: oracle x-range + Band B dead-zone fixes, n_attempts 100→200.
# Prior regen (v3): 9999/10001 = 99.98% (2 impossible: seeds 6702, 8169).
# Root causes (oracle audit 2026-04-14):
#   seed 6702 (gb.y=3.62): n_attempts=100 insufficient (solved at n=2000 via Band B).
#   seed 8169 variant 0: solution at x=-4.5, oracle x_min=-1.9 (cx±2 missed it).
#   seed 8169 variant 1: solution at y=gb.y-0.15, in dead zone [gb.y-0.2, gb.y+0.2].
# Fix A: x_min = min(cx-2, gb.x-2) — extends left bound for near-left-wall seeds.
# Fix B: y_max_b extended from gb.y-0.2 to gb.y+0.3 — closes the near-ball dead zone.
# Fix C: n_attempts 100→200.
# Expected: 100% valid.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_off_the_rails_v4] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels off_the_rails \
    --seeds 0:10001 \
    --workers 16

echo "[bundle_off_the_rails_v4] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/off_the_rails.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'off_the_rails: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
impossible = [e for e in entries if e['status'] == 'impossible']
if impossible:
    print(f'  Impossible seeds: {[e[\"seed\"] for e in impossible]}')
if pct < 99.99:
    print(f'WARN: below expected 99.99% threshold')
    sys.exit(1)
print('OK')
"
