"""Automated safety and constraint tests for Phase 1B ingestion."""
import ast
from pathlib import Path
import pytest

from scholarship_intelligence.ingestion.safety import IngestionSafetyError, validate_url
from scholarship_intelligence.ingestion.client import PoliteHttpClient
from scholarship_intelligence.ingestion.status import FetchStatusCategory


def test_url_safety_scheme_validation():
    """Verifies that non-HTTP/HTTPS schemes are strictly rejected."""
    with pytest.raises(IngestionSafetyError, match="Unsupported URL scheme"):
        validate_url("file:///etc/passwd")

    with pytest.raises(IngestionSafetyError, match="Unsupported URL scheme"):
        validate_url("javascript:alert(1)")

    with pytest.raises(IngestionSafetyError, match="Unsupported URL scheme"):
        validate_url("ftp://ftp.example.edu/data.txt")


def test_url_safety_length_limit():
    """Verifies URLs exceeding 2048 characters are rejected."""
    oversized = "https://example.edu/" + ("a" * 2050)
    with pytest.raises(IngestionSafetyError, match="exceeds maximum length"):
        validate_url(oversized)


def test_malformed_url_safety():
    """Verifies malformed or empty URLs are caught safely."""
    with pytest.raises(IngestionSafetyError):
        validate_url("")

    with pytest.raises(IngestionSafetyError):
        validate_url("http://")


def test_no_eval_or_exec_in_ingestion_codebase():
    """AST check: verifies that eval() and exec() are never used anywhere in ingestion."""
    ingestion_dir = Path(__file__).parent.parent / "scholarship_intelligence" / "ingestion"
    
    for py_file in ingestion_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                    pytest.fail(f"Forbidden dynamic execution '{node.func.id}' found in {py_file}")
