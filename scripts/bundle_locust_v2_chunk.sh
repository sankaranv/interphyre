#!/bin/bash
#SBATCH --job-name=locust_chunk
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/locust_v2_chunk_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/locust_v2_chunk_%j.err

# locust_swarm v2 bundle regen — chain-1 anchored to green_ball.x (trivial rate 48.2%→19.3%).
# register_defaults: max_variants=50, n_attempts=500.
# 500-seed validation: avg_var=1.060 (54.5% improvement from baseline 2.332).

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate
echo "[locust_chunk] Starting seeds ${SEED_START}:${SEED_STOP} at $(date)"

OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs
OUTFILE=$OUTDIR/locust_v2_${SEED_START}_${SEED_STOP}_${SLURM_JOB_ID}.json.lzma

python -u -m interphyre.validation._bundle \
    --levels locust_swarm \
    --seeds ${SEED_START}:${SEED_STOP} \
    --workers 16 \
    --output $OUTFILE

echo "[locust_chunk] Done seeds ${SEED_START}:${SEED_STOP} at $(date)"
echo "Output: $OUTFILE"
