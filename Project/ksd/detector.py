
import numpy as np


class KNNDetector:

    def __init__(self, distance, k=3, normalize=True):
        self.distance = distance
        self.k = k
        self.normalize = normalize
        self.train = []
        self.scale = 1.0

    def _get_distance(self, x, train):
        distances = []

        # Calculate the distance to each training sample
        for sample in train:
            d = self.distance(x, sample)

            if np.isfinite(d):
                distances.append(d)

        if len(distances) == 0:
            return np.inf

        # Keep only the k closest samples
        distances.sort()
        nearest = distances[:self.k]

        return float(np.mean(nearest))

    def fit(self, train):
        self.train = train
        self.scale = 1.0

        if self.normalize and len(train) > self.k:
            distances = []

            # Calculate distances using leave-one-out
            for i in range(len(train)):
                other_samples = train[:i] + train[i + 1:]
                d = self._get_distance(train[i], other_samples)

                if np.isfinite(d):
                    distances.append(d)

            if len(distances) > 0:
                avg_distance = np.mean(distances)

                if avg_distance > 0:
                    self.scale = float(avg_distance)

        return self

    def score(self, x):
        # Normalize the distance using the training scale
        distance = self._get_distance(x, self.train)
        return distance / self.scale
