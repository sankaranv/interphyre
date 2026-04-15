#!/bin/bash
#SBATCH --job-name=cat_v6_chunk
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=24G
#SBATCH --time=06:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cat_v6_chunk_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cat_v6_chunk_%j.err

# catapult v6 bundle regen — expanded oracle (Zones A+B+C+D).
# Zone C: near-arm placement for bridge/roll mechanism.
# Zone D: small-radius full-board for wall-bounce + indirect trajectories.
# n_attempts=1000 (2x default) to capture harder seeds; oracle_steps=1000 required.
# Audit on 253 impossible seeds: ~26% recovery rate (65 seeds become solvable).

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate
echo "[cat_v6_chunk] Starting seeds ${SEED_START}:${SEED_STOP} at $(date)"

OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/catapult_v6_chunks
mkdir -p $OUTDIR
OUTFILE=$OUTDIR/cat_v6_${SEED_START}_${SEED_STOP}_${SLURM_JOB_ID}.json.lzma

python -u -m interphyre.validation._bundle \
    --levels catapult \
    --seeds ${SEED_START}:${SEED_STOP} \
    --workers 16 \
    --attempts 1000 \
    --oracle-steps 1000 \
    --output $OUTFILE

echo "[cat_v6_chunk] Done seeds ${SEED_START}:${SEED_STOP} at $(date)"
echo "Output: $OUTFILE"
