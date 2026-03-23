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
    "dtilm": "#2A7FFF",
    "hyperpcm": "#D97706",
}


def save(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(OUT_DIR / name, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def plot_delta_summary() -> None:
    benchmarks = ["Kd\nunseen_drug", "Kd\nblind_start", "Kd\nunseen_target", "patent\ntemporal"]
    x = np.arange(len(benchmarks))
    width = 0.28

    dtilm = np.array([-0.0505, -0.0100, -0.0088, 0.0054])
    hyperpcm = np.array([0.0185, 0.0092, -0.0269, -0.0019])

    dtilm_ci = {
        0: (-0.0614, -0.0399),
        1: (-0.0304, 0.0132),
        2: (-0.0206, 0.0021),
        3: (0.0028, 0.0079),
    }
    hyperpcm_ci = {
        0: (0.0082, 0.0279),
        1: (-0.0134, 0.0317),
        2: (-0.0390, -0.0151),
        3: (-0.0045, 0.0009),
    }

    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    ax.axhline(0.0, color="black", linewidth=0.9, linestyle="--", alpha=0.7)

    for idx, value in enumerate(dtilm):
        xpos = x[idx] - width / 2
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
        xpos = x[idx] + width / 2
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
    ax.set_ylim(-0.07, 0.04)
    ax.legend(frameon=False, loc="upper right", ncol=2)
    save(fig, "benchmark_delta_summary.pdf")


def plot_patent_diagnosis() -> None:
    years = ["2019\nn=42,009", "2020\nn=6,947", "2021\nn=72"]
    overlap = ["low\nn=16,341", "mid\nn=16,342", "high\nn=16,345"]
    x_year = np.arange(len(years))
    x_overlap = np.arange(len(overlap))

    year_stats = {
        "base": ([0.7626, 0.8715, 0.9529], [0.0098, 0.0122, 0.0340]),
        "dtilm": ([0.7734, 0.8545, 0.7511], [0.0071, 0.0100, 0.0485]),
        "hyperpcm": ([0.7637, 0.8526, 0.6953], [0.0049, 0.0139, 0.0151]),
    }
    overlap_stats = {
        "base": ([0.5551, 0.7218, 0.9237], [0.0190, 0.0167, 0.0030]),
        "dtilm": ([0.6353, 0.7489, 0.8866], [0.0175, 0.0094, 0.0097]),
        "hyperpcm": ([0.6147, 0.7513, 0.8767], [0.0208, 0.0060, 0.0042]),
    }

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1), sharey=False)

    for key, label in [("base", "base"), ("dtilm", "DTI-LM"), ("hyperpcm", "HyperPCM")]:
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

    for key, label in [("base", "base"), ("dtilm", "DTI-LM"), ("hyperpcm", "HyperPCM")]:
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
