#!/bin/bash
#SBATCH --job-name=bundle_locust_v4
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_locust_v4_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_locust_v4_%j.err

# Bundle regen for locust_swarm v4: star chain max_points reduced 30→20.
# Prior regen (v3): 9681/10001 = 96.8% (320 impossible seeds).
# Root cause (audit 2026-04-14):
#   - Stars are dynamic=False (cannot be pushed by red ball)
#   - Causal chain: red ball deflects green_ball through EXISTING GAPS in star chains
#   - Grid search confirmed 0/8 sampled impossible seeds have solutions in v=0-4
#   - Stars use min_step=0.5, max_step=1.55 (passability threshold is 1.5)
#   - Most steps (0.5-1.5) create impassable gaps — chains form complete barriers
#   - Level docstring acknowledges inherent impossibility; this reduces it
# Fix: max_points rng.integers(15,30)→rng.integers(10,20) — 37% fewer stars on avg,
#   creating sparser chains with more natural gaps for green_ball navigation.
#   RNG sequence changes (fewer loop iterations) → full regen required.
# Expected: ~99%+ valid (significant reduction from 3.2% impossible).

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_locust_v4] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels locust_swarm \
    --seeds 0:10001 \
    --workers 16

echo "[bundle_locust_v4] Done at $(date)"

python -u -c "
import lzma, json, sys
path = '$PROJECT/interphyre/data/levels/locust_swarm.json.lzma'
with lzma.open(path, 'rb') as f:
    data = json.load(f)
entries = data['entries']
n_valid = len(set(e['seed'] for e in entries if e['status'] == 'valid'))
n_seeds = len(set(e['seed'] for e in entries))
pct = 100.0 * n_valid / n_seeds
impossible = [e for e in entries if e['status'] == 'impossible']
print(f'locust_swarm: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
if impossible:
    print(f'  Impossible count: {len(impossible)}, first few: {[e[\"seed\"] for e in impossible[:5]]}')
if pct < 98.5:
    print(f'WARN: below expected 98.5% threshold')
    sys.exit(1)
print('OK')
"
