"""Tests for SHA-256 change detection and distinguishing content change from fact change."""
import pytest
from scholarship_intelligence.verification.content_comparator import ContentComparator


def test_content_comparator_unchanged():
    hash_val = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    res = ContentComparator.compare(hash_val, hash_val)
    assert res.content_changed is False
    assert "unchanged" in res.message


def test_content_comparator_changed_triggers_verification():
    """Content changed does NOT immediately mean facts changed; it signals verification needed."""
    hash_old = "1111111111111111111111111111111111111111111111111111111111111111"
    hash_new = "2222222222222222222222222222222222222222222222222222222222222222"
    res = ContentComparator.compare(hash_old, hash_new)
    assert res.content_changed is True
    assert "Fact-level verification required" in res.message
