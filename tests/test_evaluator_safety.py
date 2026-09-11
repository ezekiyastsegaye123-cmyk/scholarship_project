"""Tests for rule safety, sandbox isolation, and code injection prevention."""
import ast
import os
from pathlib import Path
import pytest
from scholarship_intelligence.evaluator.validator import (
    RuleValidationError,
    validate_rule_expression,
)


FORBIDDEN_CALLS = {
    "eval",
    "exec",
    "compile",
    "system",
    "popen",
    "spawn",
}


def test_evaluator_codebase_has_no_dynamic_exec():
    """Inspects all Python files in scholarship_intelligence/evaluator/ for dangerous calls."""
    evaluator_dir = Path("scholarship_intelligence/evaluator")
    for py_file in evaluator_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                    pytest.fail(f"Dangerous call '{node.func.id}' found in {py_file} at line {node.lineno}")
                elif isinstance(node.func, ast.Attribute) and node.func.attr in FORBIDDEN_CALLS:
                    pytest.fail(f"Dangerous call '{node.func.attr}' found in {py_file} at line {node.lineno}")


def test_field_injection_attempts_fail():
    """Attempts to inject attribute traversal or Python code via field names."""
    injection_fields = [
        "__class__",
        "__dict__",
        "student.__class__.__mro__",
        "citizenship; import os; os.system('ls')",
        "gpa.__gt__(3.0)",
    ]
    for field in injection_fields:
        expr = {"op": "EQ", "field": field, "value": "test"}
        with pytest.raises(RuleValidationError):
            validate_rule_expression(expr)
