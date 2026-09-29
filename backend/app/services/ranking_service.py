"""Public ranking interface; evidence calculations are shared across all views."""
from app.services.evidence_scoring import compute_overall_score, explain_score, ranking_key
