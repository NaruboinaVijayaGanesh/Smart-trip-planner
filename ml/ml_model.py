from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


class BudgetPredictionModel:
    def __init__(self):
        categorical_features = ["destination", "travel_mode"]
        numeric_features = ["number_of_days", "number_of_people"]

        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
                ("num", "passthrough", numeric_features),
            ]
        )

        self.pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "regressor",
                    RandomForestRegressor(
                        n_estimators=300,
                        max_depth=20,
                        min_samples_leaf=2,
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        )

    def train(self, dataset_path: str | Path):
        df = pd.read_csv(dataset_path)
        df["destination"] = df["destination"].astype(str).str.lower()
        df["travel_mode"] = df["travel_mode"].astype(str).str.lower()
        x = df[["destination", "number_of_days", "number_of_people", "travel_mode"]]
        y = df["estimated_cost"]
        self.pipeline.fit(x, y)
        return self

    def predict(self, destination: str, number_of_days: int, number_of_people: int, travel_mode: str) -> float:
        features = pd.DataFrame(
            [
                {
                    "destination": destination.lower(),
                    "number_of_days": number_of_days,
                    "number_of_people": number_of_people,
                    "travel_mode": travel_mode.lower(),
                }
            ]
        )
        return float(self.pipeline.predict(features)[0])

    def save(self, model_path: str | Path):
        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, model_path)

    @staticmethod
    def load(model_path: str | Path):
        model = BudgetPredictionModel()
        model.pipeline = joblib.load(model_path)
        return model
