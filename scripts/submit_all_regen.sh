#!/bin/bash
# Submit validate_and_regen jobs for all 25 levels in parallel.
# Usage: bash scripts/submit_all_regen.sh
#
# Each job validates one level's bundle against env.step() and regenerates
# any seeds whose stored solution no longer passes. Results go to:
#   scratch/bundle_regen/<level_name>_report.json
#   scratch/bundle_regen/logs/<level>_<jobid>.{out,err}

set -euo pipefail

PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
mkdir -p "$PROJECT/scratch/bundle_regen/logs"

LEVELS=(
    basket_case
    catapult
    cliffhanger
    dive_bomb
    down_to_earth
    end_of_line
    falling_into_place
    flagpole_sitta
    just_a_nudge
    keyhole
    locust_swarm
    marble_race
    mind_the_gap
    off_the_rails
    pass_the_parcel
    pinball_machine
    seesaw
    staircase
    straight_face
    the_cradle
    the_funnel
    tipping_point
    two_body_problem
    wedge_issue
    zebra_crossing
)

JOB_IDS=()
for LEVEL in "${LEVELS[@]}"; do
    JOB_ID=$(sbatch \
        --job-name="regen_${LEVEL}" \
        --export=ALL,LEVEL="$LEVEL" \
        "$PROJECT/scripts/run_validate_and_regen.sh" \
        | awk '{print $NF}')
    JOB_IDS+=("$JOB_ID")
    echo "Submitted $LEVEL → job $JOB_ID"
done

echo ""
echo "All 25 jobs submitted. Monitor with:"
echo "  squeue -u \$USER --format='%.10i %.20j %.8T %.10M %.10l'"
echo ""
echo "Job IDs: ${JOB_IDS[*]}"
echo ""
echo "After all jobs complete, collect results with:"
echo "  python scripts/collect_regen_report.py"
