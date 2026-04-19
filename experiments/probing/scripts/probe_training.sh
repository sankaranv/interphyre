#!/bin/bash
#SBATCH --job-name=probe_training
#SBATCH --partition=cpu
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=scratch/probing/logs/probe_training_%j.out
#SBATCH --error=scratch/probing/logs/probe_training_%j.err

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p scratch/probing/logs

source $PROJECT/.venv/bin/activate
cd $PROJECT

echo "=== Probe Training: job=$SLURM_JOB_ID ==="
echo "Start: $(date)"

python -u -m experiments.probing.scripts.run_probe_training \
    --model-id Qwen/Qwen3-8B \
    --activations-dir scratch/probing/activations \
    --cf-outcomes-dir scratch/probing/cf_outcomes \
    --h4-labels-dir scratch/probing/h4_labels \
    --output-dir results/probing

echo "End: $(date)"

# --- Inline verification ---
python -u -c "
import sys
from pathlib import Path

output_dir = Path('results/probing')
h1_path = output_dir / 'H1_descriptive_results.parquet'
if not h1_path.exists():
    print(f'FAIL: H1 results not found at {h1_path}', file=sys.stderr)
    sys.exit(1)

import pandas as pd
df = pd.read_parquet(h1_path)
print(f'OK: {h1_path} exists, {len(df)} rows')
print(df[['level','skipped','balanced_accuracy']].to_string() if 'balanced_accuracy' in df.columns else df.to_string())
"
