"""
Smart Ranking Algorithm.

Turns raw hospital metrics into one comparable 0-100 "overall score" per
the spec's default weighting (quality 35% / wait time 25% / distance 20% /
satisfaction 10% / readmission performance 10%), with user-customizable
weights supported via RankingWeights.

Each sub-score is normalized to a 0-100 scale where higher is always
better, then combined by weight. Keeping the normalization here (not in
the DB) means we can improve it later without a migration.
"""
from app.models.hospital import Hospital
from app.schemas.hospital import RankingWeights

# Reasonable ceilings used to normalize raw metrics into 0-100 scores.
# These are placeholder assumptions for the prototype; a real version
# would derive them from the national distribution in the CMS dataset.
MAX_ER_WAIT_MINUTES = 120
MAX_DISTANCE_MILES = 50
MAX_READMISSION_RATE = 25.0


def _score_quality(hospital: Hospital) -> float:
    if not hospital.quality or hospital.quality.cms_overall_rating is None:
        return 50.0  # neutral default when data is missing
    return (hospital.quality.cms_overall_rating / 5.0) * 100


def _score_wait_time(hospital: Hospital) -> float:
    if not hospital.wait_time or hospital.wait_time.er_wait_minutes is None:
        return 50.0
    minutes = min(hospital.wait_time.er_wait_minutes, MAX_ER_WAIT_MINUTES)
    return max(0.0, 100 - (minutes / MAX_ER_WAIT_MINUTES) * 100)


def _score_distance(distance_miles: float | None) -> float:
    if distance_miles is None:
        return 50.0
    capped = min(distance_miles, MAX_DISTANCE_MILES)
    return max(0.0, 100 - (capped / MAX_DISTANCE_MILES) * 100)


def _score_satisfaction(hospital: Hospital) -> float:
    if not hospital.experience or hospital.experience.overall_satisfaction is None:
        return 50.0
    return hospital.experience.overall_satisfaction  # already a 0-100 percentage


def _score_readmission(hospital: Hospital) -> float:
    if not hospital.outcomes or hospital.outcomes.readmission_rate is None:
        return 50.0
    capped = min(hospital.outcomes.readmission_rate, MAX_READMISSION_RATE)
    # Lower readmission rate is better, so invert.
    return max(0.0, 100 - (capped / MAX_READMISSION_RATE) * 100)


def compute_overall_score(
    hospital: Hospital,
    weights: RankingWeights,
    distance_miles: float | None = None,
) -> float:
    """Weighted 0-100 composite score. Weights need not pre-sum to 1.0;
    we normalize by their sum so a partial weight override still works."""
    total_weight = (
        weights.quality + weights.wait_time + weights.distance
        + weights.satisfaction + weights.readmission
    )
    if total_weight <= 0:
        total_weight = 1.0

    raw = (
        weights.quality * _score_quality(hospital)
        + weights.wait_time * _score_wait_time(hospital)
        + weights.distance * _score_distance(distance_miles)
        + weights.satisfaction * _score_satisfaction(hospital)
        + weights.readmission * _score_readmission(hospital)
    )
    return round(raw / total_weight, 1)
