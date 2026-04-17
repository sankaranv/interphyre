#!/bin/bash
# §14 Replication — Gemma 2 9B-IT inference + activation extraction.
# Same shard structure as inference_qwen3.sbatch; swaps model ID.
# Gemma 2 9B-IT has 42 layers × hidden_size=3584 ≈ matched storage to Qwen3-8B.
#
# Submit identically to inference_qwen3.sbatch but with MODEL_ID=google/gemma-2-9b-it.

#SBATCH --job-name=probing_inf_gemma2
#SBATCH --partition=gpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --gres=gpu:1
#SBATCH --constraint=vram40
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=03:00:00
#SBATCH --signal=SIGUSR1@120
#SBATCH --requeue
#SBATCH --output=scratch/probing/logs/inference_gemma2_%j.out
#SBATCH --error=scratch/probing/logs/inference_gemma2_%j.err

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p scratch/probing/logs scratch/probing/activations scratch/probing/scene_dicts

cd "$PROJECT"
source .venv/bin/activate

LEVEL="${LEVEL:-down_to_earth}"
SPLIT="${SPLIT:-train}"
SHARD_IDX="${SHARD_IDX:-0}"
SHARD_TOTAL="${SHARD_TOTAL:-120}"
MODEL_ID="${MODEL_ID:-google/gemma-2-9b-it}"

echo "=== Inference Gemma2: level=$LEVEL split=$SPLIT shard=$SHARD_IDX/$SHARD_TOTAL job=$SLURM_JOB_ID ==="
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "Start: $(date)"

# Verify model architecture at load time per §14.1.
python -u -c "
from transformers import AutoConfig
cfg = AutoConfig.from_pretrained('$MODEL_ID')
assert cfg.num_hidden_layers == 42, f'Expected 42 layers, got {cfg.num_hidden_layers}'
assert cfg.hidden_size == 3584, f'Expected hidden_size=3584, got {cfg.hidden_size}'
print(f'Architecture verified: {cfg.num_hidden_layers} layers, hidden_size={cfg.hidden_size}')
"

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
import sys, h5py, glob
safe_model = '${MODEL_ID}'.replace('/', '_')
pattern = f'scratch/probing/activations/{safe_model}_${LEVEL}_${SPLIT}_shard{int(\"${SHARD_IDX}\"):03d}.h5'
files = glob.glob(pattern)
if not files:
    print(f'FAIL: No HDF5 file found at {pattern}', file=sys.stderr)
    sys.exit(1)
with h5py.File(files[0], 'r') as f:
    n = len(f['instance_id'])
print(f'OK: {files[0]} has {n} instances.')
"
