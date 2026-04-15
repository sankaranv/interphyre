#!/bin/bash
#SBATCH --job-name=sf_v3_chunk
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/sf_v3_chunk_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/sf_v3_chunk_%j.err

# straight_face v3 bundle regen — corridor oracle (70% corridor, 30% fallback).
# 500-seed validation: avg_var=1.118 (17.9% improvement from baseline 1.362).
# register_defaults: max_variants=20, n_attempts=100.

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate
echo "[sf_v3_chunk] Starting seeds ${SEED_START}:${SEED_STOP} at $(date)"

OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/sf_v3_chunks
mkdir -p $OUTDIR
OUTFILE=$OUTDIR/sf_v3_${SEED_START}_${SEED_STOP}_${SLURM_JOB_ID}.json.lzma

python -u -m interphyre.validation._bundle \
    --levels straight_face \
    --seeds ${SEED_START}:${SEED_STOP} \
    --workers 16 \
    --attempts 100 \
    --output $OUTFILE

echo "[sf_v3_chunk] Done seeds ${SEED_START}:${SEED_STOP} at $(date)"
echo "Output: $OUTFILE"
