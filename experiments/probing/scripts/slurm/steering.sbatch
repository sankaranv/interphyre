#!/bin/bash
# §13 Steering protocol (H6a/H6b/H6c) — GPU required.
# One job per (level, target, direction) combination.
# Requires probe training complete (DIM directions in calibration.json).
#
# Time estimate: 200 eval instances × 21 α values × (1 steered + 20 random) inferences
#   = 200 × 21 × 21 = 88,200 inferences. At 83 sec/inference → ~2,037 hrs.
#   This is too large for a single job. Reduce scope:
#   Use n_eval_instances=50, random_controls=5 → 200 × 21 × 6 = 25,200 inferences ≈ 580 hrs.
#   Split across 20 jobs (one per (level, target, direction) combo) → ~29 hrs/job.
#   Or: 10 instances × 21 α × 21 controls = 4,410 inferences ≈ 4 hrs/job with SHARD.
#
#   Pilot first: submit one job with --n-eval-instances=10, time 30 min.
#
# Submit per combination:
#   sbatch --export=ALL,LEVEL=down_to_earth,TARGET=purple_ground,DIR_KEY=+1.0,+0.0 \
#     --output=scratch/probing/logs/steering_dte_pg_px_%j.out \
#     experiments/probing/scripts/slurm/steering.sbatch

#SBATCH --job-name=probing_steer
#SBATCH --partition=gpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --gres=gpu:1
#SBATCH --constraint=vram40
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=08:00:00
#SBATCH --signal=SIGUSR1@120
#SBATCH --requeue
#SBATCH --output=scratch/probing/logs/steering_%j.out
#SBATCH --error=scratch/probing/logs/steering_%j.err

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p scratch/probing/logs results/probing

cd "$PROJECT"
source .venv/bin/activate

LEVEL="${LEVEL:-down_to_earth}"
TARGET="${TARGET:-purple_ground}"
DIR_KEY="${DIR_KEY:-+1.0,+0.0}"
MODEL_ID="${MODEL_ID:-Qwen/Qwen3-8B}"
N_EVAL="${N_EVAL:-50}"

echo "=== Steering: level=$LEVEL target=$TARGET dir=$DIR_KEY model=$MODEL_ID n_eval=$N_EVAL ==="
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "Start: $(date)"

python -u -m experiments.probing.scripts.run_steering \
    --model-id "$MODEL_ID" \
    --level "$LEVEL" \
    --target "$TARGET" \
    --direction-key "$DIR_KEY" \
    --calibration-json scratch/probing/calibration.json \
    --h3-results-dir results/probing \
    --activations-dir scratch/probing/activations \
    --cf-outcomes-dir scratch/probing/cf_outcomes \
    --scene-dicts-dir scratch/probing/scene_dicts \
    --output-dir results/probing \
    --n-eval-instances "$N_EVAL"

echo "End: $(date)"

# --- Inline verification ---
python -u -c "
import sys, pathlib, json

safe_dir = '${DIR_KEY}'.replace(',', '_').replace('+', 'p').replace('-', 'n')
out = pathlib.Path(f'results/probing/h6_${LEVEL}_${TARGET}_{safe_dir}.json')
if not out.exists():
    print(f'FAIL: H6 results not found: {out}', file=sys.stderr)
    sys.exit(1)
with open(out) as f:
    results = json.load(f)
rho = results.get('h6b_spearman_rho', 'N/A')
print(f'OK: {out} — H6b rho={rho}')
"
