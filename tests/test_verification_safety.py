"""Security and forbidden-scope compliance tests for Phase 1C verification layer."""
import os
import re
import pytest

FORBIDDEN_PATTERNS = [
    r"trust_score",
    r"confidence_score",
    r"verification_score",
    r"match_score",
    r"fit_score",
    r"competitiveness_score",
    r"acceptance_probability",
    r"vector",
    r"pgvector",
    r"embedding",
    r"ranking",
    r"recommendation",
    r"playwright",
    r"puppeteer",
    r"celery",
    r"redis",
    r"kafka",
    r"rabbitmq",
    r"eval\(",
    r"exec\(",
    r"os\.system\(",
    r"subprocess",
]


def test_no_forbidden_patterns_in_verification_source_code():
    verification_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "scholarship_intelligence", "verification")
    )
    for root, _, files in os.walk(verification_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                for pattern in FORBIDDEN_PATTERNS:
                    match = re.search(pattern, content, re.IGNORECASE)
                    assert match is None, f"Forbidden pattern '{pattern}' detected in {file_path}: {match.group(0) if match else ''}"
