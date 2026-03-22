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
    "raicd": "#2A7FFF",
    "ftm": "#D97706",
}


def save(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(OUT_DIR / name, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def plot_delta_summary() -> None:
    benchmarks = ["Kd\nunseen_drug", "Kd\nblind_start", "Kd\nunseen_target", "patent\ntemporal"]
    x = np.arange(len(benchmarks))
    width = 0.28

    raicd = np.array([-0.0281, 0.0288, np.nan, -0.0080])
    ftm = np.array([np.nan, np.nan, 0.0214, -0.0050])

    raicd_ci = {
        1: (0.0145, 0.0431),
        3: (-0.0101, -0.0059),
    }
    ftm_ci = {
        3: (-0.0072, -0.0029),
    }

    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    ax.axhline(0.0, color="black", linewidth=0.9, linestyle="--", alpha=0.7)

    for idx, value in enumerate(raicd):
        if np.isnan(value):
            continue
        xpos = x[idx] - width / 2
        ax.bar(xpos, value, width=width, color=COLORS["raicd"], label="RAICD" if idx == 0 else None)
        if idx in raicd_ci:
            lo, hi = raicd_ci[idx]
            ax.errorbar(
                xpos,
                value,
                yerr=[[value - lo], [hi - value]],
                fmt="none",
                ecolor="black",
                capsize=3,
                linewidth=0.9,
            )

    for idx, value in enumerate(ftm):
        if np.isnan(value):
            continue
        xpos = x[idx] + width / 2
        ax.bar(xpos, value, width=width, color=COLORS["ftm"], label="FTM sparse" if idx == 2 else None)
        if idx in ftm_ci:
            lo, hi = ftm_ci[idx]
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
    ax.set_ylim(-0.04, 0.05)
    ax.legend(frameon=False, loc="upper right", ncol=2)
    save(fig, "benchmark_delta_summary.pdf")


def plot_patent_diagnosis() -> None:
    years = ["2019\nn=42,009", "2020\nn=6,947", "2021\nn=72"]
    overlap = ["low\nn=16,341", "mid\nn=16,342", "high\nn=16,345"]
    x_year = np.arange(len(years))
    x_overlap = np.arange(len(overlap))

    year_stats = {
        "base": ([0.7626, 0.8715, 0.9529], [0.0098, 0.0122, 0.0340]),
        "raicd": ([0.7583, 0.8395, 0.9211], [0.0026, 0.0021, 0.0104]),
        "ftm": ([0.7624, 0.8358, 0.9469], [0.0024, 0.0034, 0.0360]),
    }
    overlap_stats = {
        "base": ([0.5551, 0.7218, 0.9237], [0.0190, 0.0167, 0.0030]),
        "raicd": ([0.5505, 0.7274, 0.9085], [0.0071, 0.0076, 0.0090]),
        "ftm": ([0.5537, 0.7297, 0.9113], [0.0063, 0.0033, 0.0137]),
    }

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1), sharey=False)

    for key, label in [("base", "base"), ("raicd", "RAICD"), ("ftm", "FTM sparse")]:
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

    for key, label in [("base", "base"), ("raicd", "RAICD"), ("ftm", "FTM sparse")]:
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
