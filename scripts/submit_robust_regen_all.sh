#!/bin/bash
# Submit robust regen jobs for all levels that have fragile/impossible seeds.
# Reads regen seed counts from replay_validity_1000 summaries, evicts fragile seeds
# from production bundles, submits parallel chunk jobs, then a merge job per level.
#
# Usage: bash scripts/submit_robust_regen_all.sh
# Produces chunks in /scratch4/.../robust_regen/<level>/

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
REPLAY_DIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/replay_validity_1000
REGEN_BASE=/scratch4/workspace/svaidyanatha_umass_edu-phyre/robust_regen
LOG_DIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

source $PROJECT/.venv/bin/activate
cd $PROJECT

mkdir -p $LOG_DIR

# ---------------------------------------------------------------------------
# Levels to regen and their chunk counts (based on seed count)
# Large (>1000 seeds): 8 chunks; medium (>100): 4 chunks; small (<=100): 1 chunk
# ---------------------------------------------------------------------------
declare -A CHUNKS
CHUNKS[locust_swarm]=8
CHUNKS[marble_race]=8
CHUNKS[off_the_rails]=8
CHUNKS[pass_the_parcel]=4
CHUNKS[dive_bomb]=4
CHUNKS[staircase]=4
CHUNKS[the_funnel]=1
CHUNKS[straight_face]=1
CHUNKS[just_a_nudge]=1
CHUNKS[seesaw]=1
CHUNKS[pinball_machine]=1
CHUNKS[wedge_issue]=1
CHUNKS[zebra_crossing]=1
CHUNKS[keyhole]=1
CHUNKS[the_cradle]=1
CHUNKS[falling_into_place]=1
# Catapult: 3321 variant>0 entries are on wrong geometry (variant bug); all need regen.
# Uses a dedicated seeds file instead of the replay_validity_1000 output.
CHUNKS[catapult]=8

# Per-level seed file overrides (for levels whose seeds come from a different source)
declare -A SEEDS_OVERRIDE
SEEDS_OVERRIDE[catapult]=/scratch4/workspace/svaidyanatha_umass_edu-phyre/catapult_regen_seeds.txt

# ---------------------------------------------------------------------------
# Step 1: Evict fragile seeds from all production bundles (local, fast)
# ---------------------------------------------------------------------------
echo "=== Evicting fragile seeds from production bundles ==="
for LEVEL in "${!CHUNKS[@]}"; do
    if [ -n "${SEEDS_OVERRIDE[$LEVEL]+_}" ]; then
        SEEDS_FILE=${SEEDS_OVERRIDE[$LEVEL]}
    else
        SEEDS_FILE=$REPLAY_DIR/${LEVEL}_regen_seeds.txt
    fi
    if [ ! -f "$SEEDS_FILE" ]; then
        echo "  SKIP $LEVEL: no regen seeds file"
        continue
    fi
    N=$(wc -l < "$SEEDS_FILE")
    if [ "$N" -eq 0 ]; then
        echo "  SKIP $LEVEL: 0 seeds to regen"
        continue
    fi
    echo "  Evicting $N seeds from $LEVEL..."
    python scripts/evict_regen_seeds.py --level $LEVEL --seeds $SEEDS_FILE
done

# ---------------------------------------------------------------------------
# Step 2: Submit chunk regen jobs + merge jobs per level
# ---------------------------------------------------------------------------
echo ""
echo "=== Submitting regen chunk jobs ==="

for LEVEL in "${!CHUNKS[@]}"; do
    if [ -n "${SEEDS_OVERRIDE[$LEVEL]+_}" ]; then
        SEEDS_FILE=${SEEDS_OVERRIDE[$LEVEL]}
    else
        SEEDS_FILE=$REPLAY_DIR/${LEVEL}_regen_seeds.txt
    fi
    if [ ! -f "$SEEDS_FILE" ]; then continue; fi
    N=$(wc -l < "$SEEDS_FILE")
    if [ "$N" -eq 0 ]; then continue; fi

    N_CHUNKS=${CHUNKS[$LEVEL]}
    OUTDIR=$REGEN_BASE/$LEVEL
    mkdir -p $OUTDIR

    echo ""
    echo "--- $LEVEL: $N seeds, $N_CHUNKS chunks ---"

    # Submit chunk jobs
    CHUNK_JIDS=()
    for (( IDX=0; IDX<N_CHUNKS; IDX++ )); do
        JID=$(sbatch \
            --job-name=rr_${LEVEL}_c${IDX} \
            --parsable \
            --export=ALL,LEVEL_NAME=$LEVEL,SEEDS_FILE=$SEEDS_FILE,CHUNK_IDX=$IDX,N_CHUNKS=$N_CHUNKS \
            $PROJECT/scripts/robust_regen_chunk.sh)
        CHUNK_JIDS+=($JID)
        echo "  chunk $IDX/$N_CHUNKS: job $JID"
    done

    # Build dependency string for the merge job
    DEP_STR=$(IFS=:; echo "afterok:${CHUNK_JIDS[*]}")

    # Submit merge job
    MERGE_JID=$(sbatch \
        --job-name=rr_merge_${LEVEL} \
        --parsable \
        --dependency=${DEP_STR} \
        --partition=cpu-preempt \
        --account=pi_jensen_umass_edu \
        --cpus-per-task=4 \
        --mem=8G \
        --time=00:30:00 \
        --output=$LOG_DIR/rr_merge_${LEVEL}_%j.out \
        --error=$LOG_DIR/rr_merge_${LEVEL}_%j.err \
        --wrap="
set -euo pipefail
source $PROJECT/.venv/bin/activate
cd $PROJECT
CHUNKS=\$(ls $OUTDIR/${LEVEL}_chunk*.json.lzma | sort)
echo 'Merging chunks for $LEVEL: '\$CHUNKS
python scripts/merge_chunks.py --level $LEVEL --chunks \$CHUNKS
echo '$LEVEL merge done'
")
    echo "  merge job: $MERGE_JID (depends on ${CHUNK_JIDS[*]})"
done

echo ""
echo "=== All jobs submitted. Monitor with: squeue -u \$USER ==="
