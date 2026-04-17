"""
Entry point for §12 probe training (H1/H2/H3/H3b/H4a-c/H5a/H5b).

Reads HDF5 activations, metadata parquet, and CF outcomes parquet.
Writes per-hypothesis result parquets to results/probing/.

Usage:
    python -m experiments.probing.scripts.run_probe_training \
        --model-id Qwen/Qwen3-8B \
        --activations-dir scratch/probing/activations \
        --cf-outcomes-dir scratch/probing/cf_outcomes \
        --output-dir results/probing

CPU. Run via SLURM.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train all probes for the probing study.")
    parser.add_argument("--model-id", default="Qwen/Qwen3-8B")
    parser.add_argument("--activations-dir", default="scratch/probing/activations")
    parser.add_argument("--cf-outcomes-dir", default="scratch/probing/cf_outcomes")
    parser.add_argument("--h4-labels-dir", default="scratch/probing/h4_labels",
                        help="Dir containing precomputed H4 continuous labels parquets.")
    parser.add_argument("--output-dir", default="results/probing")
    parser.add_argument(
        "--hypotheses",
        nargs="+",
        default=["H1", "H2", "H3", "H3b", "H4", "H5"],
        help="Which hypotheses to train probes for.",
    )
    args = parser.parse_args()

    from experiments.probing.config import PRIMARY_LEVELS, FALLBACK_LEVEL
    from experiments.probing.probing.trainer import run_full_probe_training

    safe_model = args.model_id.replace("/", "_")
    hdf5_path = Path(args.activations_dir) / f"{safe_model}_merged.h5"
    metadata_parquet = Path(args.activations_dir) / f"{safe_model}_metadata.parquet"
    cf_outcomes_parquet = Path(args.cf_outcomes_dir) / f"{safe_model}_cf_outcomes.parquet"
    h4_labels_parquet = Path(args.h4_labels_dir) / f"{safe_model}_h4_labels.parquet"

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine which levels to use (check two_body_problem gate at execution time).
    levels = PRIMARY_LEVELS

    logger.info(
        "Starting probe training. Model=%s, levels=%s, hypotheses=%s",
        args.model_id, levels, args.hypotheses,
    )

    run_full_probe_training(
        hdf5_path=str(hdf5_path),
        metadata_parquet=str(metadata_parquet),
        cf_outcomes_parquet=str(cf_outcomes_parquet),
        h4_labels_parquet=str(h4_labels_parquet),
        levels=levels,
        output_dir=str(output_dir),
        hypotheses=args.hypotheses,
    )

    logger.info("Probe training complete. Results in %s", output_dir)

    # Inline verification: check that at least H1 results file was written.
    h1_path = output_dir / "h1_results.parquet"
    if not h1_path.exists():
        logger.error("FAIL: H1 results not found at %s", h1_path)
        sys.exit(1)
    logger.info("OK: %s exists.", h1_path)


if __name__ == "__main__":
    main()
