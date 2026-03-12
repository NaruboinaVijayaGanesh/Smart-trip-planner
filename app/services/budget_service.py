import math

from app.services.ml_service import predict_budget, predict_food_cost


TRANSPORT_MULTIPLIER = {
    "bus": 450,
    "train": 750,
    "flight": 3200,
}


FOOD_BASE_DAILY_PER_PERSON = {
    "solo": 650,
    "friends": 550,
    "family": 700,
    "couple": 620,
}
FOOD_DESTINATION_BUMP = 0.04
FOOD_SHARE_BY_TYPE = {
    "solo": 0.22,
    "friends": 0.20,
    "family": 0.28,
    "couple": 0.24,
}


def _calculate_food_cost(
    primary_destination: str,
    travel_mode: str,
    travel_type: str,
    number_of_days: int,
    number_of_people: int,
    destination_count: int,
    user_budget: float,
    ml_predicted_total: float,
) -> float:
    base_daily = FOOD_BASE_DAILY_PER_PERSON.get(travel_type, 600)
    destination_factor = 1 + (max(0, destination_count - 1) * FOOD_DESTINATION_BUMP)
    base_cost = base_daily * number_of_people * number_of_days * destination_factor
    share = FOOD_SHARE_BY_TYPE.get(travel_type, 0.22)

    ml_food_cost = max(0.0, ml_predicted_total) * share * destination_factor

    # Keep food estimate aligned with available budget range.
    budget_reference_total = user_budget if user_budget > 0 else ml_predicted_total
    budget_daily_per_person = budget_reference_total / max(1, number_of_people * number_of_days)
    budget_guided_daily = max(250.0, min(1800.0, budget_daily_per_person * 0.30))
    guided_cost = budget_guided_daily * number_of_people * number_of_days

    blended_food_cost = (ml_food_cost * 0.55) + (base_cost * 0.25) + (guided_cost * 0.20)

    # If dedicated real-data food model is available, use it as primary signal.
    food_model_prediction = predict_food_cost(
        destination=primary_destination,
        number_of_days=number_of_days,
        number_of_people=number_of_people,
        travel_mode=travel_mode,
        travel_type=travel_type,
        destination_count=max(1, destination_count),
        estimated_food_cost=blended_food_cost,
        estimated_total_cost=max(0.0, ml_predicted_total),
    )
    if food_model_prediction is not None and food_model_prediction > 0:
        # Keep some heuristic stabilizer to avoid sudden jumps on small datasets.
        return (food_model_prediction * 0.80) + (blended_food_cost * 0.20)

    return blended_food_cost


def calculate_budget(
    primary_destination: str,
    number_of_days: int,
    number_of_people: int,
    travel_mode: str,
    travel_type: str,
    hotel_rate: float,
    activity_cost: float,
    destination_count: int,
    service_charge: float = 0.0,
    user_budget: float = 0.0,
) -> dict:
    travel_mode = travel_mode.lower()
    travel_type = travel_type.lower()
    rooms = max(1, math.ceil(number_of_people / 2))
    minimum_service_charge = 300.0
    effective_service_charge = max(minimum_service_charge, float(service_charge or 0.0))

    transport_cost = TRANSPORT_MULTIPLIER.get(travel_mode, 1000) * number_of_people * max(1, destination_count)
    hotel_cost = hotel_rate * number_of_days * rooms
    predicted_budget = predict_budget(primary_destination, number_of_days, number_of_people, travel_mode)
    food_cost = _calculate_food_cost(
        primary_destination=primary_destination,
        travel_mode=travel_mode,
        travel_type=travel_type,
        number_of_days=number_of_days,
        number_of_people=number_of_people,
        destination_count=max(1, destination_count),
        user_budget=user_budget,
        ml_predicted_total=predicted_budget,
    )
    min_hotel_cost = 800.0 * number_of_days * rooms
    min_food_cost = 250.0 * number_of_people * number_of_days
    hotel_cost = max(hotel_cost, min_hotel_cost)
    food_cost = max(food_cost, min_food_cost)

    calculated_core = transport_cost + hotel_cost + food_cost + activity_cost
    baseline_total = max(calculated_core, predicted_budget * 0.85) + effective_service_charge
    total_group_cost = baseline_total

    # If user entered a budget, optimize adjustable components to stay close to it.
    if user_budget > 0 and total_group_cost > user_budget:
        # Activity cost is based on planned places and is treated as fixed.
        fixed_cost = transport_cost + effective_service_charge + activity_cost
        # Keep activity cost aligned with actual planned places; only scale hotel/food.
        adjustable_total = hotel_cost + food_cost
        target_adjustable = max(0.0, user_budget - fixed_cost)

        if adjustable_total > 0 and target_adjustable < adjustable_total:
            scale = target_adjustable / adjustable_total
            hotel_cost *= scale
            food_cost *= scale

        # Guardrail: do not drop essential stay/food estimates to near-zero values.
        hotel_cost = max(hotel_cost, min_hotel_cost)
        food_cost = max(food_cost, min_food_cost)

        total_group_cost = fixed_cost + hotel_cost + food_cost

    per_person_cost = total_group_cost / max(1, number_of_people)
    within_budget = True if user_budget <= 0 else total_group_cost <= user_budget
    budget_gap = 0.0 if user_budget <= 0 else total_group_cost - user_budget

    return {
        "transport_cost": round(transport_cost, 2),
        "hotel_cost": round(hotel_cost, 2),
        "food_cost": round(food_cost, 2),
        "activity_cost": round(activity_cost, 2),
        "predicted_budget": round(predicted_budget, 2),
        "per_person_cost": round(per_person_cost, 2),
        "total_group_cost": round(total_group_cost, 2),
        "service_charge": round(effective_service_charge, 2),
        "within_budget": within_budget,
        "budget_gap": round(budget_gap, 2),
    }
