#!/bin/bash
#SBATCH --job-name=pinball_chunk
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/pinball_v2_chunk_%a_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/pinball_v2_chunk_%a_%j.err

# Pinball machine v2 bundle regen -- Gaussian x oracle (17% avg_var improvement confirmed).
# register_defaults: max_variants=25, n_attempts=200.
# Run as array job or call with SEED_START and SEED_STOP env vars.

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate
echo "[pinball_chunk] Starting seeds ${SEED_START}:${SEED_STOP} at $(date)"

OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs
OUTFILE=$OUTDIR/pinball_v2_${SEED_START}_${SEED_STOP}_${SLURM_JOB_ID}.json.lzma

python -u -m interphyre.validation._bundle \
    --levels pinball_machine \
    --seeds ${SEED_START}:${SEED_STOP} \
    --workers 16 \
    --output $OUTFILE

echo "[pinball_chunk] Done seeds ${SEED_START}:${SEED_STOP} at $(date)"
echo "Output: $OUTFILE"
