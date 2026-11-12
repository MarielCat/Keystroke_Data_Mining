
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


# Keys that do not represent regular text input
MODIFIERS = {
    "shift", "caps_lock", "control_l", "control_r",
    "alt_l", "alt_r", "iso_next_group", "iso_level3_shift",
    "super_l", "meta_l"
}

# Keys that should not be used to create digraphs
NON_TEXT = MODIFIERS | {
    "backspace", "left", "right", "up", "down",
    "tab", "return", "escape", "delete", "home", "end"
}

# Keywords used to identify the type of dataset
KINDS = {
    "insa80": "fixed",
    "one_sentence": "fixed",
    "ten_first": "ten",
    "11-sentence": "ten",
    "50_diff": "free",
    "fifty": "free",
    "random": "free"
}


def dataset_kind(folder: str) -> str:
    folder = folder.lower()

    for keyword, kind in KINDS.items():
        if keyword in folder:
            return kind

    return "unknown"


def normalize_key(key) -> str:
    """Convert key names to a common format."""

    if not isinstance(key, str) or not key:
        return "?"

    # Treat uppercase and lowercase versions as the same physical key
    if key.startswith("Shift"):
        return "shift"

    return key.lower()


def fold_name(name: str) -> str:
    # Remove accents and convert names to lowercase
    name = name.strip()

    normalized = unicodedata.normalize("NFKD", name)
    name = normalized.encode("ascii", "ignore").decode()

    return name.lower()


def load_raw(root: str | Path) -> pd.DataFrame:
    """Load all keystroke CSV files found inside the dataset folder."""

    frames = []

    # Search for all files matching the expected name
    for path in sorted(Path(root).rglob("keystrokes_*.csv")):
        df = pd.read_csv(
            path,
            encoding="utf-8-sig",
            dtype={"key": str, "char": str},
            keep_default_na=False
        )

        if df.empty:
            continue

        # Add information about the dataset and source file
        df["dataset"] = dataset_kind(path.parent.name)
        df["file"] = str(path.relative_to(root))

        frames.append(df)

    raw = pd.concat(frames, ignore_index=True)

    # Keep the original name and create a normalized participant ID
    raw["name"] = raw["participant_id"].str.strip()
    raw["participant_id"] = raw["name"].map(fold_name)

    # Convert timestamps from nanoseconds to milliseconds
    raw["t_ms"] = raw["perf_time_ns"].astype("int64") / 1e6

    return raw


def pseudonymize(raw: pd.DataFrame) -> dict:
    """Replace participant names with anonymous IDs."""

    # Assign IDs in alphabetical order
    names = sorted(raw["participant_id"].unique())

    mapping = {}

    for i, name in enumerate(names):
        mapping[name] = f"P{i + 1:02d}"

    raw["participant_id"] = raw["participant_id"].map(mapping)

    return mapping


def pair_events(raw: pd.DataFrame) -> pd.DataFrame:
    """Match keydown and keyup events to obtain complete keystrokes."""

    rows = []

    # Process each file separately to avoid mixing events
    for file, events in raw.groupby("file", sort=False):
        events = events.sort_values("event_index")

        pid = events["participant_id"].iat[0]
        kind = events["dataset"].iat[0]
        start_unix = events["unix_time_ns"].iat[0]

        # Store keys that are currently pressed
        down = {}

        for typ, key, char, time in zip(
            events["event_type"],
            events["key"],
            events["char"],
            events["t_ms"]
        ):
            normalized_key = normalize_key(key)

            if typ == "keydown":
                # Ignore repeated keydown events
                if normalized_key not in down:
                    down[normalized_key] = (time, key, char)

            elif typ == "keyup" and normalized_key in down:
                press_time, raw_key, raw_char = down.pop(normalized_key)

                rows.append((
                    pid, kind, file, start_unix,
                    normalized_key, raw_key, raw_char,
                    press_time, time
                ))

    columns = [
        "participant_id", "dataset", "file", "file_start",
        "key", "raw_key", "char", "press", "release"
    ]

    ks = pd.DataFrame(rows, columns=columns)

    # Calculate how long each key was held
    ks["hold"] = ks["release"] - ks["press"]

    # Keep keystrokes in chronological order
    ks = ks.sort_values(
        ["participant_id", "file_start", "press"]
    ).reset_index(drop=True)

    return add_digraphs(ks)


def add_digraphs(ks: pd.DataFrame, max_latency_ms=1500.0) -> pd.DataFrame:
    """Calculate timing information between consecutive text keys."""

    ks = ks.copy()

    ks["digraph"] = None
    ks["dd"] = np.nan
    ks["ud"] = np.nan

    # Remove modifiers before looking for consecutive text keys
    text = ks[~ks["key"].isin(MODIFIERS)]

    # Digraphs are calculated separately for each file
    for _, group in text.groupby("file", sort=False):
        indexes = group.index.to_numpy()

        keys = group["key"].to_numpy()
        press_times = group["press"].to_numpy()
        release_times = group["release"].to_numpy()

        for i in range(len(indexes) - 1):
            key_a = keys[i]
            key_b = keys[i + 1]

            # Skip navigation and correction keys
            if key_a in NON_TEXT or key_b in NON_TEXT:
                continue

            # Time between the two key presses
            dd = press_times[i + 1] - press_times[i]

            # Ignore long pauses between keystrokes
            if dd > max_latency_ms:
                continue

            ks.at[indexes[i], "digraph"] = f"{key_a}>{key_b}"
            ks.at[indexes[i], "dd"] = dd

            # Time between releasing the first key and pressing the next
            ks.at[indexes[i], "ud"] = (
                press_times[i + 1] - release_times[i]
            )

    return ks


def events_to_keystrokes(events: list[tuple]) -> pd.DataFrame:
    """Convert live keyboard events using the same processing as CSV data."""

    columns = ["event_type", "key", "char", "perf_time_ns"]
    raw = pd.DataFrame(events, columns=columns)

    raw["event_index"] = range(len(raw))
    raw["t_ms"] = raw["perf_time_ns"] / 1e6

    # Add the required metadata for live events
    raw["participant_id"] = "?"
    raw["dataset"] = "live"
    raw["file"] = "live"
    raw["unix_time_ns"] = 0

    return pair_events(raw)


def to_common_format(raw: pd.DataFrame, session_id="S1") -> pd.DataFrame:
    """Convert events to the common keystroke format."""

    out = []

    # Each original file represents one sample
    for sample_id, (file, events) in enumerate(
        raw.groupby("file", sort=False)
    ):
        events = events.sort_values("event_index")

        down = {}
        next_id = 0

        for _, event in events.iterrows():
            key = normalize_key(event["key"])

            if event["event_type"] == "keydown":

                # Ignore auto-repeat events
                if key in down:
                    continue

                down[key] = next_id
                press_id = next_id
                next_id += 1

            else:
                # Ignore releases without a previous press
                if key not in down:
                    continue

                press_id = down.pop(key)

            event_type = (
                "down" if event["event_type"] == "keydown" else "up"
            )

            out.append((
                event["participant_id"],
                session_id,
                sample_id,
                event_type,
                event["key"],
                round(event["t_ms"], 3),
                press_id,
                event["char"]
            ))

    columns = [
        "participant_id", "session_id", "sample_id", "event",
        "key_code", "timestamp_ms", "press_id", "key"
    ]

    return pd.DataFrame(out, columns=columns)
