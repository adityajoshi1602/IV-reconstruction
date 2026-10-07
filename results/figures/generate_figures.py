"""Generate final benchmark figures from saved result tables.

Run after the benchmark notebook has produced results/benchmark_results.csv.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"


def require_results() -> pd.DataFrame:
    path = RESULTS / "benchmark_results.csv"
    df = pd.read_csv(path)
    required = {"model", "missingness", "rmse", "mae"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required result columns: {sorted(missing)}")
    if df.empty:
        raise ValueError("benchmark_results.csv is empty. Run the benchmark first.")
    return df


def line_plot(df: pd.DataFrame, metric: str, filename: str, title: str) -> None:
    plt.figure(figsize=(8, 5))
    for model, group in df.groupby("model", sort=True):
        group = group.sort_values("missingness")
        plt.plot(group["missingness"] * 100, group[metric], marker="o", label=model)
    plt.xlabel("Masked holdout (% of observed evaluation cells)")
    plt.ylabel(metric.upper())
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES / filename, dpi=200)
    plt.close()


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    df = require_results()

    line_plot(
        df, "rmse",
        "rmse_vs_missingness.png",
        "Reconstruction RMSE vs Controlled Missingness",
    )
    line_plot(
        df, "mae",
        "mae_vs_missingness.png",
        "Reconstruction MAE vs Controlled Missingness",
    )

    # One compact comparison plot: RMSE by missingness/model.
    pivot = df.pivot(index="missingness", columns="model", values="rmse")
    ax = pivot.plot(kind="bar", figsize=(9, 5))
    ax.set_xlabel("Missingness")
    ax.set_ylabel("RMSE")
    ax.set_title("Model Comparison Across Missingness Levels")
    ax.set_xticklabels([f"{int(x*100)}%" for x in pivot.index], rotation=0)
    plt.tight_layout()
    plt.savefig(FIGURES / "model_comparison.png", dpi=200)
    plt.close()


if __name__ == "__main__":
    main()
