
"""Distance functions for comparing window profiles."""

import numpy as np


def shared_l1(a, b, min_shared=3):
    # Find the features that are present in both windows
    common = a.keys() & b.keys()

    if len(common) < min_shared:
        return np.nan

    differences = []

    # Compare the values using logarithms to account for relative differences
    for feature in common:
        value_a = a[feature][0]
        value_b = b[feature][0]

        differences.append(abs(np.log(value_a) - np.log(value_b)))

    return float(np.mean(differences))


def gunetti_r(a, b, min_shared=3, prefix="DD:"):
    # Only use digraph features for this comparison
    common = sorted(
        feature for feature in a.keys() & b.keys()
        if feature.startswith(prefix)
    )

    n = len(common)

    if n < max(min_shared, 2):
        return np.nan

    # Get the values and calculate their ranking in each window
    values_a = [a[feature][0] for feature in common]
    values_b = [b[feature][0] for feature in common]

    rank_a = np.argsort(np.argsort(values_a))
    rank_b = np.argsort(np.argsort(values_b))

    # Maximum possible difference between the two rankings
    if n % 2 == 0:
        max_disorder = n * n / 2
    else:
        max_disorder = (n * n - 1) / 2

    difference = np.abs(rank_a - rank_b).sum()

    return float(difference / max_disorder)


def combined(a, b, min_shared=3):
    # Calculate both distance measures
    d1 = shared_l1(a, b, min_shared)
    d2 = gunetti_r(a, b, min_shared)

    # Ignore distances that could not be calculated
    valid = [d for d in [d1, d2] if np.isfinite(d)]

    if not valid:
        return np.nan

    return float(np.mean(valid))


# Available distance functions
DISTANCES = {
    "l1": shared_l1,
    "gunetti": gunetti_r,
    "combined": combined
}
