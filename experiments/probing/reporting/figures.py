"""
Figure generation for the probing study (§15.1, F1–F5).

All figures use the Okabe-Ito colorblind-safe palette, constrained layout,
and dual PDF+PNG output. Font sizing targets NeurIPS single-column width
(~3.25 inches per panel).
"""

from __future__ import annotations

from pathlib import Path

try:
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

import numpy as np

# Okabe-Ito colorblind-safe palette.
_OKABE_ITO = [
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#009E73",  # bluish green
    "#F0E442",  # yellow
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish purple
    "#000000",  # black
]

_PASS_COLOR = "#009E73"  # bluish green
_FAIL_COLOR = "#D55E00"  # vermillion
_BASELINE_COLOR = "#56B4E9"  # sky blue


def _require_matplotlib() -> None:
    """Raise if matplotlib is not installed."""
    if not HAS_MATPLOTLIB:
        raise RuntimeError("matplotlib is not installed; cannot generate figures")


def _apply_style() -> None:
    """Apply consistent publication style for the probing study."""
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 8,
            "axes.labelsize": 9,
            "axes.titlesize": 9,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "axes.prop_cycle": plt.cycler(color=_OKABE_ITO),
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def _save_dual(fig: plt.Figure, output_path: str) -> None:
    """Save figure as both .pdf and .png at 300 DPI.

    output_path is treated as a stem: the suffix is replaced (or added) with
    .pdf and .png. The parent directory is created if absent.
    """
    stem = Path(output_path).with_suffix("")
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(stem) + ".pdf", bbox_inches="tight")
    fig.savefig(str(stem) + ".png", bbox_inches="tight", dpi=300)


def plot_f1_h1_layer_sweep(
    scores_grids: dict[str, np.ndarray],
    layer_indices: list[int],
    best_layer_positions: dict[str, tuple[int, int]],
    output_path: str,
) -> None:
    """F1: Layer × position heatmap of inner-val balanced accuracy per level.

    One panel per level. Each cell shows mean balanced accuracy on the inner
    validation set. The best (L*, p*) is highlighted with a black box drawn
    over the cell border to make the selected hyperparameter visible.

    Args:
        scores_grids: level_name -> [n_layers, 3] float array of balanced-acc
            values at positions {T1, T2, T3} (columns 0, 1, 2).
        layer_indices: list of layer indices corresponding to rows in scores_grids.
        best_layer_positions: level_name -> (L*, p*) index tuple into
            (layer_indices, position_index).
        output_path: file stem for dual PDF+PNG output.
    """
    _require_matplotlib()
    _apply_style()
    n_levels = len(scores_grids)
    fig, axes = plt.subplots(
        1,
        n_levels,
        figsize=(3.25 * n_levels, 3.5),
        layout="constrained",
    )
    if n_levels == 1:
        axes = [axes]

    position_labels = ["T1", "T2", "T3"]

    for ax, (level_name, grid) in zip(axes, scores_grids.items()):
        # grid: [n_layers, 3]
        im = ax.imshow(
            grid,
            aspect="auto",
            vmin=0.5,
            vmax=1.0,
            cmap="viridis",
            origin="upper",
        )
        ax.set_xticks(range(len(position_labels)))
        ax.set_xticklabels(position_labels)
        ax.set_yticks(range(len(layer_indices)))
        ax.set_yticklabels(layer_indices, fontsize=6)
        ax.set_xlabel("Position")
        ax.set_ylabel("Layer")
        ax.set_title(level_name.replace("_", " ").title())

        # Draw black box at the best (L*, p*) cell.
        if level_name in best_layer_positions:
            l_star_idx, p_star_idx = best_layer_positions[level_name]
            rect = plt.Rectangle(
                (p_star_idx - 0.5, l_star_idx - 0.5),
                1,
                1,
                linewidth=2,
                edgecolor="black",
                facecolor="none",
            )
            ax.add_patch(rect)

        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Balanced acc.")

    _save_dual(fig, output_path)
    plt.close(fig)


