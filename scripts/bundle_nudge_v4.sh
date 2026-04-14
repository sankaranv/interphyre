#!/bin/bash
#SBATCH --job-name=bundle_nudge_v4
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_nudge_v4_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_nudge_v4_%j.err

# Bundle regen for just_a_nudge after level redesign. Level changes: platform_x [0.6,1.0], platform_angle [1,9], green_ball_radius [0.2,0.35], basket tracks green_ball. Oracle adds Zone C (40% of attempts, right-edge cluster). Expected ~57.5% (genuine geometric impossibility for remaining 42.5%).

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_nudge_v4] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels just_a_nudge \
    --seeds 0:10001 \
    --workers 16 \
    --attempts 50

echo "[bundle_nudge_v4] Done at $(date)"

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
if pct < 50:
    print(f'WARN: below expected 50% threshold')
    sys.exit(1)
print('OK')
"
