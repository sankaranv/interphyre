#!/bin/bash
#SBATCH --job-name=bundle_mind_the_gap_v4
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_mind_the_gap_v4_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_mind_the_gap_v4_%j.err

# Bundle regen for mind_the_gap v4: hole_width 1.05→1.15, n_attempts 200→300.
# Prior regen (v3): 10000/10001 = 100.0% (1 impossible: seed 6719).
# Root cause (oracle audit 2026-04-14): hole_width=1.05 ≈ green_ball_diameter=1.0
#   leaves only 0.05 units of slack, making only 2/30 variants solvable for seed 6719.
# Fix A (level): hole_width 1.05→1.15 (tripling post-displacement slack, 0.05→0.15).
#   RNG sequence unchanged — hole_width is a constant, not a sampled value.
# Fix B (oracle): n_attempts 200→300 increases per-variant P(find) ~43%→~59%.
# Expected: 100% valid.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_mind_the_gap_v4] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels mind_the_gap \
    --seeds 0:10001 \
    --workers 16

echo "[bundle_mind_the_gap_v4] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/mind_the_gap.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'mind_the_gap: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
impossible = [e for e in entries if e['status'] == 'impossible']
if impossible:
    print(f'  Impossible seeds: {[e[\"seed\"] for e in impossible]}')
if pct < 99.99:
    print(f'WARN: below expected 99.99% threshold')
    sys.exit(1)
print('OK')
"
