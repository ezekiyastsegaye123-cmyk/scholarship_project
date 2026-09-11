"""Automated tests for HtmlExtractor DOM parsing and table extraction."""
from pathlib import Path
import pytest

from scholarship_intelligence.ingestion.extractor import HtmlExtractor

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_extract_normal_scholarship_page():
    """Verifies complete metadata, section, and prose extraction from standard page."""
    html = (FIXTURES_DIR / "normal_scholarship.html").read_text(encoding="utf-8")
    extractor = HtmlExtractor()
    page = extractor.extract(html)

    assert page.title == "Global Leaders Undergraduate Scholarship"
    assert page.canonical_url == "https://example.edu/scholarships/global-leaders"
    assert page.meta_description is not None
    assert len(page.sections) >= 3

    # Verify boilerplate removal
    all_text = " ".join(page.all_prose_snippets).lower()
    assert "cookie" not in all_text
    assert "accept cookies" not in all_text
    assert "nav" not in all_text

    # Verify headings and prose captured
    headings = [s.heading for s in page.sections]
    assert any("Award Details" in h for h in headings)
    assert any("Eligibility Requirements" in h for h in headings)
    assert any("Important Deadlines" in h for h in headings)


def test_extract_tables():
    """Verifies structured table extraction with headers and data rows."""
    html = (FIXTURES_DIR / "table_scholarship.html").read_text(encoding="utf-8")
    extractor = HtmlExtractor()
    page = extractor.extract(html)

    assert len(page.tables) == 2
    award_table = page.tables[0]
    assert "Tuition" in award_table.rows[0][0]
    assert "$30,000" in award_table.rows[0][1]

    deadline_table = page.tables[1]
    assert "Priority Scholarship Consideration" in deadline_table.rows[0][0]
    assert "December 1, 2025" in deadline_table.rows[0][1]


def test_extract_malformed_html():
    """Verifies parser resilience against unclosed tags and imperfect HTML."""
    html = (FIXTURES_DIR / "malformed_html.html").read_text(encoding="utf-8")
    extractor = HtmlExtractor()
    page = extractor.extract(html)

    assert page.title is not None
    assert len(page.all_prose_snippets) >= 2
    assert any("$15,000" in s for s in page.all_prose_snippets)
    assert len(page.tables) == 1


def test_extract_empty_sections():
    """Verifies extractor handles empty HTML documents without crashing."""
    html = (FIXTURES_DIR / "empty_sections.html").read_text(encoding="utf-8")
    extractor = HtmlExtractor()
    page = extractor.extract(html, default_title="Fallback Title")

    assert page.title in ["Blank Template Page", "Fallback Title"]
    assert len(page.sections) == 0
    assert len(page.all_prose_snippets) == 0
