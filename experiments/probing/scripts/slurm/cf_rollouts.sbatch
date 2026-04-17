#!/bin/bash
# §9.2 Counterfactual rollout generation — CPU only.
# Requires inference shards to be complete and merged.
#
# Submit per (level, split, model):
#   for split in train eval; do
#     for shard in $(seq 0 7); do
#       sbatch --export=ALL,LEVEL=down_to_earth,SPLIT=$split,SHARD_IDX=$shard,SHARD_TOTAL=8 \
#         experiments/probing/scripts/slurm/cf_rollouts.sbatch
#     done
#   done
#
# Time estimate: 28,500 conditioned instances × ~6 CF rollouts × ~0.3 sec = ~14 hrs total.
# 8 shards → ~1.7 hrs/shard. Fits in 2-hr window.

#SBATCH --job-name=probing_cf
#SBATCH --partition=cpu
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=02:30:00
#SBATCH --signal=SIGUSR1@120
#SBATCH --requeue
#SBATCH --output=scratch/probing/logs/cf_rollouts_%j.out
#SBATCH --error=scratch/probing/logs/cf_rollouts_%j.err

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p scratch/probing/logs scratch/probing/cf_outcomes

cd "$PROJECT"
source .venv/bin/activate

LEVEL="${LEVEL:-down_to_earth}"
SPLIT="${SPLIT:-train}"
SHARD_IDX="${SHARD_IDX:-0}"
SHARD_TOTAL="${SHARD_TOTAL:-8}"
MODEL_ID="${MODEL_ID:-Qwen/Qwen3-8B}"

echo "=== CF Rollouts: level=$LEVEL split=$SPLIT shard=$SHARD_IDX/$SHARD_TOTAL job=$SLURM_JOB_ID ==="
echo "Start: $(date)"

export SHARD_IDX SHARD_TOTAL

python -u -m experiments.probing.scripts.run_cf_rollouts \
    --level "$LEVEL" \
    --split "$SPLIT" \
    --model-id "$MODEL_ID" \
    --shard-idx "$SHARD_IDX" \
    --shard-total "$SHARD_TOTAL" \
    --metadata-dir scratch/probing/activations \
    --scene-dicts-dir scratch/probing/scene_dicts \
    --calibration-json scratch/probing/calibration.json \
    --output-dir scratch/probing/cf_outcomes

echo "End: $(date)"

# --- Inline verification ---
python -u -c "
import sys, pathlib, json

safe_model = '${MODEL_ID}'.replace('/', '_')
out = pathlib.Path(f'scratch/probing/cf_outcomes/{safe_model}_${LEVEL}_${SPLIT}_cf_shard{int(\"${SHARD_IDX}\"):03d}.jsonl')
if not out.exists():
    print(f'FAIL: CF output not found: {out}', file=sys.stderr)
    sys.exit(1)
with open(out) as f:
    n = sum(1 for _ in f)
print(f'OK: {out} has {n} CF rows.')
"