def plot_f2_h3_headline(
    probe_results: dict,
    output_path: str,
) -> None:
    """F2: Grouped bar chart of LLM probe vs baseline balanced accuracy per level.

    Two bars per (target, direction) group: LLM probe (filled) and geometric
    baseline (hatched). Chance line at 0.5 and pass threshold at 0.55 are
    drawn as horizontal dashed/dotted lines. Error bars show 95% CI.

    Args:
        probe_results: level_name -> {(target, direction): {"acc", "ci",
            "baseline_acc", "baseline_ci"}} nested dict.
        output_path: file stem for dual PDF+PNG output.
    """
    _require_matplotlib()
    _apply_style()
    levels = list(probe_results.keys())
    n_levels = len(levels)
    fig, axes = plt.subplots(
        1,
        n_levels,
        figsize=(4.0 * n_levels, 3.5),
        layout="constrained",
    )
    if n_levels == 1:
        axes = [axes]

    for ax, level_name in zip(axes, levels):
        level_data = probe_results[level_name]
        keys = list(level_data.keys())
        x = np.arange(len(keys))
        width = 0.35

        probe_accs = [level_data[k]["acc"] for k in keys]
        probe_cis = [level_data[k]["ci"] for k in keys]
        base_accs = [level_data[k]["baseline_acc"] for k in keys]
        base_cis = [level_data[k]["baseline_ci"] for k in keys]

        # CI tuples are (lower, upper); convert to symmetric half-widths.
        probe_errs = [[a - ci[0], ci[1] - a] for a, ci in zip(probe_accs, probe_cis)]
        base_errs = [[a - ci[0], ci[1] - a] for a, ci in zip(base_accs, base_cis)]

        ax.bar(
            x - width / 2,
            probe_accs,
            width,
            yerr=np.array(probe_errs).T,
            capsize=3,
            color=_OKABE_ITO[0],
            label="LLM probe",
        )
        ax.bar(
            x + width / 2,
            base_accs,
            width,
            yerr=np.array(base_errs).T,
            capsize=3,
            color=_BASELINE_COLOR,
            hatch="///",
            label="Baseline",
        )

        ax.axhline(0.5, linestyle="--", linewidth=0.8, color="gray", label="Chance")
        ax.axhline(
            0.55,
            linestyle=":",
            linewidth=0.8,
            color="black",
            label="Pass threshold (0.55)",
        )

        tick_labels = [f"{t}\n{d}" for t, d in keys]
        ax.set_xticks(x)
        ax.set_xticklabels(tick_labels, fontsize=6)
        ax.set_ylim(0.40, 1.05)
        ax.set_ylabel("Balanced accuracy")
        ax.set_title(level_name.replace("_", " ").title())
        ax.legend(fontsize=6)

    _save_dual(fig, output_path)
    plt.close(fig)


def plot_f3_h4_precision(
    h4_results: dict,
    output_path: str,
) -> None:
    """F3: Three-panel R² heatmaps for H4a, H4b, H4c.

    Each panel is a level × sub-hypothesis heatmap comparing LLM probe R²
    against baseline upper CI. Cells below threshold are shown in a distinct
    color to make pass/fail immediately visible.

    Args:
        h4_results: {sub_hypothesis: {level -> {"r2", "ci", "baseline_r2",
            "baseline_ci"}}}. sub_hypothesis in {"H4a", "H4b", "H4c"}.
        output_path: file stem for dual PDF+PNG output.
    """
    _require_matplotlib()
    _apply_style()
    sub_hyps = ["H4a", "H4b", "H4c"]
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.5), layout="constrained")

    for ax, sub_hyp in zip(axes, sub_hyps):
        if sub_hyp not in h4_results:
            ax.set_visible(False)
            continue

        sub_data = h4_results[sub_hyp]
        levels = list(sub_data.keys())

        r2_vals = np.array([[sub_data[lv]["r2"]] for lv in levels])
        baseline_upper = np.array([[sub_data[lv]["baseline_ci"][1]] for lv in levels])
        # Display difference: probe R² − baseline upper CI.
        delta = r2_vals - baseline_upper

        im = ax.imshow(
            delta,
            aspect="auto",
            vmin=-0.3,
            vmax=0.5,
            cmap="RdBu",
        )
        ax.set_xticks([0])
        ax.set_xticklabels(["ΔR²"])
        ax.set_yticks(range(len(levels)))
        ax.set_yticklabels([lv.replace("_", " ").title() for lv in levels], fontsize=7)
        ax.set_title(sub_hyp)
        fig.colorbar(
            im,
            ax=ax,
            fraction=0.046,
            pad=0.04,
            label="Probe − Baseline upper CI",
        )

    _save_dual(fig, output_path)
    plt.close(fig)


