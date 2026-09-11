"""HTML Extractor using BeautifulSoup4.

Performs DOM parsing, boilerplate filtering (scripts, nav, footers, cookie banners),
metadata extraction, structured section grouping, and table extraction.
"""
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, Field


class ExtractedTable(BaseModel):
    """Structured table representation extracted from HTML."""
    caption: Optional[str] = None
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    section_context: Optional[str] = None


class ExtractedSection(BaseModel):
    """Logical section of a page grouped under a heading."""
    heading: str
    level: int
    paragraphs: List[str] = Field(default_factory=list)
    list_items: List[str] = Field(default_factory=list)
    tables: List[ExtractedTable] = Field(default_factory=list)


class ExtractedPage(BaseModel):
    """Complete structured extraction result from an HTML document."""
    title: Optional[str] = None
    canonical_url: Optional[str] = None
    meta_description: Optional[str] = None
    sections: List[ExtractedSection] = Field(default_factory=list)
    all_prose_snippets: List[str] = Field(default_factory=list)
    tables: List[ExtractedTable] = Field(default_factory=list)


class HtmlExtractor:
    """Extracts relevant scholarship/aid text and tables from raw HTML."""

    BOILERPLATE_TAGS = {"script", "style", "noscript", "nav", "header", "footer", "aside", "form"}

    def __init__(self):
        pass

    def extract(self, html_content: str, default_title: Optional[str] = None) -> ExtractedPage:
        """Parses HTML and extracts structured metadata, sections, prose, and tables."""
        if not html_content or not html_content.strip():
            return ExtractedPage(title=default_title)

        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Extract metadata before removing tags
        title = None
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            h1 = soup.find("h1")
            title = h1.get_text(strip=True) if h1 else None
        if not title:
            title = default_title

        canonical_url = None
        canonical_tag = soup.find("link", rel="canonical")
        if canonical_tag and canonical_tag.get("href"):
            canonical_url = str(canonical_tag.get("href")).strip()

        meta_desc = None
        desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if desc_tag and desc_tag.get("content"):
            meta_desc = str(desc_tag.get("content")).strip()

        # 2. Decompose boilerplate elements
        for tag in soup.find_all(self.BOILERPLATE_TAGS):
            tag.decompose()

        # Remove common cookie / modal banners by class or id
        for tag in soup.find_all(
            lambda t: t.name in ["div", "section"]
            and (
                any("cookie" in str(c).lower() for c in t.get("class", []))
                or "cookie" in str(t.get("id", "")).lower()
                or any("banner" in str(c).lower() for c in t.get("class", []))
                or t.get("aria-modal") == "true"
            )
        ):
            tag.decompose()

        # 3. Extract structured sections based on headings
        sections: List[ExtractedSection] = []
        all_snippets: List[str] = []
        all_tables: List[ExtractedTable] = []

        # Current section tracker
        current_section = ExtractedSection(heading="Overview", level=1)

        # Process main content elements sequentially
        body = soup.body or soup
        heading_tags = {"h1", "h2", "h3", "h4", "h5", "h6"}

        for elem in body.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "table"]):
            # Ignore elements that are descendants of other already processed container elements
            # except direct children of interest
            if not isinstance(elem, Tag):
                continue

            tag_name = elem.name.lower()

            if tag_name in heading_tags:
                heading_text = elem.get_text(strip=True)
                if heading_text:
                    if current_section.paragraphs or current_section.list_items or current_section.tables:
                        sections.append(current_section)
                    level = int(tag_name[1])
                    current_section = ExtractedSection(heading=heading_text, level=level)

            elif tag_name == "p":
                text = elem.get_text(separator=" ", strip=True)
                cleaned = re.sub(r"\s+", " ", text).strip()
                if cleaned and len(cleaned) > 10:
                    current_section.paragraphs.append(cleaned)
                    all_snippets.append(cleaned)

            elif tag_name in ["ul", "ol"]:
                for li in elem.find_all("li", recursive=False):
                    li_text = li.get_text(separator=" ", strip=True)
                    cleaned_li = re.sub(r"\s+", " ", li_text).strip()
                    if cleaned_li:
                        current_section.list_items.append(cleaned_li)
                        all_snippets.append(cleaned_li)

            elif tag_name == "table":
                table_obj = self._parse_table(elem, current_section.heading)
                if table_obj and (table_obj.headers or table_obj.rows):
                    current_section.tables.append(table_obj)
                    all_tables.append(table_obj)

        if current_section.paragraphs or current_section.list_items or current_section.tables:
            sections.append(current_section)

        return ExtractedPage(
            title=title,
            canonical_url=canonical_url,
            meta_description=meta_desc,
            sections=sections,
            all_prose_snippets=all_snippets,
            tables=all_tables,
        )

    def _parse_table(self, table_tag: Tag, section_context: str) -> Optional[ExtractedTable]:
        """Parses an HTML table element into headers and row tuples."""
        caption = None
        cap_tag = table_tag.find("caption")
        if cap_tag:
            caption = cap_tag.get_text(strip=True)

        headers: List[str] = []
        for th in table_tag.find_all("th"):
            txt = th.get_text(separator=" ", strip=True)
            if txt:
                headers.append(txt)

        rows: List[List[str]] = []
        for tr in table_tag.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue
            row_vals = [c.get_text(separator=" ", strip=True) for c in cells]
            # Avoid repeating the header row as data if it's identical
            if headers and row_vals == headers:
                continue
            if any(row_vals):
                rows.append(row_vals)

        return ExtractedTable(
            caption=caption,
            headers=headers,
            rows=rows,
            section_context=section_context,
        )
