"""
Merge inference shards (HDF5 + metadata JSONL) into single files per (model, level, split).

Run after all inference_*.sbatch shards complete:
    python -m experiments.probing.scripts.merge_shards \
        --model-id Qwen/Qwen3-8B \
        --activations-dir scratch/probing/activations \
        --levels down_to_earth end_of_line two_body_problem

Then run the same for CF outcomes:
    python -m experiments.probing.scripts.merge_shards --merge-cf \
        --model-id Qwen/Qwen3-8B \
        --cf-outcomes-dir scratch/probing/cf_outcomes \
        --levels down_to_earth end_of_line two_body_problem
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def merge_hdf5_shards(
    shard_dir: Path,
    model_id: str,
    level: str,
    split: str,
    output_path: Path,
) -> None:
    """Merge all HDF5 shard files for one (model, level, split) into a single HDF5."""
    try:
        import h5py
    except ImportError:
        logger.error("h5py required for HDF5 merge.")
        sys.exit(1)

    safe_model = model_id.replace("/", "_")
    pattern = f"{safe_model}_{level}_{split}_shard*.h5"
    shard_files = sorted(shard_dir.glob(pattern))

    if not shard_files:
        logger.warning("No shard HDF5 files found matching: %s/%s", shard_dir, pattern)
        return

    logger.info("Merging %d HDF5 shards for %s/%s/%s", len(shard_files), model_id, level, split)

    def _try_open(path: Path) -> "h5py.File | None":
        try:
            return h5py.File(str(path), "r")
        except OSError as exc:
            logger.warning("Skipping unreadable shard %s: %s", path.name, exc)
            return None

    # Discover schema from first readable shard.
    layer_keys: list[str] = []
    has_embed = False
    shape: tuple = ()
    dtype_main = None
    for sf in shard_files:
        f0 = _try_open(sf)
        if f0 is None:
            continue
        with f0:
            layer_keys = [k for k in f0.keys() if k.startswith("layer_")]
            has_embed = "embed" in f0
            if layer_keys:
                shape = f0[layer_keys[0]].shape[1:]  # (3, hidden_size)
                dtype_main = f0[layer_keys[0]].dtype
        break

    if not layer_keys:
        logger.error("No readable shard found with layer keys — cannot merge.")
        return

    readable_shards: list[Path] = []
    skipped = 0
    for sf in shard_files:
        f = _try_open(sf)
        if f is None:
            skipped += 1
            continue
        f.close()
        readable_shards.append(sf)

    if skipped:
        logger.warning("Skipped %d/%d corrupt or locked shards.", skipped, len(shard_files))

    with h5py.File(str(output_path), "w") as out:
        # Collect all instance_ids first to pre-allocate.
        all_ids = []
        for sf in readable_shards:
            with h5py.File(str(sf), "r") as f:
                ids = [iid.decode() if isinstance(iid, bytes) else iid for iid in f["instance_id"][:]]
                all_ids.extend(ids)

        n_total = len(all_ids)
        logger.info("Total instances: %d (from %d readable shards)", n_total, len(readable_shards))

        # Create output datasets.
        for lk in layer_keys:
            out.create_dataset(
                lk, shape=(n_total, *shape), dtype=dtype_main,
                chunks=(1, *shape), compression="gzip", compression_opts=4,
            )
        if has_embed:
            out.create_dataset(
                "embed", shape=(n_total, *shape), dtype=dtype_main,
                chunks=(1, *shape), compression="gzip", compression_opts=4,
            )
        out.create_dataset("instance_id", data=np.array([iid.encode() for iid in all_ids], dtype="S64"))

        # Copy data shard by shard.
        write_idx = 0
        for sf in readable_shards:
            with h5py.File(str(sf), "r") as f:
                n_shard = len(f["instance_id"])
                for lk in layer_keys:
                    if lk in f:
                        out[lk][write_idx:write_idx + n_shard] = f[lk][:]
                if has_embed and "embed" in f and len(f["embed"]) == n_shard:
                    out["embed"][write_idx:write_idx + n_shard] = f["embed"][:]
                elif has_embed and "embed" in f:
                    logger.warning("Shard %s: embed length %d != instance count %d; skipping embed rows", sf.name, len(f["embed"]), n_shard)
                write_idx += n_shard

        # Copy stats from the first readable shard that has them.
        for sf in readable_shards:
            with h5py.File(str(sf), "r") as f:
                if "stats" in f:
                    f.copy("stats", out)
                    break

        logger.info("Merged HDF5 written: %s (%d instances)", output_path, n_total)


def merge_hdf5_files(
    source_paths: list[Path],
    output_path: Path,
) -> None:
    """Concatenate a list of per-level-per-split HDF5 files into one merged file.

    Called after all per-level-per-split merges complete to produce the single
    {model}_merged.h5 that run_probe_training.py expects.  Each source file
    must share the same layer schema (n_layers, hidden_size).
    """
    try:
        import h5py
    except ImportError:
        logger.error("h5py required for HDF5 merge.")
        return

    existing = [p for p in source_paths if p.exists()]
    if not existing:
        logger.warning("No per-level HDF5 files to merge into %s", output_path)
        return

    logger.info("Merging %d per-level HDF5 files into %s", len(existing), output_path)

    # Discover schema from first file.
    with h5py.File(str(existing[0]), "r") as f0:
        layer_keys = sorted(k for k in f0.keys() if k.startswith("layer_"))
        shape_suffix = f0[layer_keys[0]].shape[1:]  # (3, hidden_size)
        dtype_main = f0[layer_keys[0]].dtype

    # Count total instances.
    total_n = 0
    for src in existing:
        with h5py.File(str(src), "r") as f:
            total_n += len(f["instance_id"])

    with h5py.File(str(output_path), "w") as out:
        for lk in layer_keys:
            out.create_dataset(
                lk,
                shape=(total_n, *shape_suffix),
                dtype=dtype_main,
                chunks=(1, *shape_suffix),
                compression="gzip",
                compression_opts=4,
            )
        out.create_dataset("instance_id", shape=(total_n,), dtype="S64")

        write_idx = 0
        for src in existing:
            with h5py.File(str(src), "r") as f:
                n = len(f["instance_id"])
                out["instance_id"][write_idx:write_idx + n] = f["instance_id"][:]
                for lk in layer_keys:
                    if lk in f:
                        out[lk][write_idx:write_idx + n] = f[lk][:]
                write_idx += n

    logger.info("Merged HDF5 written: %s (%d instances)", output_path, total_n)


def merge_metadata_jsonl(
    shard_dir: Path,
    model_id: str,
    level: str,
    split: str,
    output_path: Path,
) -> None:
    """Merge metadata JSONL shards into a single parquet."""
    safe_model = model_id.replace("/", "_")
    pattern = f"{safe_model}_{level}_{split}_shard*.meta.jsonl"
    shard_files = sorted(shard_dir.glob(pattern))

    if not shard_files:
        logger.warning("No metadata JSONL files found: %s/%s", shard_dir, pattern)
        return

    rows = []
    for sf in shard_files:
        with open(sf) as f:
            for line in f:
                rows.append(json.loads(line.strip()))

    df = pd.DataFrame(rows)
    n_before = len(df)
    df = df.drop_duplicates(subset=["instance_id"], keep="last")
    if len(df) < n_before:
        logger.warning("Dropped %d duplicate instance_id rows from metadata.", n_before - len(df))
    df.to_parquet(str(output_path), index=False)
    logger.info("Merged metadata parquet: %s (%d rows)", output_path, len(df))


def merge_cf_jsonl(
    cf_dir: Path,
    model_id: str,
    level: str,
    split: str,
    output_path: Path,
) -> None:
    """Merge CF outcome JSONL shards into a single parquet."""
    safe_model = model_id.replace("/", "_")
    pattern = f"{safe_model}_{level}_{split}_cf_shard*.jsonl"
    shard_files = sorted(cf_dir.glob(pattern))

    if not shard_files:
        logger.warning("No CF outcome files found: %s/%s", cf_dir, pattern)
        return

    rows = []
    for sf in shard_files:
        with open(sf) as f:
            for line in f:
                rows.append(json.loads(line.strip()))

    df = pd.DataFrame(rows)
    df.to_parquet(str(output_path), index=False)
    logger.info("Merged CF parquet: %s (%d rows)", output_path, len(df))


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge inference/CF shards.")
    parser.add_argument("--model-id", default="Qwen/Qwen3-8B")
    parser.add_argument("--levels", nargs="+", default=["two_body_problem", "mind_the_gap"])
    parser.add_argument("--splits", nargs="+", default=["train", "eval"])
    parser.add_argument("--activations-dir", default="scratch/probing/activations")
    parser.add_argument("--cf-outcomes-dir", default="scratch/probing/cf_outcomes")
    parser.add_argument("--merge-cf", action="store_true", help="Merge CF outcomes instead of activations.")
    args = parser.parse_args()

    safe_model = args.model_id.replace("/", "_")

    for level in args.levels:
        for split in args.splits:
            if args.merge_cf:
                cf_dir = Path(args.cf_outcomes_dir)
                out = cf_dir / f"{safe_model}_{level}_{split}_cf.parquet"
                merge_cf_jsonl(cf_dir, args.model_id, level, split, out)
            else:
                act_dir = Path(args.activations_dir)
                h5_out = act_dir / f"{safe_model}_{level}_{split}.h5"
                meta_out = act_dir / f"{safe_model}_{level}_{split}_meta.parquet"
                merge_hdf5_shards(act_dir, args.model_id, level, split, h5_out)
                merge_metadata_jsonl(act_dir, args.model_id, level, split, meta_out)

    # After all levels+splits merged, combine per-split parquets into one metadata parquet
    # and concatenate all per-level-per-split HDF5 files into a single _merged.h5.
    if not args.merge_cf:
        act_dir = Path(args.activations_dir)
        all_dfs = []
        for level in args.levels:
            for split in args.splits:
                p = act_dir / f"{safe_model}_{level}_{split}_meta.parquet"
                if p.exists():
                    all_dfs.append(pd.read_parquet(str(p)))
        if all_dfs:
            combined = pd.concat(all_dfs, ignore_index=True)
            out = act_dir / f"{safe_model}_metadata.parquet"
            combined.to_parquet(str(out), index=False)
            logger.info("Combined metadata parquet: %s (%d rows)", out, len(combined))

        # Produce the single merged HDF5 that run_probe_training.py expects.
        per_level_h5s = [
            act_dir / f"{safe_model}_{level}_{split}.h5"
            for level in args.levels
            for split in args.splits
        ]
        merged_h5_out = act_dir / f"{safe_model}_merged.h5"
        merge_hdf5_files(per_level_h5s, merged_h5_out)
    else:
        cf_dir = Path(args.cf_outcomes_dir)
        all_dfs = []
        for level in args.levels:
            for split in args.splits:
                p = cf_dir / f"{safe_model}_{level}_{split}_cf.parquet"
                if p.exists():
                    all_dfs.append(pd.read_parquet(str(p)))
        if all_dfs:
            combined = pd.concat(all_dfs, ignore_index=True)
            out = cf_dir / f"{safe_model}_cf_outcomes.parquet"
            combined.to_parquet(str(out), index=False)
            logger.info("Combined CF parquet: %s (%d rows)", out, len(combined))


if __name__ == "__main__":
    main()