def plot_f4_h5_transfer(
    h5a_results: dict,
    h5b_results: dict,
    levels: list[str],
    output_path: str,
) -> None:
    """F4: Transfer generalization — LOLO bar chart (a) and pairwise matrix (b).

    Panel (a): LOLO balanced accuracy per held-out level. Bar color encodes
    pass (green) or fail (vermillion) relative to threshold. Error bars show
    95% CI.

    Panel (b): Pairwise-transfer accuracy matrix with source levels as rows
    and target levels as columns. Diagonal is masked (not applicable).

    Args:
        h5a_results: {held_out_level: {"acc", "ci", "baseline_upper_ci"}}.
        h5b_results: {(source, target): {"acc", "ci", "baseline_upper_ci"}}.
        levels: ordered list of level names.
        output_path: file stem for dual PDF+PNG output.
    """
    _require_matplotlib()
    _apply_style()
    from ..config import H5_TRANSFER_BALANCED_ACC_THRESHOLD

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(10, 3.5), layout="constrained")

    # Panel (a): LOLO bar chart.
    held_out_levels = list(h5a_results.keys())
    accs = [h5a_results[lv]["acc"] for lv in held_out_levels]
    cis = [h5a_results[lv]["ci"] for lv in held_out_levels]
    errs = [[a - ci[0], ci[1] - a] for a, ci in zip(accs, cis)]
    colors = [
        _PASS_COLOR if a >= H5_TRANSFER_BALANCED_ACC_THRESHOLD else _FAIL_COLOR
        for a in accs
    ]

    ax_a.bar(
        range(len(held_out_levels)),
        accs,
        color=colors,
        yerr=np.array(errs).T,
        capsize=4,
    )
    ax_a.axhline(
        0.55, linestyle=":", linewidth=0.8, color="black", label="Pass threshold"
    )
    ax_a.axhline(0.5, linestyle="--", linewidth=0.8, color="gray", label="Chance")
    ax_a.set_xticks(range(len(held_out_levels)))
    ax_a.set_xticklabels(
        [lv.replace("_", " ").title() for lv in held_out_levels],
        rotation=20,
        ha="right",
        fontsize=7,
    )
    ax_a.set_ylim(0.40, 1.05)
    ax_a.set_ylabel("Balanced accuracy (LOLO)")
    ax_a.set_title("H5a: LOLO transfer")
    ax_a.legend(fontsize=6)

    # Panel (b): pairwise-transfer matrix.
    n = len(levels)
    matrix = np.full((n, n), np.nan)
    level_idx = {lv: i for i, lv in enumerate(levels)}
    for (src, tgt), result in h5b_results.items():
        i, j = level_idx.get(src, None), level_idx.get(tgt, None)
        if i is not None and j is not None and i != j:
            matrix[i, j] = result["acc"]

    im = ax_b.imshow(
        matrix,
        aspect="equal",
        vmin=0.4,
        vmax=1.0,
        cmap="viridis",
    )
    ax_b.set_xticks(range(n))
    ax_b.set_xticklabels(
        [lv.replace("_", " ").title() for lv in levels],
        rotation=30,
        ha="right",
        fontsize=7,
    )
    ax_b.set_yticks(range(n))
    ax_b.set_yticklabels([lv.replace("_", " ").title() for lv in levels], fontsize=7)
    ax_b.set_title("H5b: Pairwise transfer")
    ax_b.set_xlabel("Target level")
    ax_b.set_ylabel("Source level")
    fig.colorbar(im, ax=ax_b, fraction=0.046, pad=0.04, label="Balanced acc.")

    _save_dual(fig, output_path)
    plt.close(fig)


