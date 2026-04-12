#!/bin/bash
#SBATCH --job-name=bundle_locust
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_locust_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_locust_%j.err

# Extend locust_swarm to 10 000 valid seeds.
# Currently: 7458 valid / 10 000 seeds (74.6%). Need ~2542 more valid.
# Estimated extra seeds needed: ~3799.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_locust] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels locust_swarm \
    --extend \
    --target-valid 10000 \
    --workers 16 \
    --attempts 50 \
    --oracle-steps 500

echo "[bundle_locust] Done at $(date)"

python -u -c "
import lzma, json, sys
sys.path.insert(0, '$PROJECT')
path = '$PROJECT/interphyre/data/levels/locust_swarm.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
print(f'locust_swarm: {n_valid} valid / {n_seeds} seeds')
if n_valid < 10000:
    print('FAIL: did not reach 10000 valid')
    sys.exit(1)
print('OK')
"
