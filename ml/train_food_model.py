import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from ml.food_model import FoodCostModel


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "data" / "food_cost_dataset.csv"
MODEL_PATH = BASE_DIR / "ml" / "food_cost_model.joblib"
METRICS_PATH = BASE_DIR / "ml" / "food_model_metrics.json"


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
TARGET_COLUMN = "actual_food_cost"


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.copy()
    clean["destination"] = clean["destination"].astype(str).str.lower()
    clean["travel_mode"] = clean["travel_mode"].astype(str).str.lower()
    clean["travel_type"] = clean["travel_type"].astype(str).str.lower()
    return clean


if __name__ == "__main__":
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    data = _normalize(pd.read_csv(DATASET_PATH))
    if len(data) < 25:
        raise ValueError("Need at least 25 real data rows in data/food_cost_dataset.csv to train.")

    x = data[FEATURE_COLUMNS]
    y = data[TARGET_COLUMN]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
    )

    eval_model = FoodCostModel()
    eval_model.pipeline.fit(x_train, y_train)
    y_pred = pd.Series(eval_model.pipeline.predict(x_test), index=y_test.index)

    metrics = {
        "dataset": {
            "path": str(DATASET_PATH),
            "total_rows": int(len(data)),
            "train_rows": int(len(x_train)),
            "test_rows": int(len(x_test)),
        },
        "regression": {
            "mae": float(mean_absolute_error(y_test, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "r2": float(r2_score(y_test, y_pred)),
        },
        "model_path": str(MODEL_PATH),
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    final_model = FoodCostModel().train(DATASET_PATH)
    final_model.save(MODEL_PATH)

    print(f"Food model trained and saved to: {MODEL_PATH}")
    print(f"Metrics saved to: {METRICS_PATH}")
