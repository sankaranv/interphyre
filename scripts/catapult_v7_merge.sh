#!/bin/bash
#SBATCH --job-name=cat_v7_merge
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cat_v7_merge_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/cat_v7_merge_%j.err

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
source $PROJECT/.venv/bin/activate
cd $PROJECT
echo "[cat_v7_merge] Starting at $(date)"

OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/catapult_v7
CHUNKS=$(ls $OUTDIR/cat_v7_chunk_*.json.lzma 2>/dev/null | sort)
echo "Chunks to merge: $CHUNKS"

python scripts/merge_chunks.py \
    --level catapult \
    --chunks $CHUNKS

echo "[cat_v7_merge] Done at $(date)"
