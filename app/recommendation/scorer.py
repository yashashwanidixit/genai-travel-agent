from typing import Dict, List


class WeightedScorer:
    """Calculates weighted multi-objective scores for options."""

    DEFAULT_HOTEL_WEIGHTS = {
        "rating": 0.30,
        "review_count": 0.10,
        "star_match": 0.15,
        "amenity_score": 0.20,
        "budget_score": 0.25,
    }

    DEFAULT_RIDE_WEIGHTS = {
        "fare": 0.40,
        "eta_pickup": 0.25,
        "duration": 0.15,
        "type_match": 0.20,
    }

    @staticmethod
    def calculate_score(features: Dict[str, float], weights: Dict[str, float]) -> float:
        total_weight = sum(weights.values())
        score = sum(features.get(k, 0.0) * w for k, w in weights.items())
        return round(score / total_weight, 4) if total_weight > 0 else 0.0
