#!/bin/bash
#SBATCH --job-name=bundle_straight_face_v2
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_straight_face_v2_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_straight_face_v2_%j.err

# Bundle regen for straight_face. Root cause was n_attempts=50 and y-floor bug (now fixed: full-board y). Expected ~100% with n_attempts=100.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_straight_face_v2] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels straight_face \
    --seeds 0:10001 \
    --workers 16 \
    --attempts 200

echo "[bundle_straight_face_v2] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/straight_face.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
print(f'straight_face: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if pct < 93:
    print(f'WARN: below expected 93% threshold')
    sys.exit(1)
print('OK')
"
