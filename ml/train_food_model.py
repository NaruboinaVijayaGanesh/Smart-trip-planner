import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from ml.food_model import FoodCostModel


# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Paths
DATASET_PATH = BASE_DIR / "data" / "food_cost_dataset.csv"
MODEL_PATH = BASE_DIR / "ml" / "food_cost_model.joblib"
METRICS_PATH = BASE_DIR / "ml" / "food_model_metrics.json"


# Feature columns used for training
FEATURE_COLUMNS = [
    "destination",
    "number_of_days",
    "number_of_people",
    "travel_mode",
    "travel_type",
    "destination_count",
    "estimated_food_cost",
    "estimated_total_cost",
]

# Target column
TARGET_COLUMN = "actual_food_cost"


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize categorical text fields."""
    clean = df.copy()
    clean["destination"] = clean["destination"].astype(str).str.lower()
    clean["travel_mode"] = clean["travel_mode"].astype(str).str.lower()
    clean["travel_type"] = clean["travel_type"].astype(str).str.lower()
    return clean


def load_dataset():
    """Load dataset and validate it."""
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)
    df = normalize(df)

    if len(df) < 25:
        raise ValueError("Dataset must contain at least 25 rows.")

    return df


def train_and_evaluate(df: pd.DataFrame):
    """Train model and calculate evaluation metrics."""

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    model = FoodCostModel()
    model.pipeline.fit(X_train, y_train)

    predictions = pd.Series(model.pipeline.predict(X_test), index=y_test.index)

    metrics = {
        "dataset": {
            "path": str(DATASET_PATH),
            "total_rows": int(len(df)),
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
        },
        "regression": {
            "mae": float(mean_absolute_error(y_test, predictions)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, predictions))),
            "r2": float(r2_score(y_test, predictions)),
        },
        "model_path": str(MODEL_PATH),
    }

    return metrics


def save_metrics(metrics: dict):
    """Save evaluation metrics to JSON."""
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")


def train_final_model():
    """Train final model using full dataset and save it."""
    model = FoodCostModel().train(DATASET_PATH)
    model.save(MODEL_PATH)


def main():
    df = load_dataset()

    metrics = train_and_evaluate(df)
    save_metrics(metrics)

    train_final_model()

    print(f"Food model trained and saved to: {MODEL_PATH}")
    print(f"Metrics saved to: {METRICS_PATH}")


if __name__ == "__main__":
    main()
