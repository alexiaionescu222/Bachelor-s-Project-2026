import json
import warnings
warnings.filterwarnings("ignore")

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
import joblib

from features import extract_feature_matrix


def load_dataset(path: str) -> tuple[np.ndarray, np.ndarray]:
    with open(path) as f:
        samples = json.load(f)
    X = extract_feature_matrix(samples)
    y = np.array([s["label"] for s in samples])
    return X, y


def make_model() -> Pipeline:
    return Pipeline([
        ("clf", RandomForestClassifier(
            n_estimators = 300,
            max_depth    = None,
            class_weight = "balanced",
            random_state = 42,
            n_jobs       = 1,
        )),
    ])


def main():
    X, y = load_dataset("dataset.json")
    model = make_model()
    model.fit(X, y)
    joblib.dump(model, "error_classifier.pkl")


if __name__ == "__main__":
    main()