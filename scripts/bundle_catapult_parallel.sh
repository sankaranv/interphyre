#!/bin/bash
# Submit 4 parallel catapult chunk jobs then a merge job dependent on all of them.
# Seeds 0-10000 split into 4 chunks of 2500-2501 seeds each.
# Each chunk writes to a separate temp file; merge job combines them.

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
TMPDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/catapult_chunks
mkdir -p "$TMPDIR"

submit_chunk() {
    local chunk=$1 start=$2 stop=$3
    sbatch --parsable \
        --job-name="catapult_chunk_${chunk}" \
        --partition=cpu-preempt \
        --account=pi_jensen_umass_edu \
        --cpus-per-task=16 \
        --mem=16G \
        --time=02:00:00 \
        --output="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/catapult_chunk_${chunk}_%j.out" \
        --error="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/catapult_chunk_${chunk}_%j.err" \
        --wrap="
            . $PROJECT/.venv/bin/activate
            python -u -m interphyre.validation._bundle \
                --levels catapult \
                --seeds ${start}:${stop} \
                --workers 16 \
                --attempts 200 \
                --oracle-steps 500 \
                --output $TMPDIR/catapult_chunk_${chunk}.json.lzma
            echo 'Chunk ${chunk} done: ${start}:${stop}'
        "
}

JOB0=$(submit_chunk 0 0    2501)
JOB1=$(submit_chunk 1 2501 5001)
JOB2=$(submit_chunk 2 5001 7501)
JOB3=$(submit_chunk 3 7501 10001)

echo "Chunk jobs: $JOB0 $JOB1 $JOB2 $JOB3"

# Merge job runs only after all 4 chunks succeed.
MERGE_JOB=$(sbatch --parsable \
    --job-name="catapult_merge" \
    --partition=cpu-preempt \
    --account=pi_jensen_umass_edu \
    --cpus-per-task=2 \
    --mem=8G \
    --time=00:15:00 \
    --dependency=afterok:${JOB0}:${JOB1}:${JOB2}:${JOB3} \
    --output="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/catapult_merge_%j.out" \
    --error="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/catapult_merge_%j.err" \
    --wrap="
        . $PROJECT/.venv/bin/activate
        python -u -c \"
import lzma, json
from pathlib import Path

chunk_dir = Path('$TMPDIR')
chunks = sorted(chunk_dir.glob('catapult_chunk_*.json.lzma'))
print(f'Merging {len(chunks)} chunks: {[c.name for c in chunks]}')

all_entries = []
schema_hash = None
oracle_commit = None
for chunk in chunks:
    with lzma.open(chunk, 'rb') as f:
        data = json.load(f)
    all_entries.extend(data['entries'])
    schema_hash = data['schema_hash']
    oracle_commit = data['oracle_commit']

all_entries.sort(key=lambda e: (e['seed'], e['variant']))
n_valid = sum(1 for e in all_entries if e['status'] == 'valid')
n_seeds = len({e['seed'] for e in all_entries})
pct = 100.0 * n_valid / n_seeds

out = Path('$PROJECT/interphyre/data/levels/catapult.json.lzma')
tmp = out.with_suffix('.lzma.tmp')
with lzma.open(tmp, 'wt', encoding='utf-8') as f:
    json.dump({'schema_hash': schema_hash, 'oracle_commit': oracle_commit, 'entries': all_entries}, f)
tmp.replace(out)

print(f'catapult: {n_valid} valid / {n_seeds} seeds = {pct:.1f}%')
assert n_seeds == 10001, f'Expected 10001 seeds, got {n_seeds}'
print('OK: merge complete')
\"
    ")

echo "Merge job: $MERGE_JOB (runs after all chunks)"
echo "Monitor: squeue -u \$USER"
