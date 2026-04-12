#!/bin/bash
#SBATCH --job-name=bundle_cradle
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_cradle_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_cradle_%j.err

# Extend the_cradle to 10 000 valid seeds.
# Currently: 5985 valid / 10 000 seeds (59.9%). Need ~4015 more valid.
# Estimated extra seeds needed: ~7429. Higher memory due to large bundle size.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

module load conda/latest

export PYTHONPATH=$PROJECT

echo "[bundle_cradle] Starting at $(date)"

conda run -n interpbench python -m interphyre.validation._bundle \
    --levels the_cradle \
    --extend \
    --target-valid 10000 \
    --workers 16 \
    --attempts 50 \
    --oracle-steps 500

echo "[bundle_cradle] Done at $(date)"

conda run -n interpbench python -c "
import lzma, json, sys
sys.path.insert(0, '$PROJECT')
path = '$PROJECT/interphyre/data/scenes/the_cradle.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
print(f'the_cradle: {n_valid} valid / {n_seeds} seeds')
if n_valid < 10000:
    print('FAIL: did not reach 10000 valid')
    sys.exit(1)
print('OK')
"
