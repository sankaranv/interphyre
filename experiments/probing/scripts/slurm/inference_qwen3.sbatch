#!/bin/bash
# §10+11 LLM inference + activation extraction — Qwen3-8B.
# Array job: one shard per task. Each shard processes N_SEEDS/SHARD_TOTAL seeds.
#
# Seed estimate: 4,200 seeds/level × 3 levels = 12,600 inferences.
# At ~30 tok/sec on A100 and ~2500 tok/instance ≈ 83 sec/instance.
# 40 shards → 315 inferences/shard ≈ 7.3 hrs per shard (exceeds time limit).
# Use SHARD_TOTAL=120 → ~105 instances/shard ≈ 2.4 hrs. Fits in 3-hr window.
#
# Pilot: run SHARD_TOTAL=1 SHARD_IDX=0 on 20 seeds first, adjust accordingly.
#
# Submit all shards for one level+split:
#   for split in train eval; do
#     for shard in $(seq 0 119); do
#       sbatch --export=ALL,LEVEL=down_to_earth,SPLIT=$split,SHARD_IDX=$shard,SHARD_TOTAL=120 \
#         --output=scratch/probing/logs/inference_qwen3_dte_${split}_shard${shard}_%j.out \
#         experiments/probing/scripts/slurm/inference_qwen3.sbatch
#     done
#   done

#SBATCH --job-name=probing_inf_qwen3
#SBATCH --partition=gpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --gres=gpu:1
#SBATCH --constraint=vram80
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --signal=SIGUSR1@120
#SBATCH --requeue
#SBATCH --output=scratch/probing/logs/inference_qwen3_%j.out
#SBATCH --error=scratch/probing/logs/inference_qwen3_%j.err

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p scratch/probing/logs scratch/probing/activations scratch/probing/scene_dicts

cd "$PROJECT"
source .venv/bin/activate

LEVEL="${LEVEL:-down_to_earth}"
SPLIT="${SPLIT:-train}"
SHARD_IDX="${SHARD_IDX:-0}"
SHARD_TOTAL="${SHARD_TOTAL:-120}"
MODEL_ID="${MODEL_ID:-Qwen/Qwen3-8B}"

echo "=== Inference Qwen3: level=$LEVEL split=$SPLIT shard=$SHARD_IDX/$SHARD_TOTAL job=$SLURM_JOB_ID ==="
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "Start: $(date)"

export SHARD_IDX SHARD_TOTAL

python -u -m experiments.probing.scripts.run_inference \
    --level "$LEVEL" \
    --split "$SPLIT" \
    --model-id "$MODEL_ID" \
    --shard-idx "$SHARD_IDX" \
    --shard-total "$SHARD_TOTAL" \
    --activations-dir scratch/probing/activations \
    --metadata-dir scratch/probing/activations \
    --scene-dicts-dir scratch/probing/scene_dicts

echo "End: $(date)"

# --- Inline verification ---
python -u -c "
import sys, h5py, pathlib, glob, json, statistics

safe_model = '${MODEL_ID}'.replace('/', '_')
shard_id = f'{safe_model}_${LEVEL}_${SPLIT}_shard{int(\"${SHARD_IDX}\"):03d}'
h5_pattern = f'scratch/probing/activations/{shard_id}.h5'
meta_pattern = f'scratch/probing/activations/{shard_id}.meta.jsonl'

files = glob.glob(h5_pattern)
if not files:
    print(f'FAIL: No HDF5 file found at {h5_pattern}', file=sys.stderr)
    sys.exit(1)
with h5py.File(files[0], 'r') as f:
    n = len(f['instance_id'])
print(f'OK HDF5: {files[0]} has {n} instances.')

meta_files = glob.glob(meta_pattern)
if not meta_files:
    print(f'FAIL: No meta.jsonl found at {meta_pattern}', file=sys.stderr)
    sys.exit(1)
rows = [json.loads(l) for l in open(meta_files[0])]
n_rows = len(rows)
if n_rows == 0:
    print('FAIL: meta.jsonl is empty', file=sys.stderr)
    sys.exit(1)

n_success = sum(1 for r in rows if r.get('factual_outcome'))
n_empty_level = sum(1 for r in rows if not r.get('level_name', ''))
step_counts = sorted(r.get('factual_step_count', 0) for r in rows)
median_steps = statistics.median(step_counts)
success_rate = n_success / n_rows

issues = []
if success_rate < 0.01:
    issues.append(f'success_rate={success_rate:.1%} (<1%): possible rollout bug')
if success_rate > 0.95:
    issues.append(f'success_rate={success_rate:.1%} (>95%): possible rollout bug')
if n_empty_level > 0:
    issues.append(f'{n_empty_level}/{n_rows} rows have empty level_name')
if median_steps < 50:
    issues.append(f'median factual_step_count={median_steps:.0f} (<50): possible early-stop bug')

if issues:
    for issue in issues:
        print(f'FAIL metadata: {issue}', file=sys.stderr)
    sys.exit(1)

print(f'OK metadata: n={n_rows}, success_rate={success_rate:.1%}, median_steps={median_steps:.0f}')
"
