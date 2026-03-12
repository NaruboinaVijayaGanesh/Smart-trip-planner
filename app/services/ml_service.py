from __future__ import annotations

from pathlib import Path

from flask import current_app

from ml.food_model import FoodCostModel
from ml.ml_model import BudgetPredictionModel


_cached_model = None
_cached_food_model = None


def _dataset_path() -> Path:
    return Path(current_app.root_path).parent / "data" / "budget_dataset.csv"


def _train_and_cache_model(model_path: Path):
    model = BudgetPredictionModel().train(_dataset_path())
    model.save(model_path)
    return model


def get_model():
    global _cached_model
    if _cached_model is not None:
        return _cached_model

    model_path = Path(current_app.config["MODEL_PATH"])
    if model_path.exists():
        try:
            _cached_model = BudgetPredictionModel.load(model_path)
        except Exception as exc:
            current_app.logger.warning(
                "Failed to load budget model at %s (%s). Re-training from dataset.",
                model_path,
                exc,
            )
            _cached_model = _train_and_cache_model(model_path)
    else:
        _cached_model = _train_and_cache_model(model_path)
    return _cached_model


def predict_budget(destination: str, number_of_days: int, number_of_people: int, travel_mode: str) -> float:
    model = get_model()
    return model.predict(destination, number_of_days, number_of_people, travel_mode)


def get_food_model():
    global _cached_food_model
    if _cached_food_model is not None:
        return _cached_food_model

    model_path = Path(current_app.config["FOOD_MODEL_PATH"])
    if model_path.exists():
        try:
            _cached_food_model = FoodCostModel.load(model_path)
            return _cached_food_model
        except Exception as exc:
            current_app.logger.warning("Failed to load food cost model at %s (%s).", model_path, exc)
            return None
    return None


def predict_food_cost(
    *,
    destination: str,
    number_of_days: int,
    number_of_people: int,
    travel_mode: str,
    travel_type: str,
    destination_count: int,
    estimated_food_cost: float,
    estimated_total_cost: float,
) -> float | None:
    model = get_food_model()
    if model is None:
        return None

    try:
        return model.predict(
            destination=destination,
            number_of_days=number_of_days,
            number_of_people=number_of_people,
            travel_mode=travel_mode,
            travel_type=travel_type,
            destination_count=destination_count,
            estimated_food_cost=estimated_food_cost,
            estimated_total_cost=estimated_total_cost,
        )
    except Exception as exc:
        current_app.logger.warning("Food model prediction failed (%s).", exc)
        return None
