from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


OUT_DIR = Path(__file__).resolve().parent

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)

COLORS = {
    "base": "#4C566A",
    "rf": "#2F855A",
    "dtilm": "#2A7FFF",
    "hyperpcm": "#D97706",
}


def save(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(OUT_DIR / name, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def plot_delta_summary() -> None:
    benchmarks = ["Kd\nunseen_drug", "Kd\nblind_start", "Kd\nunseen_target", "patent\ntemporal", "nonpatent\ntemporal"]
    x = np.arange(len(benchmarks))
    width = 0.22

    rf = np.array([0.1830, 0.0775, -0.0042, 0.0463, 0.0832])
    dtilm = np.array([-0.0505, -0.0100, -0.0088, 0.0054, 0.0163])
    hyperpcm = np.array([0.0185, 0.0092, -0.0269, -0.0019, np.nan])

    rf_ci = {
        0: (0.1739, 0.1919),
        1: (0.0546, 0.1030),
        2: (-0.0175, 0.0084),
        3: (0.0441, 0.0484),
        4: (0.0737, 0.0920),
    }
    dtilm_ci = {
        0: (-0.0614, -0.0399),
        1: (-0.0304, 0.0132),
        2: (-0.0206, 0.0021),
        3: (0.0028, 0.0079),
        4: (0.0064, 0.0265),
    }
    hyperpcm_ci = {
        0: (0.0082, 0.0279),
        1: (-0.0134, 0.0317),
        2: (-0.0390, -0.0151),
        3: (-0.0045, 0.0009),
    }

    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    ax.axhline(0.0, color="black", linewidth=0.9, linestyle="--", alpha=0.7)

    for idx, value in enumerate(rf):
        xpos = x[idx] - width
        ax.bar(xpos, value, width=width, color=COLORS["rf"], label="RF" if idx == 0 else None)
        lo, hi = rf_ci[idx]
        ax.errorbar(
            xpos,
            value,
            yerr=[[value - lo], [hi - value]],
            fmt="none",
            ecolor="black",
            capsize=3,
            linewidth=0.9,
        )

    for idx, value in enumerate(dtilm):
        xpos = x[idx]
        ax.bar(xpos, value, width=width, color=COLORS["dtilm"], label="DTI-LM" if idx == 0 else None)
        lo, hi = dtilm_ci[idx]
        ax.errorbar(
            xpos,
            value,
            yerr=[[value - lo], [hi - value]],
            fmt="none",
            ecolor="black",
            capsize=3,
            linewidth=0.9,
        )

    for idx, value in enumerate(hyperpcm):
        if np.isnan(value):
            continue
        xpos = x[idx] + width
        ax.bar(xpos, value, width=width, color=COLORS["hyperpcm"], label="HyperPCM" if idx == 0 else None)
        lo, hi = hyperpcm_ci[idx]
        ax.errorbar(
            xpos,
            value,
            yerr=[[value - lo], [hi - value]],
            fmt="none",
            ecolor="black",
            capsize=3,
            linewidth=0.9,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(benchmarks)
    ax.set_ylabel("Mean AUPRC delta vs base")
    ax.set_ylim(-0.07, 0.22)
    ax.legend(frameon=False, loc="upper right", ncol=3)
    save(fig, "benchmark_delta_summary.pdf")


def plot_patent_diagnosis() -> None:
    years = ["2019\nn=42,009", "2020-2021\nn=7,019"]
    overlap = ["low\nn=16,341", "mid\nn=16,342", "high\nn=16,345"]
    x_year = np.arange(len(years))
    x_overlap = np.arange(len(overlap))

    year_stats = {
        "base": ([0.7626, 0.8716], [0.0098, 0.0121]),
        "rf": ([0.8062, 0.9098], [0.0013, 0.0005]),
        "dtilm": ([0.7734, 0.8533], [0.0071, 0.0100]),
    }
    overlap_stats = {
        "base": ([0.5551, 0.7218, 0.9237], [0.0190, 0.0167, 0.0030]),
        "rf": ([0.6005, 0.7606, 0.9426], [0.0034, 0.0012, 0.0005]),
        "dtilm": ([0.6353, 0.7489, 0.8866], [0.0175, 0.0094, 0.0097]),
    }

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1), sharey=False)

    for key, label in [("base", "base"), ("rf", "RF"), ("dtilm", "DTI-LM")]:
        y, err = year_stats[key]
        axes[0].errorbar(
            x_year,
            y,
            yerr=err,
            marker="o",
            linewidth=1.5,
            capsize=3,
            color=COLORS[key],
            label=label,
        )
    axes[0].set_xticks(x_year)
    axes[0].set_xticklabels(years)
    axes[0].set_ylabel("Mean AUPRC")
    axes[0].set_title("Patent year bands")
    axes[0].set_ylim(0.72, 0.99)

    for key, label in [("base", "base"), ("rf", "RF"), ("dtilm", "DTI-LM")]:
        y, err = overlap_stats[key]
        axes[1].errorbar(
            x_overlap,
            y,
            yerr=err,
            marker="o",
            linewidth=1.5,
            capsize=3,
            color=COLORS[key],
            label=label,
        )
    axes[1].set_xticks(x_overlap)
    axes[1].set_xticklabels(overlap)
    axes[1].set_title("Patent overlap buckets")
    axes[1].set_ylim(0.50, 0.96)
    axes[1].legend(frameon=False, loc="lower right")

    save(fig, "patent_shift_diagnosis.pdf")


if __name__ == "__main__":
    plot_delta_summary()
    plot_patent_diagnosis()
