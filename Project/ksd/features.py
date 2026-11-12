import numpy as np
import pandas as pd

from .data import MODIFIERS


def make_windows(ks: pd.DataFrame, n_keys: int) -> list:
    # Remove modifier keys before creating the windows
    text = ks[~ks["key"].isin(MODIFIERS)]

    windows = []

    # Split the keystrokes into non-overlapping groups
    for i in range(0, len(text) - n_keys + 1, n_keys):
        window = text.iloc[i:i + n_keys]
        windows.append(window)

    return windows


def window_profile(w: pd.DataFrame, min_count=1) -> dict:
    #Extract timing features from a window.

    #H: hold time for each key
    #DD: press-to-press time between two consecutive keys


    profile = {}

    # Calculate the median hold time for each key
    grouped_keys = w.groupby("key")["hold"]

    for key, values in grouped_keys:
        if len(values) >= min_count:
            median_time = float(np.median(values))
            profile[f"H:{key}"] = (median_time, len(values))

    # Extract digraphs with valid timing values
    digraph_data = w.dropna(subset=["dd"])

    # Calculate the median DD time for each digraph
    grouped_digraphs = digraph_data.groupby("digraph")["dd"]

    for digraph, values in grouped_digraphs:
        if len(values) >= min_count:
            median_time = float(np.median(values))
            profile[f"DD:{digraph}"] = (median_time, len(values))

    return profile


def global_stats(w: pd.DataFrame) -> dict:

    # Calculate the duration of each file separately
    # Timestamps from different files should not be compared
    durations = w.groupby("file")["press"].agg(
        lambda values: values.max() - values.min()
    )

    duration_seconds = durations.sum() / 1000

    # General statistics about typing speed and timing
    stats = {
        "hold_median": w["hold"].median(),
        "dd_median": w["dd"].median(),
        "ud_median": w["ud"].median(),
        "keys_per_s": len(w) / duration_seconds if duration_seconds > 0 else np.nan,
        "backspace_rate": (w["key"] == "backspace").mean()
    }

    return stats
