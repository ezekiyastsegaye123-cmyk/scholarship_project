"""Candidate Normalization Engine.

Transforms extracted HTML page structures into structured CandidateOpportunity models
with strict evidence preservation and tri-state uncertainty representation.
"""
import re
from datetime import date, datetime, timezone
from typing import Any, List, Optional, Tuple

from scholarship_intelligence.domain.enums import (
    AmountPeriod,
    AuthorityTier,
    DeadlineType,
    FundingClassification,
    FundingComponentType,
    RequirementType,
    RuleKind,
    TriState,
)
from scholarship_intelligence.ingestion.extractor import ExtractedPage, ExtractedTable
from scholarship_intelligence.ingestion.status import FetchResult
from scholarship_intelligence.schemas.candidate import (
    CandidateAward,
    CandidateDeadline,
    CandidateEvidence,
    CandidateFundingComponent,
    CandidateOpportunity,
    CandidateRequirement,
)


class CandidateNormalizer:
    """Normalizes extracted page content into candidate models with attached evidence."""

    MONTHS = {
        "january": 1, "jan": 1,
        "february": 2, "feb": 2,
        "march": 3, "mar": 3,
        "april": 4, "apr": 4,
        "may": 5,
        "june": 6, "jun": 6,
        "july": 7, "jul": 7,
        "august": 8, "aug": 8,
        "september": 9, "sep": 9, "sept": 9,
        "october": 10, "oct": 10,
        "november": 11, "nov": 11,
        "december": 12, "dec": 12,
    }

    def __init__(self):
        pass

    def _create_evidence(
        self,
        snippet: str,
        fetch_result: FetchResult,
        context: Optional[str] = None,
        authority_tier: AuthorityTier = AuthorityTier.THIRD_PARTY,
    ) -> CandidateEvidence:
        """Constructs an immutable CandidateEvidence anchor for a fact."""
        # Clean snippet to ensure conciseness
        cleaned = re.sub(r"\s+", " ", snippet).strip()
        if len(cleaned) > 280:
            cleaned = cleaned[:277] + "..."

        return CandidateEvidence(
            source_url=fetch_result.url,
            retrieved_at=fetch_result.retrieved_at,
            http_status=fetch_result.http_status or 200,
            content_sha256=fetch_result.content_sha256 or "unknown_hash",
            evidence_text=cleaned,
            evidence_context=context,
            authority_tier=authority_tier,
        )

    def normalize(
        self,
        extracted: ExtractedPage,
        fetch_result: FetchResult,
        authority_tier: AuthorityTier = AuthorityTier.THIRD_PARTY,
        academic_cycle: str = "2026-2027",
    ) -> CandidateOpportunity:
        """Transforms ExtractedPage into CandidateOpportunity with candidate sub-entities."""
        title = extracted.title or "Candidate Scholarship Opportunity"

        # Evidence accumulation
        all_evidence: List[CandidateEvidence] = []
        deadlines: List[CandidateDeadline] = []
        requirements: List[CandidateRequirement] = []
        funding_components: List[CandidateFundingComponent] = []

        intl_allowed = TriState.UNKNOWN
        requires_sat = TriState.UNKNOWN
        requires_act = TriState.UNKNOWN
        requires_css = TriState.UNKNOWN
        need_required = TriState.UNKNOWN

        # 1. Parse tables for structured funding or deadlines
        for table in extracted.tables:
            self._process_table(
                table, fetch_result, authority_tier, funding_components, deadlines, all_evidence
            )

        # 2. Parse prose snippets and section items
        for snippet in extracted.all_prose_snippets:
            lower = snippet.lower()

            # International student eligibility check
            if intl_allowed == TriState.UNKNOWN:
                if any(k in lower for k in ["international students are eligible", "open to international students", "all citizens eligible"]):
                    intl_allowed = TriState.YES
                    all_evidence.append(self._create_evidence(snippet, fetch_result, "International Eligibility", authority_tier))
                elif any(k in lower for k in ["us citizens only", "permanent residents only", "international students are not eligible"]):
                    intl_allowed = TriState.NO
                    all_evidence.append(self._create_evidence(snippet, fetch_result, "International Eligibility", authority_tier))

            # SAT / ACT requirements
            if requires_sat == TriState.UNKNOWN:
                if "sat is required" in lower or "requires the sat" in lower:
                    requires_sat = TriState.YES
                    all_evidence.append(self._create_evidence(snippet, fetch_result, "Standardized Testing", authority_tier))
                elif "test-optional" in lower or "sat not required" in lower or "sat is not required" in lower or "does not require sat" in lower:
                    requires_sat = TriState.NO
                    all_evidence.append(self._create_evidence(snippet, fetch_result, "Standardized Testing", authority_tier))

            if requires_act == TriState.UNKNOWN:
                if "act is required" in lower or "requires the act" in lower:
                    requires_act = TriState.YES
                    all_evidence.append(self._create_evidence(snippet, fetch_result, "Standardized Testing", authority_tier))
                elif "test-optional" in lower or "act not required" in lower or "act is not required" in lower or "does not require act" in lower:
                    requires_act = TriState.NO
                    all_evidence.append(self._create_evidence(snippet, fetch_result, "Standardized Testing", authority_tier))

            # CSS Profile / Financial Need
            if requires_css == TriState.UNKNOWN:
                if "css profile" in lower:
                    if "required" in lower or "must submit" in lower:
                        requires_css = TriState.YES
                        all_evidence.append(self._create_evidence(snippet, fetch_result, "Financial Aid Application", authority_tier))
                    elif "not required" in lower:
                        requires_css = TriState.NO
                        all_evidence.append(self._create_evidence(snippet, fetch_result, "Financial Aid Application", authority_tier))

            if need_required == TriState.UNKNOWN:
                if "need-based" in lower or "demonstrated financial need" in lower:
                    need_required = TriState.YES
                    all_evidence.append(self._create_evidence(snippet, fetch_result, "Financial Need", authority_tier))
                elif "merit-based only" in lower or "without regard to financial need" in lower:
                    need_required = TriState.NO
                    all_evidence.append(self._create_evidence(snippet, fetch_result, "Financial Need", authority_tier))

            # GPA Requirement extraction
            gpa_match = re.search(r"\b(?:minimum\s+)?gpa\s+(?:of\s+)?(?:at\s+least\s+)?([234]\.\d{1,2})\b", snippet, re.I)
            if gpa_match:
                val = float(gpa_match.group(1))
                ev = self._create_evidence(snippet, fetch_result, "Academic GPA Requirement", authority_tier)
                requirements.append(
                    CandidateRequirement(
                        requirement_type=RequirementType.TRANSCRIPT,
                        kind=RuleKind.REQUIRED,
                        name="Minimum GPA",
                        raw_text=snippet,
                        field_name="gpa",
                        operator="GTE",
                        target_value=val,
                        evidence=ev,
                    )
                )
                all_evidence.append(ev)

            # Deadline extraction from prose
            self._extract_deadlines_from_prose(
                snippet, fetch_result, authority_tier, deadlines, all_evidence, academic_cycle
            )

            # Funding amounts from prose if not already populated from tables
            self._extract_funding_from_prose(
                snippet, fetch_result, authority_tier, funding_components, all_evidence
            )

        # Build CandidateAward if funding was extracted or described
        award = self._build_candidate_award(
            title, extracted, fetch_result, authority_tier, funding_components, need_required
        )

        # Fallback evidence anchor from document title or description if specific sub-facts lacked evidence
        if not all_evidence:
            if extracted.title:
                all_evidence.append(
                    self._create_evidence(
                        f"Opportunity title: {title}",
                        fetch_result,
                        "Document Heading/Title",
                        authority_tier,
                    )
                )
            elif extracted.meta_description:
                all_evidence.append(
                    self._create_evidence(
                        extracted.meta_description,
                        fetch_result,
                        "Meta Description",
                        authority_tier,
                    )
                )

        if not all_evidence:
            # Without any supporting evidence, candidate staging is prohibited
            return None

        return CandidateOpportunity(
            title=title,
            description=extracted.meta_description,
            academic_cycle=academic_cycle,
            target_degree_level="BACHELOR",
            destination_country="US",
            international_students_allowed=intl_allowed,
            requires_sat=requires_sat,
            requires_act=requires_act,
            requires_css_profile=requires_css,
            financial_need_required=need_required,
            award=award,
            deadlines=deadlines,
            requirements=requirements,
            source_evidence=all_evidence,
            extraction_status="EXTRACTED",
            extracted_at=datetime.now(timezone.utc),
        )

    def _process_table(
        self,
        table: ExtractedTable,
        fetch_result: FetchResult,
        authority_tier: AuthorityTier,
        components: List[CandidateFundingComponent],
        deadlines: List[CandidateDeadline],
        all_evidence: List[CandidateEvidence],
    ) -> None:
        """Extracts candidate funding or deadlines from HTML table structures."""
        headers_lower = [h.lower() for h in table.headers]

        # 1. Check if it is a funding / award table
        is_award_table = any(k in h for h in headers_lower for k in ["amount", "award", "component", "tuition", "cost", "coverage"])
        if is_award_table:
            for row in table.rows:
                row_str = " | ".join(row)
                ev = self._create_evidence(
                    f"Table row: {row_str}",
                    fetch_result,
                    f"Table in section '{table.section_context or 'Unknown'}'",
                    authority_tier,
                )
                # Parse amount from cells
                parsed_amount = self._parse_currency_amount(row_str)
                comp_type = self._determine_component_type(row_str)
                period = self._determine_period(row_str)

                if parsed_amount or comp_type:
                    min_amt, max_amt = parsed_amount if parsed_amount else (None, None)
                    comp = CandidateFundingComponent(
                        component_type=comp_type or FundingComponentType.OTHER,
                        amount_min=min_amt,
                        amount_max=max_amt,
                        currency="USD",
                        amount_period=period,
                        description=row_str,
                        evidence=ev,
                    )
                    components.append(comp)
                    all_evidence.append(ev)

        # 2. Check if it is a deadline table
        is_deadline_table = any(k in h for h in headers_lower for k in ["deadline", "date", "round", "decision"])
        if is_deadline_table:
            for row in table.rows:
                row_str = " | ".join(row)
                ev = self._create_evidence(
                    f"Deadline table row: {row_str}",
                    fetch_result,
                    f"Table in section '{table.section_context or 'Unknown'}'",
                    authority_tier,
                )
                dl_type = self._determine_deadline_type(row_str)
                parsed_date, is_exact = self._parse_date_string(row_str)

                dl = CandidateDeadline(
                    deadline_type=dl_type,
                    raw_date_text=row_str,
                    deadline_date=parsed_date,
                    is_exact_date=is_exact,
                    evidence=ev,
                )
                deadlines.append(dl)
                all_evidence.append(ev)

    def _extract_deadlines_from_prose(
        self,
        snippet: str,
        fetch_result: FetchResult,
        authority_tier: AuthorityTier,
        deadlines: List[CandidateDeadline],
        all_evidence: List[CandidateEvidence],
        academic_cycle: str,
    ) -> None:
        """Identifies dates and deadline statements in prose snippets."""
        lower = snippet.lower()
        if not any(k in lower for k in ["deadline", "due date", "apply by", "application by", "priority date"]):
            return

        dl_type = self._determine_deadline_type(snippet)

        # Check for explicit "deadline varies"
        if "deadline varies" in lower or "varies by program" in lower:
            ev = self._create_evidence(snippet, fetch_result, "Deadline Policy", authority_tier)
            dl = CandidateDeadline(
                deadline_type=dl_type,
                raw_date_text="Deadline varies",
                deadline_date=None,
                is_exact_date=False,
                varies_by_program=True,
                academic_cycle=academic_cycle,
                evidence=ev,
            )
            deadlines.append(dl)
            all_evidence.append(ev)
            return

        parsed_date, is_exact = self._parse_date_string(snippet)
        if parsed_date or is_exact:
            ev = self._create_evidence(snippet, fetch_result, f"Deadline: {dl_type.value}", authority_tier)
            dl = CandidateDeadline(
                deadline_type=dl_type,
                raw_date_text=snippet,
                deadline_date=parsed_date,
                is_exact_date=is_exact,
                academic_cycle=academic_cycle,
                evidence=ev,
            )
            deadlines.append(dl)
            all_evidence.append(ev)

    def _extract_funding_from_prose(
        self,
        snippet: str,
        fetch_result: FetchResult,
        authority_tier: AuthorityTier,
        components: List[CandidateFundingComponent],
        all_evidence: List[CandidateEvidence],
    ) -> None:
        """Extracts funding amounts and components from prose snippets."""
        lower = snippet.lower()
        if not any(k in lower for k in ["$", "dollar", "tuition", "award", "stipend", "grant", "scholarship"]):
            return

        # Check if already parsed
        amounts = self._parse_currency_amount(snippet)
        if amounts:
            min_amt, max_amt = amounts
            comp_type = self._determine_component_type(snippet)
            period = self._determine_period(snippet)
            ev = self._create_evidence(snippet, fetch_result, "Award Funding Prose", authority_tier)
            comp = CandidateFundingComponent(
                component_type=comp_type or FundingComponentType.TUITION,
                amount_min=min_amt,
                amount_max=max_amt,
                currency="USD",
                amount_period=period,
                description=snippet,
                evidence=ev,
            )
            components.append(comp)
            all_evidence.append(ev)

    def _build_candidate_award(
        self,
        title: str,
        extracted: ExtractedPage,
        fetch_result: FetchResult,
        authority_tier: AuthorityTier,
        components: List[CandidateFundingComponent],
        need_required: TriState,
    ) -> Optional[CandidateAward]:
        """Constructs CandidateAward based strictly on extracted components and prose."""
        page_text = " ".join(extracted.all_prose_snippets).lower()

        # Determine classification
        classification = FundingClassification.PARTIAL_FUNDING
        if "full ride" in page_text or ("full tuition" in page_text and any(k in page_text for k in ["room", "living expense", "stipend"])):
            classification = FundingClassification.FULL_FUNDING
        elif "full tuition" in page_text or "100% of tuition" in page_text:
            classification = FundingClassification.FULL_TUITION
        elif need_required == TriState.YES or "demonstrated need" in page_text:
            classification = FundingClassification.FULL_FUNDING
        elif components and all(c.component_type == FundingComponentType.STIPEND for c in components):
            classification = FundingClassification.STIPEND_ONLY

        # Evidence anchor for award
        award_evidence_snippet = None
        for s in extracted.all_prose_snippets:
            if any(k in s.lower() for k in ["award", "tuition", "scholarship covers", "full ride", "full tuition", "$"]):
                award_evidence_snippet = s
                break

        if not award_evidence_snippet:
            if components:
                award_evidence_snippet = components[0].evidence.evidence_text
            else:
                return None

        ev = self._create_evidence(award_evidence_snippet, fetch_result, "Award Overview", authority_tier)

        # Renewable check
        is_renewable = TriState.UNKNOWN
        if "renewable for" in page_text or "renewable up to four years" in page_text or "each year" in page_text:
            is_renewable = TriState.YES
        elif "one-time award" in page_text or "non-renewable" in page_text:
            is_renewable = TriState.NO

        return CandidateAward(
            funding_classification=classification,
            title=f"{title} Award",
            is_renewable=is_renewable,
            components=components,
            evidence=ev,
        )

    def _parse_currency_amount(self, text: str) -> Optional[Tuple[float, float]]:
        """Parses dollar amount or range e.g. '$20,000' or '$15,000 - $25,000'."""
        # Check range pattern: $X,XXX - $Y,YYY
        range_match = re.search(
            r"\$\s*([0-9]{1,3}(?:,[0-9]{3})+|\d+)\s*(?:-|to)\s*\$\s*([0-9]{1,3}(?:,[0-9]{3})+|\d+)",
            text,
            re.I,
        )
        if range_match:
            min_val = float(range_match.group(1).replace(",", ""))
            max_val = float(range_match.group(2).replace(",", ""))
            return (min_val, max_val)

        # Single amount: $X,XXX
        single_match = re.search(r"\$\s*([0-9]{1,3}(?:,[0-9]{3})+|\d+)", text)
        if single_match:
            val = float(single_match.group(1).replace(",", ""))
            return (val, val)

        return None

    def _determine_component_type(self, text: str) -> Optional[FundingComponentType]:
        """Classifies funding component type from text snippet."""
        lower = text.lower()
        if "tuition" in lower:
            return FundingComponentType.TUITION
        elif "room" in lower or "housing" in lower:
            return FundingComponentType.ROOM
        elif "board" in lower or "meal" in lower or "food" in lower:
            return FundingComponentType.MEALS
        elif "book" in lower or "supplies" in lower:
            return FundingComponentType.BOOKS
        elif "stipend" in lower or "living allowance" in lower:
            return FundingComponentType.STIPEND
        elif "insurance" in lower or "health" in lower:
            return FundingComponentType.HEALTH_INSURANCE
        elif "travel" in lower or "flight" in lower:
            return FundingComponentType.TRAVEL
        elif "fee" in lower:
            return FundingComponentType.MANDATORY_FEES
        return None

    def _determine_period(self, text: str) -> AmountPeriod:
        """Determines period: annual, total, one_time."""
        lower = text.lower()
        if "per year" in lower or "annual" in lower or "each year" in lower or "/year" in lower or "/yr" in lower:
            return AmountPeriod.ANNUAL
        elif "semester" in lower or "term" in lower:
            return AmountPeriod.ANNUAL
        elif "one-time" in lower or "single year" in lower or "one year" in lower:
            return AmountPeriod.ONE_TIME
        elif "total" in lower or "over 4 years" in lower or "four years" in lower:
            return AmountPeriod.TOTAL
        return AmountPeriod.ANNUAL

    def _determine_deadline_type(self, text: str) -> DeadlineType:
        """Classifies deadline type based on textual cues."""
        lower = text.lower()
        if "early decision" in lower or " ed " in lower:
            return DeadlineType.EARLY_DECISION
        elif "early action" in lower or " ea " in lower:
            return DeadlineType.EARLY_ACTION
        elif "regular decision" in lower or " rd " in lower:
            return DeadlineType.REGULAR_DECISION
        elif "priority" in lower:
            return DeadlineType.PRIORITY
        elif "financial aid" in lower or "css" in lower or "aid application" in lower:
            return DeadlineType.FINANCIAL_AID
        elif "scholarship" in lower:
            return DeadlineType.SCHOLARSHIP_APPLICATION
        return DeadlineType.UNIVERSITY_APPLICATION

    def _parse_date_string(self, text: str) -> Tuple[Optional[date], bool]:
        """Extracts date from text like 'November 1, 2025' or '11/01/2025' or '2026-01-15'.
        
        Returns (parsed_date, is_exact).
        """
        # ISO format: YYYY-MM-DD
        iso_match = re.search(r"\b(202[4-9])-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b", text)
        if iso_match:
            try:
                y = int(iso_match.group(1))
                m = int(iso_match.group(2))
                d = int(iso_match.group(3))
                return (date(y, m, d), True)
            except ValueError:
                pass

        # Month Day, Year e.g. November 1, 2025 or Nov 1, 2025
        month_pattern = r"\b(" + "|".join(self.MONTHS.keys()) + r")\s+([0-9]{1,2})(?:st|nd|rd|th)?(?:,)?\s+(202[4-9])\b"
        mdy_match = re.search(month_pattern, text, re.I)
        if mdy_match:
            m_str = mdy_match.group(1).lower()
            m_num = self.MONTHS.get(m_str)
            d_num = int(mdy_match.group(2))
            y_num = int(mdy_match.group(3))
            try:
                return (date(y_num, m_num, d_num), True)
            except ValueError:
                pass

        # Month Day without Year (e.g. 'November 1')
        md_pattern = r"\b(" + "|".join(self.MONTHS.keys()) + r")\s+([0-9]{1,2})(?:st|nd|rd|th)?\b"
        md_match = re.search(md_pattern, text, re.I)
        if md_match:
            m_str = md_match.group(1).lower()
            m_num = self.MONTHS.get(m_str)
            d_num = int(md_match.group(2))
            # Assume 2025 for academic cycle 2026-2027 admissions
            assumed_year = 2025 if m_num >= 8 else 2026
            try:
                return (date(assumed_year, m_num, d_num), True)
            except ValueError:
                pass

        return (None, False)
