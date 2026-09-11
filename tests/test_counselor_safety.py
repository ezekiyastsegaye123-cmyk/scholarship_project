"""Tests for counselor module safety, sandbox isolation, and prohibition of numerical scoring."""
import ast
from pathlib import Path
import pytest
from scholarship_intelligence.schemas.counselor import CounselorAssessmentResult

FORBIDDEN_CALLS = {
    "eval",
    "exec",
    "compile",
    "system",
    "popen",
    "spawn",
}

FORBIDDEN_MODULES = {
    "openai",
    "anthropic",
    "google.generativeai",
    "langchain",
    "llama_index",
    "redis",
    "celery",
    "kafka",
}

FORBIDDEN_ATTRIBUTES = {
    "fit_score",
    "match_score",
    "competitiveness_score",
    "readiness_score",
    "confidence_score",
    "trust_score",
    "acceptance_probability",
    "scholarship_probability",
    "ranking",
}


def test_counselor_codebase_has_no_dynamic_exec_or_llm_imports():
    """Inspects all Python files in scholarship_intelligence/counselor/ for forbidden imports or calls."""
    counselor_dir = Path("scholarship_intelligence/counselor")
    for py_file in counselor_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            # Check function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                    pytest.fail(f"Dangerous call '{node.func.id}' found in {py_file} at line {node.lineno}")
                elif isinstance(node.func, ast.Attribute) and node.func.attr in FORBIDDEN_CALLS:
                    pytest.fail(f"Dangerous call '{node.func.attr}' found in {py_file} at line {node.lineno}")

            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in FORBIDDEN_MODULES:
                        pytest.fail(f"Forbidden import '{alias.name}' found in {py_file}")
            if isinstance(node, ast.ImportFrom):
                if node.module and any(forbidden in node.module for forbidden in FORBIDDEN_MODULES):
                    pytest.fail(f"Forbidden import from '{node.module}' found in {py_file}")


def test_counselor_result_schema_has_no_prohibited_scores():
    """Ensures CounselorAssessmentResult model fields contain zero numerical score constructs."""
    fields = set(CounselorAssessmentResult.model_fields.keys())
    for forbidden in FORBIDDEN_ATTRIBUTES:
        assert forbidden not in fields, f"Forbidden attribute '{forbidden}' present on CounselorAssessmentResult"
