"""Tests for canonical student profile models."""
import pytest
from pydantic import ValidationError

from scholarship_intelligence.schemas.student_profile import StudentProfileCreate


def test_valid_student_profile():
    """Validates creation of a complete, compliant international student profile."""
    profile = StudentProfileCreate(
        citizenship_country="GH",
        residence_country="GH",
        intended_degree_level="BACHELOR",
        intended_destination_country="US",
        gpa=3.85,
        gpa_scale=4.0,
        intended_major="Computer Science",
        english_test_type="TOEFL",
        english_test_score=105.0,
        sat_score=1450,
        financial_need_tier="HIGH",
        academic_achievements=["National Science Olympiad Silver Medalist"],
        extracurricular_activities=["Robotics Club President", "Community Math Tutor"],
        interests=["Artificial Intelligence", "Renewable Energy"],
    )
    assert profile.citizenship_country == "GH"
    assert profile.intended_degree_level == "BACHELOR"
    assert profile.gpa == 3.85
    assert profile.sat_score == 1450
    assert profile.financial_need_tier == "HIGH"


def test_invalid_gpa_range():
    """Rejects out-of-range GPA inputs."""
    with pytest.raises(ValidationError):
        StudentProfileCreate(
            citizenship_country="GH",
            residence_country="GH",
            gpa=105.0,  # exceeds maximum allowed 100.0
        )

    with pytest.raises(ValidationError):
        StudentProfileCreate(
            citizenship_country="GH",
            residence_country="GH",
            gpa=-2.0,  # negative GPA
        )


def test_missing_required_demographics():
    """Enforces citizenship and residence as required fields."""
    with pytest.raises(ValidationError):
        StudentProfileCreate(
            residence_country="GH",
            # missing citizenship_country
        )
