import pandas as pd

from .data import MODIFIERS
from .detector import KNNDetector
from .distance import shared_l1
from .evaluate import build_windows, eer, run_scores
from .features import make_windows, window_profile


class Identifier:

    def __init__(self, distance=shared_l1, k=3, n_keys=50):
        self.distance = distance
        self.k = k
        self.n_keys = n_keys

    def fit(self, ks: pd.DataFrame):
        # Build the timing profiles for all participants
        windows = build_windows(ks, self.n_keys)

        # Train a separate model for each participant
        self.models = {}

        for user, user_windows in windows.items():
            if len(user_windows) > self.k:
                model = KNNDetector(self.distance, self.k)
                model.fit(user_windows)
                self.models[user] = model

        # Use the EER to determine the threshold for unknown users
        self.eer, self.threshold = eer(
            run_scores(windows, self.distance, self.k)
        )

        return self

    def sample_windows(self, ks: pd.DataFrame) -> list:

        # Remove modifier keys before splitting the sample
        text = ks[~ks["key"].isin(MODIFIERS)]

        wins = make_windows(text, self.n_keys)

        # Check if there are enough remaining keystrokes for another window
        tail_start = len(wins) * self.n_keys
        tail = text.iloc[tail_start:]

        if len(tail) > 0:
            if len(tail) >= self.n_keys // 2 or len(wins) == 0:
                wins.append(tail)

        # Convert each window into its timing profile
        profiles = []

        for window in wins:
            profiles.append(window_profile(window))

        return profiles

    def score(self, ks: pd.DataFrame) -> pd.Series:

        wins = self.sample_windows(ks)

        if not wins:
            return pd.Series(dtype=float)

        scores = {}

        # Compare each window with every participant model
        for user, model in self.models.items():
            window_scores = []

            for window in wins:
                window_scores.append(model.score(window))

            scores[user] = sum(window_scores) / len(window_scores)

        # Sort results from the closest match to the weakest match
        return pd.Series(scores).sort_values()
