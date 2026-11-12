import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from ksd.data import load_raw, pair_events, pseudonymize, to_common_format
from ksd.distance import DISTANCES
from ksd.evaluate import (
    build_windows,
    eer,
    frr_at_far,
    identification_accuracy,
    run_scores
)
from ksd.features import global_stats, make_windows


ROOT = Path(__file__).parent.parent
OUT = Path(__file__).parent / "results"


def load_all() -> tuple[pd.DataFrame, pd.DataFrame]:
    # Load all dataset folders and combine their contents
    folders = [
        folder for folder in sorted(ROOT.glob("Dataset_*"))
        if folder.is_dir()
    ]

    raw_data = []

    for folder in folders:
        raw_data.append(load_raw(folder))

    raw = pd.concat(raw_data, ignore_index=True)

    # Replace participant names with anonymous IDs
    mapping = pseudonymize(raw)
    print("Pseudonyms:", mapping)

    return raw, pair_events(raw)


def explore(ks: pd.DataFrame):
    """Display basic statistics and plots before modelling."""

    print("\n== Keystrokes per participant and dataset ==")

    counts = ks.pivot_table(
        index="participant_id",
        columns="dataset",
        values="key",
        aggfunc="count",
        fill_value=0
    )

    print(counts)

    print("\n== Global measures per participant (windows of 50 keys) ==")

    stats = []

    # Calculate general timing features for each window
    for participant, group in ks.groupby("participant_id"):
        windows = make_windows(group, 50)

        for window in windows:
            row = {
                "participant_id": participant,
                **global_stats(window)
            }

            stats.append(row)

    stats = pd.DataFrame(stats)

    summary = stats.groupby("participant_id").agg(
        ["mean", "std"]
    ).round(2)

    print(summary.T)

    # Compare the distributions of hold times and digraph delays
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    for participant, group in ks.groupby("participant_id"):
        hold_times = group["hold"].clip(0, 300)
        digraph_times = group["dd"].dropna().clip(0, 800)

        axes[0].hist(
            hold_times,
            bins=60,
            alpha=0.5,
            label=participant,
            density=True
        )

        axes[1].hist(
            digraph_times,
            bins=60,
            alpha=0.5,
            label=participant,
            density=True
        )

    axes[0].set(
        title="Hold time",
        xlabel="ms"
    )

    axes[1].set(
        title="Press-press latency (DD)",
        xlabel="ms"
    )

    axes[0].legend()

    fig.tight_layout()
    fig.savefig(OUT / "distributions.png", dpi=120)
    plt.close(fig)

    print("\n== Most frequent digraphs (count per participant) ==")

    top_digraphs = ks["digraph"].value_counts().head(15).index

    digraph_stats = ks[
        ks["digraph"].isin(top_digraphs)
    ].pivot_table(
        index="digraph",
        columns="participant_id",
        values="dd",
        aggfunc=["count", "median"]
    ).round(0)

    print(digraph_stats)


def evaluate(
    ks: pd.DataFrame,
    datasets,
    window_sizes,
    distance,
    k
) -> pd.DataFrame:

    results = []

    # Evaluate each dataset with different window sizes
    for dataset in datasets:

        if dataset == "all":
            subset = ks
        else:
            subset = ks[ks.dataset == dataset]

        for window_size in window_sizes:
            windows = build_windows(subset, window_size)

            # Skip datasets without enough windows for training and testing
            if min(
                (len(user_windows) for user_windows in windows.values()),
                default=0
            ) < 4:
                continue

            scores = run_scores(
                windows,
                DISTANCES[distance],
                k=k
            )

            error_rate, threshold = eer(scores)
            accuracy = identification_accuracy(scores)
            frr = frr_at_far(scores, 0.05)

            result = {
                "dataset": dataset,
                "window": window_size,
                "n_windows": sum(
                    len(user_windows) for user_windows in windows.values()
                ),
                "EER": error_rate,
                "threshold": threshold,
                "FRR@FAR=5%": frr,
                "ident_acc": accuracy
            }

            results.append(result)

            print(
                f"  {dataset:6s} window={window_size:4d}  "
                f"EER={error_rate:.3f}  ident={accuracy:.3f}"
            )

    return pd.DataFrame(results)


def plot_results(res: pd.DataFrame, distance: str):
    fig, ax = plt.subplots(figsize=(6, 4))

    # Plot the EER for each dataset and window size
    for dataset, group in res.groupby("dataset"):
        ax.plot(
            group["window"],
            group["EER"],
            "o-",
            label=dataset
        )

    ax.set(
        xscale="log",
        xlabel="window length (keystrokes)",
        ylabel="EER",
        title=f"EER vs window length ({distance}, k-NN)"
    )

    ax.grid(alpha=0.3)
    ax.legend()

    fig.tight_layout()
    fig.savefig(OUT / f"eer_vs_window_{distance}.png", dpi=120)
    plt.close(fig)


def main():
    # Read the command-line arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset",
        default="all",
        choices=["all", "fixed", "ten", "free", "each"],
        help="'each' = evaluate every dataset separately + all"
    )

    parser.add_argument(
        "--distance",
        default="l1",
        choices=list(DISTANCES)
    )

    parser.add_argument("--k", type=int, default=3)

    parser.add_argument(
        "--windows",
        type=int,
        nargs="+",
        default=[20, 50, 100, 200, 400]
    )

    parser.add_argument("--no-explore", action="store_true")
    parser.add_argument("--export-common", action="store_true")

    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(exist_ok=True)

    raw, ks = load_all()

    print(
        f"{raw.file.nunique()} files, "
        f"{len(raw)} events, "
        f"{len(ks)} keystrokes"
    )

    # Export the data using the common CSV format if requested
    if args.export_common:
        common_dir = OUT / "common"
        common_dir.mkdir(exist_ok=True)

        for (participant, dataset), group in raw.groupby(
            ["participant_id", "dataset"]
        ):
            common_data = to_common_format(
                group,
                session_id=dataset
            )

            common_data.to_csv(
                common_dir / f"{participant}_{dataset}.csv",
                index=False
            )

    if not args.no_explore:
        explore(ks)

    # Select the datasets to evaluate
    if args.dataset == "each":
        datasets = ["fixed", "ten", "free", "all"]
    else:
        datasets = [args.dataset]

    print(
        f"\n== Verification, k-NN (k={args.k}), "
        f"distance={args.distance} =="
    )

    results = evaluate(
        ks,
        datasets,
        args.windows,
        args.distance,
        args.k
    )

    print("\n", results.round(3).to_string(index=False))

    results.to_csv(
        OUT / f"results_{args.distance}.csv",
        index=False
    )

    plot_results(results, args.distance)

    print(f"\nPlots and tables written to {OUT}")


if __name__ == "__main__":
    main()
