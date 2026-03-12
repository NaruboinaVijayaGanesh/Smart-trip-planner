from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from flask import current_app

from app.models import Trip


FOOD_DATASET_COLUMNS = [
    "destination",
    "number_of_days",
    "number_of_people",
    "travel_mode",
    "travel_type",
    "destination_count",
    "estimated_food_cost",
    "actual_food_cost",
    "estimated_total_cost",
    "actual_total_cost",
    "source_role",
    "trip_id",
    "created_at_utc",
]


def _dataset_path() -> Path:
    configured = current_app.config.get("FOOD_DATASET_PATH")
    if configured:
        path = Path(configured)
        if not path.is_absolute():
            path = Path(current_app.root_path).parent / path
        return path
    return Path(current_app.root_path).parent / "data" / "food_cost_dataset.csv"


def _parse_destinations(raw: str) -> list[str]:
    values = [item.strip() for item in (raw or "").replace("\n", ",").split(",")]
    return [value for value in values if value]


def append_food_feedback(
    trip: Trip,
    *,
    actual_food_cost: float,
    source_role: str,
    actual_total_cost: float | None = None,
) -> Path:
    file_path = _dataset_path()
    file_path.parent.mkdir(parents=True, exist_ok=True)

    destinations = _parse_destinations(trip.destinations_raw)
    primary_destination = destinations[0] if destinations else "unknown"
    row = {
        "destination": str(primary_destination).lower(),
        "number_of_days": int(trip.number_of_days),
        "number_of_people": int(trip.number_of_people),
        "travel_mode": str(trip.travel_mode).lower(),
        "travel_type": str(trip.travel_type).lower(),
        "destination_count": max(1, len(destinations)),
        "estimated_food_cost": float(trip.food_cost or 0),
        "actual_food_cost": float(actual_food_cost),
        "estimated_total_cost": float(trip.total_group_cost or 0),
        "actual_total_cost": float(actual_total_cost if actual_total_cost is not None else trip.total_group_cost or 0),
        "source_role": source_role.lower(),
        "trip_id": int(trip.id),
        "created_at_utc": datetime.utcnow().isoformat(timespec="seconds"),
    }

    file_exists = file_path.exists()
    with file_path.open("a", newline="", encoding="utf-8") as dataset_file:
        writer = csv.DictWriter(dataset_file, fieldnames=FOOD_DATASET_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    return file_path
