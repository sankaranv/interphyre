#!/bin/bash
#SBATCH --job-name=bundle_validation
#SBATCH --partition=cpu
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=scratch/bundle_validation/logs/bundle_validation_%j.out
#SBATCH --error=scratch/bundle_validation/logs/bundle_validation_%j.err

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
cd $PROJECT

source $PROJECT/.venv/bin/activate

echo "=== Bundle validation: all 25 levels, seeds 0-10000 ==="
echo "Node: $(hostname)"
echo "Start: $(date)"

uv run pytest -m bundle_validation --tb=short -v

echo "End: $(date)"
echo "=== Done ==="
