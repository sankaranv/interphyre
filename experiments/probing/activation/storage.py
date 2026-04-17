"""
HDF5 activation storage per §11.4.

Schema:
  /layer_{L}           [n_instances, 3, hidden_size]  float16  residual-stream at T1/T2/T3
  /embed               [n_instances, 3, hidden_size]  float16  pre-block-0 embedding (optional)
  /instance_id         [n_instances]                  S64      join key per §11.5
  /audit/layer_{L}     [n_audit, 3, hidden_size]      float32  5% float32 audit subset
  /audit/instance_id   [n_audit]                      S64      join key for audit rows
  /stats/mean/layer_{L}  [3, hidden_size]             float32  per-feature z-score mean (§11.3)
  /stats/std/layer_{L}   [3, hidden_size]             float32  per-feature z-score std  (§11.3)

Chunk shape (1, 3, hidden_size) per layer dataset so per-instance reads are one I/O operation.
Compression: gzip level 4 per config. SWMR mode for concurrent reads during long writes.

Normalization statistics are fit on training instances only and stored with a blake2b
hash of the sorted training instance_id list for split-leakage auditing.
"""

from __future__ import annotations

import hashlib

try:
    import h5py
except ImportError:
    h5py = None  # type: ignore[assignment]

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore[assignment]

from experiments.probing.config import HDF5_COMPRESSION, HDF5_COMPRESSION_OPTS


def create_activation_file(
    filepath: str,
    num_layers: int,
    hidden_size: int,
    expected_n_instances: int,
) -> h5py.File:
    """Create (or open-for-append) the HDF5 file with the §11.4 schema.

    All datasets are created with maxshape=(None, ...) so they grow as
    instances are appended.

    Chunk shape (1, 3, hidden_size) ensures per-instance reads are one-shot.
    Compression: gzip level 4 per config to stay within the ~53 GB budget.

    SWMR mode is intentionally omitted: there are no concurrent readers during
    inference, and SWMR sets a write-lock flag that becomes a stale lock on
    preemption, requiring the file to be deleted and the shard restarted.
    """
    hdf5_file = h5py.File(filepath, "a")

    chunk = (1, 3, hidden_size)
    max_shape = (None, 3, hidden_size)
    init_shape = (0, 3, hidden_size)

    compress_kwargs = {
        "compression": HDF5_COMPRESSION,
        "compression_opts": HDF5_COMPRESSION_OPTS,
        "chunks": chunk,
    }

    # Create /layer_{L} datasets for all transformer blocks.
    for layer_idx in range(num_layers):
        key = f"layer_{layer_idx}"
        if key not in hdf5_file:
            hdf5_file.create_dataset(
                key,
                shape=init_shape,
                maxshape=max_shape,
                dtype="float16",
                **compress_kwargs,
            )

    # /embed dataset for pre-block-0 embeddings (§11.1 optional).
    if "embed" not in hdf5_file:
        hdf5_file.create_dataset(
            "embed",
            shape=init_shape,
            maxshape=max_shape,
            dtype="float16",
            **compress_kwargs,
        )

    # /instance_id: fixed-length 64-byte strings for the join key per §11.5.
    if "instance_id" not in hdf5_file:
        hdf5_file.create_dataset(
            "instance_id",
            shape=(0,),
            maxshape=(None,),
            dtype=h5py.string_dtype(encoding="utf-8", length=64),
        )

    # /audit/ group: float32 copies for 5% audit subset per §11.4.
    if "audit" not in hdf5_file:
        audit_group = hdf5_file.create_group("audit")
    else:
        audit_group = hdf5_file["audit"]

    for layer_idx in range(num_layers):
        key = f"layer_{layer_idx}"
        if key not in audit_group:
            audit_group.create_dataset(
                key,
                shape=init_shape,
                maxshape=max_shape,
                dtype="float32",
                **compress_kwargs,
            )

    if "instance_id" not in audit_group:
        audit_group.create_dataset(
            "instance_id",
            shape=(0,),
            maxshape=(None,),
            dtype=h5py.string_dtype(encoding="utf-8", length=64),
        )

    # /stats group will be populated by compute_and_write_normalization_stats.
    if "stats" not in hdf5_file:
        hdf5_file.create_group("stats")
        hdf5_file["stats"].create_group("mean")
        hdf5_file["stats"].create_group("std")

    return hdf5_file


def write_instance_activations(
    hdf5_file: h5py.File,
    instance_id: str,
    layer_activations: dict[int, np.ndarray],
    is_audit: bool = False,
) -> None:
    """Append one instance's activations to the HDF5 file.

    layer_activations maps layer index -> [3, hidden_size] float32 array
    (T1 at index 0, T2 at 1, T3 at 2 per §11.4 storage convention).

    Main datasets store float16 to stay within the ~53 GB budget.
    Audit datasets (5% subset) retain float32 for fidelity auditing.

    The /instance_id dataset is appended once per call regardless of is_audit;
    the /audit/instance_id dataset is additionally appended when is_audit=True.
    """
    # Encode instance_id as fixed-length bytes padded to 64 characters.
    id_bytes = instance_id.encode("utf-8")[:64].ljust(64, b"\x00")

    for layer_idx, activation in layer_activations.items():
        key = f"layer_{layer_idx}"
        dataset = hdf5_file[key]
        row = activation.astype(np.float16)[np.newaxis, ...]  # [1, 3, H]
        current_size = dataset.shape[0]
        dataset.resize(current_size + 1, axis=0)
        dataset[current_size] = row

        if is_audit:
            audit_dataset = hdf5_file[f"audit/{key}"]
            audit_row = activation.astype(np.float32)[np.newaxis, ...]
            audit_current = audit_dataset.shape[0]
            audit_dataset.resize(audit_current + 1, axis=0)
            audit_dataset[audit_current] = audit_row

    # Append instance_id to main /instance_id dataset.
    id_dataset = hdf5_file["instance_id"]
    current_id_size = id_dataset.shape[0]
    id_dataset.resize(current_id_size + 1, axis=0)
    id_dataset[current_id_size] = id_bytes

    if is_audit:
        audit_id_dataset = hdf5_file["audit/instance_id"]
        audit_id_current = audit_id_dataset.shape[0]
        audit_id_dataset.resize(audit_id_current + 1, axis=0)
        audit_id_dataset[audit_id_current] = id_bytes


