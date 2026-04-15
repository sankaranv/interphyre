#!/bin/bash
#SBATCH --job-name=pinball_v2_merge2
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/pinball_v2_merge2_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/pinball_v2_merge2_%j.err

# Corrected merge job: uses scripts/merge_chunks.py to combine pre-computed chunk
# output files directly into the production bundle (no oracle re-running).
# Replaces the broken bundle_pinball_v2_merge.sh which used invalid --input flag.

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate
echo "[pinball_merge2] Starting at $(date)"

python -u $PROJECT/scripts/merge_chunks.py \
    --level pinball_machine \
    --chunks \
        $OUTDIR/pinball_v2_0_2500_55567323.json.lzma \
        $OUTDIR/pinball_v2_2500_5000_55567324.json.lzma \
        $OUTDIR/pinball_v2_5000_7500_55567325.json.lzma \
        $OUTDIR/pinball_v2_7500_10001_55567326.json.lzma

echo "[pinball_merge2] Done at $(date)"
