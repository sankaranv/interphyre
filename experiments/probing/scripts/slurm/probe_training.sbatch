#!/bin/bash
# §12 Probe training (H1/H2/H3/H3b/H4a-c/H5a/H5b) — CPU only.
# Requires merged HDF5, metadata parquet, and CF outcomes parquet.
#
# Run AFTER merging all inference + CF shards into:
#   scratch/probing/activations/{model_id}_merged.h5
#   scratch/probing/activations/{model_id}_metadata.parquet
#   scratch/probing/cf_outcomes/{model_id}_cf_outcomes.parquet
#
# Time estimate: layer sweep (36×3 cells) × 20 combos × 4 hypotheses
#   = 8,640 probe fits. At ~10 sec/fit = ~24 hrs. Needs large time limit.
#   Use --partition=cpu (no preemption) for this job.
#
# Submit:
#   sbatch --export=ALL,MODEL_ID=Qwen/Qwen3-8B \
#     experiments/probing/scripts/slurm/probe_training.sbatch

#SBATCH --job-name=probing_train
#SBATCH --partition=cpu
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --time=36:00:00
#SBATCH --output=scratch/probing/logs/probe_training_%j.out
#SBATCH --error=scratch/probing/logs/probe_training_%j.err

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p scratch/probing/logs results/probing

cd "$PROJECT"
source .venv/bin/activate

MODEL_ID="${MODEL_ID:-Qwen/Qwen3-8B}"

echo "=== Probe Training: model=$MODEL_ID job=$SLURM_JOB_ID ==="
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Start: $(date)"

python -u -m experiments.probing.scripts.run_probe_training \
    --model-id "$MODEL_ID" \
    --activations-dir scratch/probing/activations \
    --cf-outcomes-dir scratch/probing/cf_outcomes \
    --h4-labels-dir scratch/probing/h4_labels \
    --output-dir results/probing \
    --hypotheses H1 H2 H3 H3b H4 H5

echo "End: $(date)"

# --- Inline verification ---
python -u -c "
import sys, pathlib
required = ['h1_results.parquet', 'h3_results.parquet', 'h4_results.parquet']
for r in required:
    p = pathlib.Path('results/probing') / r
    if not p.exists():
        print(f'FAIL: {p} not found', file=sys.stderr)
        sys.exit(1)
print(f'OK: All required result parquets present in results/probing/')
"
