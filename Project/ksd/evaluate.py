
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve

from .detector import KNNDetector
from .features import make_windows, window_profile


def build_windows(ks: pd.DataFrame, n_keys: int) -> dict:
    # Create window profiles for each participant, keeping their original order
    windows = {}

    for pid, group in ks.groupby("participant_id"):
        participant_windows = make_windows(group, n_keys)
        windows[pid] = [window_profile(w) for w in participant_windows]

    return windows


def run_scores(windows: dict, distance, k=3, train_frac=0.5) -> pd.DataFrame:
    # Split each participant's windows into training and testing data
    split = {}

    for user, user_windows in windows.items():
        split[user] = max(1, int(len(user_windows) * train_frac))

    # Train one detector for each participant
    models = {}

    for user, user_windows in windows.items():
        if len(user_windows) >= 2:
            train_data = user_windows[:split[user]]
            models[user] = KNNDetector(distance, k).fit(train_data)

    rows = []

    # Compare each model against genuine and impostor windows
    for owner, model in models.items():
        for user, user_windows in windows.items():

            for i, window in enumerate(user_windows):
                held_out = i >= split[user]

                # Skip windows already used to train this model
                if owner == user and not held_out:
                    continue

                score = model.score(window)
                genuine = user == owner

                rows.append((
                    owner,
                    user,
                    i,
                    held_out,
                    genuine,
                    score
                ))

    columns = [
        "model", "typist", "win",
        "held_out", "genuine", "score"
    ]

    return pd.DataFrame(rows, columns=columns)


def far_frr(scores: pd.DataFrame, threshold: float) -> tuple:
    # Separate genuine and impostor scores
    genuine_scores = scores.loc[scores.genuine, "score"]
    impostor_scores = scores.loc[~scores.genuine, "score"]

    # FAR: impostors incorrectly accepted
    # FRR: genuine users incorrectly rejected
    far = (impostor_scores <= threshold).mean()
    frr = (genuine_scores > threshold).mean()

    return float(far), float(frr)


def eer(scores: pd.DataFrame) -> tuple:
    # Prepare the labels and scores for the ROC curve
    y = scores["genuine"].to_numpy()
    values = scores["score"].to_numpy()

    # Higher values should indicate a genuine user
    values = -np.nan_to_num(values, posinf=1e9)

    far, tpr, thresholds = roc_curve(y, values)

    frr = 1 - tpr

    # Find the point where FAR and FRR are closest
    best_index = np.argmin(np.abs(far - frr))

    eer_value = (far[best_index] + frr[best_index]) / 2
    threshold = -thresholds[best_index]

    return float(eer_value), float(threshold)


def frr_at_far(scores: pd.DataFrame, target_far=0.01) -> float:
    # Sort impostor scores to find the acceptance threshold
    impostor_scores = scores.loc[~scores.genuine, "score"].to_numpy()
    impostor_scores = np.sort(impostor_scores)

    index = int(np.floor(target_far * len(impostor_scores)))

    if index < len(impostor_scores):
        threshold = impostor_scores[index] - 1e-12
    else:
        threshold = np.inf

    # Calculate the FRR using the selected threshold
    _, frr = far_frr(scores, threshold)

    return frr


def identification_accuracy(scores: pd.DataFrame) -> float:
    # Only consider held-out windows with valid scores
    valid_scores = scores[
        scores.held_out & np.isfinite(scores.score)
    ]

    # Select the model with the lowest score for each window
    best = valid_scores.loc[
        valid_scores.groupby(["typist", "win"]).score.idxmin()
    ]

    # Check how many windows were assigned to the correct participant
    accuracy = (best.model == best.typist).mean()

    return float(accuracy)