def compute_and_write_normalization_stats(
    hdf5_file: h5py.File,
    train_instance_ids: list[str],
    num_layers: int,
) -> None:
    """Compute per-feature z-score statistics over training instances per §11.3.

    For each layer L, loads /layer_{L}[train_mask] (cast to float32), computes
    population mean and std across the n_train axis (one statistic per feature
    per position), and writes to /stats/mean/layer_{L} and /stats/std/layer_{L}.

    Dead-feature guard: std values below STANDARDIZATION_MIN_STD (1e-6) are
    clipped to that value so z-scoring never divides by zero.

    The /stats group receives a stats_source_split_hash attribute containing
    the blake2b-256 digest of the sorted train_instance_ids, enabling downstream
    auditing of split integrity without re-running the stats computation.
    """
    from experiments.probing.config import STANDARDIZATION_MIN_STD

    train_row_indices = get_instance_row_indices(hdf5_file, train_instance_ids)

    # blake2b hash of the sorted instance_id list for auditing split leakage.
    sorted_ids = sorted(train_instance_ids)
    hash_input = "\n".join(sorted_ids).encode("utf-8")
    split_hash = hashlib.blake2b(hash_input, digest_size=32).hexdigest()
    hdf5_file["stats"].attrs["stats_source_split_hash"] = split_hash

    for layer_idx in range(num_layers):
        key = f"layer_{layer_idx}"
        # Load training rows as float32 for numerically stable stats.
        # Shape: [n_train, 3, hidden_size].
        train_data = hdf5_file[key][train_row_indices].astype(np.float32)

        # §11.3: population mean and std, per feature per position.
        # Axis 0 is the instance axis; output shape is [3, hidden_size].
        mean = train_data.mean(axis=0)
        std = train_data.std(axis=0)

        # Dead-feature guard: clip std to min 1e-6 so z-scoring is well-defined.
        std = np.maximum(std, STANDARDIZATION_MIN_STD)

        mean_key = f"stats/mean/{key}"
        std_key = f"stats/std/{key}"

        if mean_key in hdf5_file:
            del hdf5_file[mean_key]
        if std_key in hdf5_file:
            del hdf5_file[std_key]

        hdf5_file.create_dataset(mean_key, data=mean, dtype="float32")
        hdf5_file.create_dataset(std_key, data=std, dtype="float32")


def load_layer_activations(
    hdf5_file: h5py.File,
    layer_idx: int,
    instance_ids: list[str],
    position_idx: int,
    normalize: bool = True,
) -> np.ndarray:
    """Load activations for specified instances at one (layer, position).

    Args:
        layer_idx:    transformer block index.
        instance_ids: list of instance_id strings to load.
        position_idx: 0=T1, 1=T2, 2=T3 per §11.4 storage convention.
        normalize:    if True, apply z-score using /stats/mean and /stats/std.

    Returns:
        [n_instances, hidden_size] float32 array, z-scored when normalize=True.
        The same mean/std fit on training instances are applied here without
        refitting, per §11.3's single-fit / multi-apply contract.
    """
    row_indices = get_instance_row_indices(hdf5_file, instance_ids)
    key = f"layer_{layer_idx}"

    # Load the slice at the requested position index and cast to float32.
    # Shape after indexing: [n_instances, hidden_size].
    activations = hdf5_file[key][row_indices, position_idx, :].astype(np.float32)

    if normalize:
        mean = hdf5_file[f"stats/mean/{key}"][position_idx, :].astype(np.float32)
        std = hdf5_file[f"stats/std/{key}"][position_idx, :].astype(np.float32)
        activations = (activations - mean) / std

    return activations


def get_instance_row_indices(
    hdf5_file: h5py.File, instance_ids: list[str]
) -> list[int]:
    """Return the row positions in /instance_id for the given instance_ids.

    Builds a lookup dict from the full /instance_id dataset on first call, which
    is O(n_stored) but avoids repeated full-dataset scans when called once per
    load operation. Raises KeyError if any instance_id is not found.
    """
    stored = hdf5_file["instance_id"][:]
    # Decode fixed-length byte strings to stripped Python strings.
    id_to_row = {
        row_bytes.decode("utf-8").rstrip("\x00"): row_idx
        for row_idx, row_bytes in enumerate(stored)
    }
    row_indices = []
    for iid in instance_ids:
        if iid not in id_to_row:
            raise KeyError(f"instance_id not found in HDF5 file: {iid!r}")
        row_indices.append(id_to_row[iid])
    return row_indices
