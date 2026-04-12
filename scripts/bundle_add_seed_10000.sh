#!/bin/bash
#SBATCH --job-name=bundle_seed_10000
#SBATCH --partition=cpu-preempt
#SBATCH --account=pi_jensen_umass_edu
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_seed_10000_%j.out
#SBATCH --error=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/bundle_seed_10000_%j.err

# Add seed 10000 to all 25 level bundles.
#
# The canonical seed universe is seeds 0–10000 inclusive (10001 seeds).
# All bundles were previously truncated to max_seed=9999 by a posthoc prune;
# this job restores seed 10000 for every level using --extend.
#
# Catapult is excluded here — its bundle is being regenerated separately by
# bundle_catapult_v2.sh which covers seeds 0:10001.

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate

echo "[bundle_seed_10000] Starting at $(date)"

python -u -m interphyre.validation._bundle \
    --levels \
        basket_case \
        cliffhanger \
        dive_bomb \
        down_to_earth \
        end_of_line \
        falling_into_place \
        flagpole_sitta \
        just_a_nudge \
        keyhole \
        locust_swarm \
        marble_race \
        mind_the_gap \
        off_the_rails \
        pass_the_parcel \
        pinball_machine \
        seesaw \
        staircase \
        straight_face \
        the_cradle \
        the_funnel \
        tipping_point \
        two_body_problem \
        wedge_issue \
        zebra_crossing \
    --seeds 10000:10001 \
    --workers 16 \
    --attempts 50 \
    --oracle-steps 500

echo "[bundle_seed_10000] Done at $(date)"

python -u -c "
import lzma, json
from pathlib import Path

bundle_dir = Path('$PROJECT/interphyre/data/levels')
bad = []
for p in sorted(bundle_dir.glob('*.json.lzma')):
    with lzma.open(p, 'rb') as f:
        data = json.load(f)
    seeds = {e['seed'] for e in data['entries']}
    max_seed = max(seeds)
    if max_seed < 10000:
        bad.append(p.stem)
    else:
        print(f'{p.stem}: OK (max_seed={max_seed})')
if bad:
    print(f'MISSING seed 10000: {bad}')
    raise SystemExit(1)
print('All bundles confirmed to include seed 10000.')
"
