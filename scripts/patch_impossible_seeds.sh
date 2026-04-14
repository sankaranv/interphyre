#!/bin/bash
#SBATCH --job-name=patch_impossible
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/patch_impossible_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/patch_impossible_%j.err

# Targeted patch for 6 remaining impossible seeds across 3 levels.
# Analysis (2026-04-14):
#   pass_the_parcel seed=4846: solvable at v=0 with 500 full-board attempts → oracle FNR
#   the_funnel seed=3324: trivial at v=0, no non-trivial solution found → inherent
#   keyhole seed=4873: found at v=5 with 300 attempts → oracle FNR (max_variants too low)
#   keyhole seed=7322: found at v=1 with 300 attempts → oracle FNR
#   keyhole seed=7445: not found in v=0-9 → possibly genuine
#   keyhole seed=8360: found at v=6 with 300 attempts → oracle FNR
# Fix: --merge re-runs each impossible seed with higher n_attempts and max_variants.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate

echo "[patch_impossible] Starting at $(date)"

# pass_the_parcel seed 4846: oracle FNR — retry with 500 attempts × 30 variants
echo "Patching pass_the_parcel seed 4846..."
python -u -m interphyre.validation._bundle \
    --levels pass_the_parcel \
    --seeds 4846:4847 \
    --merge \
    --workers 1 \
    --attempts 500 \
    --max-variants 30

# the_funnel seed 3324: trivial at v=0 — retry more variants to find non-trivial
echo "Patching the_funnel seed 3324..."
python -u -m interphyre.validation._bundle \
    --levels the_funnel \
    --seeds 3324:3325 \
    --merge \
    --workers 1 \
    --attempts 500 \
    --max-variants 50

# keyhole seeds 4873, 7322, 7445, 8360 — retry with 30 variants
echo "Patching keyhole seeds 4873, 7322, 7445, 8360..."
for seed_start in 4873 7322 7445 8360; do
    seed_stop=$((seed_start + 1))
    echo "  keyhole seed $seed_start..."
    python -u -m interphyre.validation._bundle \
        --levels keyhole \
        --seeds ${seed_start}:${seed_stop} \
        --merge \
        --workers 1 \
        --attempts 500 \
        --max-variants 50
done

echo "[patch_impossible] Done at $(date)"

# Verify
python -u -c "
import lzma, json, sys
results = {}
for level in ['pass_the_parcel', 'the_funnel', 'keyhole']:
    path = '$PROJECT/interphyre/data/levels/' + level + '.json.lzma'
    with lzma.open(path, 'rb') as f:
        data = json.load(f)
    entries = data['entries']
    n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
    n_seeds = len(set(e['seed'] for e in entries))
    pct = 100.0 * n_valid / n_seeds
    impossible = [e['seed'] for e in entries if e['status'] == 'impossible']
    print(f'{level}: {n_valid}/{n_seeds} = {pct:.3f}% (impossible: {impossible})')
    results[level] = pct

if results.get('keyhole', 0) < 99.95:
    print('WARN: keyhole still has impossible seeds')
    sys.exit(1)
print('OK')
"
