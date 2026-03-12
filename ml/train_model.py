import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

from ml.ml_model import BudgetPredictionModel


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "data" / "budget_dataset.csv"
MODEL_PATH = BASE_DIR / "ml" / "budget_model.joblib"
METRICS_PATH = BASE_DIR / "ml" / "model_metrics.json"
CONFUSION_MATRIX_PATH = BASE_DIR / "ml" / "confusion_matrix.csv"
CLASSIFICATION_REPORT_PATH = BASE_DIR / "ml" / "classification_report.csv"

FEATURE_COLS = ["destination", "number_of_days", "number_of_people", "travel_mode"]
TARGET_COL = "estimated_cost"
TIER_LABELS = ["cheap", "moderate", "luxury"]


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["destination"] = df["destination"].astype(str).str.lower()
    df["travel_mode"] = df["travel_mode"].astype(str).str.lower()
    return df


def _to_tier(values: pd.Series, q1: float, q2: float) -> pd.Series:
    return pd.cut(
        values,
        bins=[-np.inf, q1, q2, np.inf],
        labels=TIER_LABELS,
        include_lowest=True,
    )


if __name__ == "__main__":
    df = _normalize(pd.read_csv(DATASET_PATH))
    x = df[FEATURE_COLS]
    y = df[TARGET_COL]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
    )

    eval_model = BudgetPredictionModel()
    eval_model.pipeline.fit(x_train, y_train)
    y_pred = pd.Series(eval_model.pipeline.predict(x_test), index=y_test.index)

    low_threshold = float(y_train.quantile(0.33))
    high_threshold = float(y_train.quantile(0.66))

    y_test_tier = _to_tier(y_test, low_threshold, high_threshold)
    y_pred_tier = _to_tier(y_pred, low_threshold, high_threshold)

    accuracy = accuracy_score(y_test_tier, y_pred_tier)
    precision = precision_score(y_test_tier, y_pred_tier, average="weighted", zero_division=0)
    recall = recall_score(y_test_tier, y_pred_tier, average="weighted", zero_division=0)
    f1 = f1_score(y_test_tier, y_pred_tier, average="weighted", zero_division=0)

    confusion = confusion_matrix(y_test_tier, y_pred_tier, labels=TIER_LABELS)
    confusion_df = pd.DataFrame(confusion, index=TIER_LABELS, columns=TIER_LABELS)
    confusion_df.to_csv(CONFUSION_MATRIX_PATH)

    cls_report = classification_report(
        y_test_tier,
        y_pred_tier,
        labels=TIER_LABELS,
        output_dict=True,
        zero_division=0,
    )
    pd.DataFrame(cls_report).transpose().to_csv(CLASSIFICATION_REPORT_PATH)

    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    metrics = {
        "dataset": {
            "path": str(DATASET_PATH),
            "total_rows": int(len(df)),
            "train_rows": int(len(x_train)),
            "test_rows": int(len(x_test)),
        },
        "tier_thresholds": {
            "cheap_max": low_threshold,
            "moderate_max": high_threshold,
        },
        "classification": {
            "accuracy": float(accuracy),
            "precision_weighted": float(precision),
            "recall_weighted": float(recall),
            "f1_weighted": float(f1),
        },
        "regression": {
            "mae": float(mean_absolute_error(y_test, y_pred)),
            "rmse": rmse,
            "r2": float(r2_score(y_test, y_pred)),
        },
        "artifacts": {
            "confusion_matrix_csv": str(CONFUSION_MATRIX_PATH),
            "classification_report_csv": str(CLASSIFICATION_REPORT_PATH),
            "model_path": str(MODEL_PATH),
        },
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # Train final model on complete dataset for production inference.
    final_model = BudgetPredictionModel().train(DATASET_PATH)
    final_model.save(MODEL_PATH)

    print(f"Model trained and saved to: {MODEL_PATH}")
    print(f"Metrics saved to: {METRICS_PATH}")
    print(f"Confusion matrix saved to: {CONFUSION_MATRIX_PATH}")
