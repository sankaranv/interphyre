#!/bin/bash
#SBATCH --job-name=bundle_topup
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_topup_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_topup_%j.err

# Extend 9 near-complete bundles to 10 000 valid seeds each.
# Levels: off_the_rails, straight_face, falling_into_place, pass_the_parcel,
#         dive_bomb, mind_the_gap, keyhole, the_funnel, staircase
# All have >= 97% valid rates; only a few hundred extra seeds needed each.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

module load conda/latest

export PYTHONPATH=$PROJECT

LEVELS="off_the_rails straight_face falling_into_place pass_the_parcel dive_bomb mind_the_gap keyhole the_funnel staircase"

echo "[bundle_topup] Starting at $(date)"
echo "[bundle_topup] Levels: $LEVELS"

conda run -n interpbench python -m interphyre.validation._bundle \
    --levels $LEVELS \
    --extend \
    --target-valid 10000 \
    --workers 16 \
    --attempts 50 \
    --oracle-steps 500

echo "[bundle_topup] Done at $(date)"

# Verify each level reached target
conda run -n interpbench python -c "
import lzma, json, sys
sys.path.insert(0, '$PROJECT')
levels = '$LEVELS'.split()
all_ok = True
for lv in levels:
    path = '$PROJECT/interphyre/data/scenes/' + lv + '.json.lzma'
    with lzma.open(path, 'rb') as f:
        data = json.load(f)
    entries = data['entries']
    n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
    ok = n_valid >= 10000
    print(f'{lv}: {n_valid} valid — {\"OK\" if ok else \"FAIL\"}')
    if not ok:
        all_ok = False
if not all_ok:
    sys.exit(1)
"
