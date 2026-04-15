#!/bin/bash
#SBATCH --job-name=cradle_chunk
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cradle_v2_chunk_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cradle_v2_chunk_%j.err

# the_cradle v2 bundle regen -- Gaussian y oracle (27.3% avg_var improvement confirmed).
# register_defaults: max_variants=20, n_attempts=200.

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate
echo "[cradle_chunk] Starting seeds ${SEED_START}:${SEED_STOP} at $(date)"

OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs
OUTFILE=$OUTDIR/cradle_v2_${SEED_START}_${SEED_STOP}_${SLURM_JOB_ID}.json.lzma

python -u -m interphyre.validation._bundle \
    --levels the_cradle \
    --seeds ${SEED_START}:${SEED_STOP} \
    --workers 16 \
    --output $OUTFILE

echo "[cradle_chunk] Done seeds ${SEED_START}:${SEED_STOP} at $(date)"
echo "Output: $OUTFILE"
