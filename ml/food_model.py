from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


class FoodCostModel:
    def __init__(self):
        categorical_features = ["destination", "travel_mode", "travel_type"]
        numeric_features = [
            "number_of_days",
            "number_of_people",
            "destination_count",
            "estimated_food_cost",
            "estimated_total_cost",
        ]

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
                        n_estimators=280,
                        max_depth=18,
                        min_samples_leaf=2,
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        )

    def train(self, dataset_path: str | Path):
        df = pd.read_csv(dataset_path)
        if "actual_food_cost" not in df.columns:
            raise ValueError("Dataset must contain 'actual_food_cost'.")

        if len(df) < 25:
            raise ValueError("Need at least 25 real rows to train food model.")

        normalized = df.copy()
        normalized["destination"] = normalized["destination"].astype(str).str.lower()
        normalized["travel_mode"] = normalized["travel_mode"].astype(str).str.lower()
        normalized["travel_type"] = normalized["travel_type"].astype(str).str.lower()

        x = normalized[
            [
                "destination",
                "number_of_days",
                "number_of_people",
                "travel_mode",
                "travel_type",
                "destination_count",
                "estimated_food_cost",
                "estimated_total_cost",
            ]
        ]
        y = normalized["actual_food_cost"].astype(float)
        self.pipeline.fit(x, y)
        return self

    def predict(
        self,
        *,
        destination: str,
        number_of_days: int,
        number_of_people: int,
        travel_mode: str,
        travel_type: str,
        destination_count: int,
        estimated_food_cost: float,
        estimated_total_cost: float,
    ) -> float:
        features = pd.DataFrame(
            [
                {
                    "destination": str(destination).lower(),
                    "number_of_days": int(number_of_days),
                    "number_of_people": int(number_of_people),
                    "travel_mode": str(travel_mode).lower(),
                    "travel_type": str(travel_type).lower(),
                    "destination_count": int(destination_count),
                    "estimated_food_cost": float(estimated_food_cost),
                    "estimated_total_cost": float(estimated_total_cost),
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
        model = FoodCostModel()
        model.pipeline = joblib.load(model_path)
        return model