def plot_f5_h6_steering(
    h6a_results: dict,
    h6b_results: dict,
    h6c_results: dict,
    alpha_grid: np.ndarray,
    output_path: str,
) -> None:
    """F5: Three-panel steering figure sharing the α axis.

    Panel (a): H6a median steered vs p95 random behavioral-change curves.
    Panel (b): H6b mean ΔCF-flip-rate with bootstrap CI ribbon.
    Panel (c): H6c parseable and coherent fractions.

    All panels share the same x-axis (α values). Log scale is used because
    the α grid is log-spaced; α=0 is shown as a gap marker.

    Args:
        h6a_results: {alpha: {"median_steered", "p95_random", "passes"}}.
        h6b_results: {alpha: {"mean_delta", "ci_lower", "ci_upper"}}.
        h6c_results: {alpha: {"parseable_fraction", "coherent_fraction"}}.
        alpha_grid: [21] array of alpha values (negative, 0, positive).
        output_path: file stem for dual PDF+PNG output.
    """
    _require_matplotlib()
    _apply_style()

    # Separate non-zero alphas for plotting (α=0 is skipped; log-spaced grid).
    all_alphas_nonzero = sorted(a for a in alpha_grid if a != 0)

    fig, (ax_a, ax_b, ax_c) = plt.subplots(
        3, 1, figsize=(5.5, 7.5), layout="constrained", sharex=False
    )

    # Panel (a): H6a median steered vs p95 random.
    steered_vals = [
        h6a_results.get(a, {}).get("median_steered", np.nan) for a in all_alphas_nonzero
    ]
    random_vals = [
        h6a_results.get(a, {}).get("p95_random", np.nan) for a in all_alphas_nonzero
    ]
    ax_a.plot(
        range(len(all_alphas_nonzero)),
        steered_vals,
        color=_OKABE_ITO[0],
        marker="o",
        markersize=4,
        label="DIM steered (median)",
    )
    ax_a.plot(
        range(len(all_alphas_nonzero)),
        random_vals,
        color=_BASELINE_COLOR,
        linestyle="--",
        marker="s",
        markersize=4,
        label="Random control (p95)",
    )
    ax_a.set_xticks(range(len(all_alphas_nonzero)))
    ax_a.set_xticklabels(
        [f"{a:.2f}" for a in all_alphas_nonzero], rotation=45, ha="right", fontsize=5
    )
    ax_a.set_ylabel("Behavioral change")
    ax_a.set_title("H6a: DIM steering vs random control")
    ax_a.legend(fontsize=6)

    # Panel (b): H6b mean ΔCF-flip-rate with CI ribbon.
    mean_deltas = [
        h6b_results.get(a, {}).get("mean_delta", np.nan) for a in all_alphas_nonzero
    ]
    ci_lowers = [
        h6b_results.get(a, {}).get("ci_lower", np.nan) for a in all_alphas_nonzero
    ]
    ci_uppers = [
        h6b_results.get(a, {}).get("ci_upper", np.nan) for a in all_alphas_nonzero
    ]
    x_vals = range(len(all_alphas_nonzero))
    ax_b.plot(x_vals, mean_deltas, color=_OKABE_ITO[4], marker="o", markersize=4)
    ax_b.fill_between(
        x_vals,
        ci_lowers,
        ci_uppers,
        alpha=0.25,
        color=_OKABE_ITO[4],
        label="95% CI",
    )
    ax_b.axhline(0, linestyle="--", linewidth=0.8, color="gray")
    ax_b.set_xticks(list(x_vals))
    ax_b.set_xticklabels(
        [f"{a:.2f}" for a in all_alphas_nonzero], rotation=45, ha="right", fontsize=5
    )
    ax_b.set_ylabel("ΔCF-flip-rate")
    ax_b.set_title("H6b: Physics-consistent shift")
    ax_b.legend(fontsize=6)

    # Panel (c): H6c parseable and coherent fractions.
    parseable_vals = [
        h6c_results.get(a, {}).get("parseable_fraction", np.nan)
        for a in all_alphas_nonzero
    ]
    coherent_vals = [
        h6c_results.get(a, {}).get("coherent_fraction", np.nan)
        for a in all_alphas_nonzero
    ]
    ax_c.plot(
        x_vals,
        parseable_vals,
        color=_OKABE_ITO[2],
        marker="^",
        markersize=4,
        label="Parseable",
    )
    ax_c.plot(
        x_vals,
        coherent_vals,
        color=_OKABE_ITO[5],
        marker="v",
        markersize=4,
        label="Coherent (parseable + below PPL)",
    )
    ax_c.axhline(
        0.80,
        linestyle=":",
        linewidth=0.8,
        color="black",
        label="Pass threshold (0.80)",
    )
    ax_c.set_xticks(list(x_vals))
    ax_c.set_xticklabels(
        [f"{a:.2f}" for a in all_alphas_nonzero], rotation=45, ha="right", fontsize=5
    )
    ax_c.set_xlabel("α (steering magnitude)")
    ax_c.set_ylabel("Fraction")
    ax_c.set_ylim(-0.05, 1.10)
    ax_c.set_title("H6c: Output coherence")
    ax_c.legend(fontsize=6)

    _save_dual(fig, output_path)
    plt.close(fig)
