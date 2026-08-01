"""
Unit tests for the ranking algorithm — the piece of business logic most
worth pinning down with tests, since it directly drives what users see
as the "best" hospital.
"""
from app.models.hospital import Hospital, HospitalQuality, HospitalOutcomes, PatientExperience, WaitTimeEstimate
from app.schemas.hospital import RankingWeights
from app.services.ranking_service import compute_overall_score


def _make_hospital(rating=4, er_wait=30, satisfaction=80.0, readmission=15.0):
    h = Hospital(name="Test Hospital")
    h.quality = HospitalQuality(cms_overall_rating=rating)
    h.outcomes = HospitalOutcomes(readmission_rate=readmission)
    h.experience = PatientExperience(overall_satisfaction=satisfaction)
    h.wait_time = WaitTimeEstimate(er_wait_minutes=er_wait)
    return h


def test_higher_quality_rating_increases_score():
    weights = RankingWeights()
    low = compute_overall_score(_make_hospital(rating=2), weights, distance_miles=10)
    high = compute_overall_score(_make_hospital(rating=5), weights, distance_miles=10)
    assert high > low


def test_shorter_wait_time_increases_score():
    weights = RankingWeights()
    slow = compute_overall_score(_make_hospital(er_wait=110), weights, distance_miles=10)
    fast = compute_overall_score(_make_hospital(er_wait=10), weights, distance_miles=10)
    assert fast > slow


def test_score_missing_data_defaults_neutral():
    h = Hospital(name="No Data Hospital")
    weights = RankingWeights()
    score = compute_overall_score(h, weights, distance_miles=None)
    assert 0 <= score <= 100


def test_custom_weights_change_ranking_order():
    # Hospital A: great quality, terrible wait time
    a = _make_hospital(rating=5, er_wait=115)
    # Hospital B: mediocre quality, great wait time
    b = _make_hospital(rating=3, er_wait=5)

    quality_focused = RankingWeights(quality=0.9, wait_time=0.1, distance=0, satisfaction=0, readmission=0)
    wait_focused = RankingWeights(quality=0.1, wait_time=0.9, distance=0, satisfaction=0, readmission=0)

    a_quality_score = compute_overall_score(a, quality_focused, None)
    b_quality_score = compute_overall_score(b, quality_focused, None)
    assert a_quality_score > b_quality_score

    a_wait_score = compute_overall_score(a, wait_focused, None)
    b_wait_score = compute_overall_score(b, wait_focused, None)
    assert b_wait_score > a_wait_score
