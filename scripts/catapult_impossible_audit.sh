#!/bin/bash
#SBATCH --job-name=catapult_audit
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/catapult_audit_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/catapult_audit_%j.err

set -e
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
cd "$PROJECT"
source .venv/bin/activate

python -u scripts/catapult_impossible_audit.py
