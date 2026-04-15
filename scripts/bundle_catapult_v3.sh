#!/bin/bash
#SBATCH --job-name=bundle_catapult_v3
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_catapult_v3_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_catapult_v3_%j.err

# Bundle regen for catapult v4: level parameter constraints + oracle n_attempts=400.
# Prior regen (bundle_catapult_v2.sh, job 55545951): 1792/10001 = 17.9% at n=200.
# Analysis (results/solvability_audit/catapult_redesign_analysis.md):
#   - red_ball_radius U(0.6,1.2) → U(0.9,1.2): 3.5% → 32.6% solvability for r<0.9 vs r>=0.9
#   - black_platform_x U(-3,-1.5) → U(-2.5,-1.5): arm_right<0.225 had only 7-9% solvability
#   - n_attempts 200 → 400: targeted FNR 21% for favorable seeds; doubling attempts halves miss rate
# Expected: ~38-45% valid (Scenario 4+5 combined estimate from analysis).

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_catapult_v3] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels catapult \
    --seeds 0:10001 \
    --workers 16 \
    --attempts 400 \
    --oracle-steps 500

echo "[bundle_catapult_v3] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/catapult.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'catapult: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if pct < 35:
    print(f'WARN: below expected 35% threshold — investigate further')
    sys.exit(1)
print('OK')
"
