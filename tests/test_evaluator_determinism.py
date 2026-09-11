from datetime import datetime, timezone
import json
import pytest
from scholarship_intelligence.evaluator.engine import EligibilityEvaluator


def test_determinism_across_100_runs():
    evaluator = EligibilityEvaluator()
    profile = {
        "citizenship_country": "ETH",
        "residence_country": "ETH",
        "intended_degree_level": "BACHELOR",
        "intended_destination_country": "US",
        "gpa": 3.75,
        "gpa_scale": 4.0,
        "sat_score": 1450,
        "interests": ["computer science", "mathematics"],
    }
    rules = [
        {
            "rule_id": "r1",
            "kind": "REQUIRED",
            "expression": {"op": "GTE", "field": "gpa", "value": 3.5, "scale": 4.0},
            "source_evidence_snippet": "Minimum GPA 3.5",
        },
        {
            "rule_id": "r2",
            "kind": "REQUIRED",
            "expression": {"op": "IN", "field": "citizenship_country", "value": ["ETH", "KEN"]},
            "source_evidence_snippet": "Citizens of Ethiopia or Kenya",
        },
        {
            "rule_id": "r3",
            "kind": "REQUIRED",
            "expression": {
                "op": "OR",
                "operands": [
                    {"op": "GTE", "field": "sat_score", "value": 1400},
                    {"op": "CONTAINS", "field": "interests", "value": "robotics"},
                ],
            },
        },
    ]

    fixed_time = datetime(2026, 11, 1, 0, 0, 0, tzinfo=timezone.utc)

    # First run
    first_result = evaluator.evaluate_rules(rules, profile, evaluated_at=fixed_time)
    first_dump = first_result.model_dump_json()

    for _ in range(100):
        run_res = evaluator.evaluate_rules(rules, profile, evaluated_at=fixed_time)
        run_dump = run_res.model_dump_json()
        assert run_dump == first_dump

