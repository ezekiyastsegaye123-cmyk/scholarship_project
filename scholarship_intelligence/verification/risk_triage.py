"""Contextual risk signal triage and quarantine classification."""
from typing import List, NamedTuple, Optional
import re

from scholarship_intelligence.domain.enums import QuarantineReason, VerificationState

HIGH_RISK_PAYMENT_PATTERNS = [
    re.compile(r"(western union|moneygram|cashier.?s check|wire transfer|cryptocurrency|bitcoin|ethereum)", re.IGNORECASE),
    re.compile(r"(pay|send|transfer)\s+\$?\d+\s+(to\s+release|before\s+receiving|to\s+claim|processing\s+fee\s+for\s+disbursement)", re.IGNORECASE),
    re.compile(r"guarantee(d)?\s+(disbursement|award)\s+(upon|after)\s+(payment|fee)", re.IGNORECASE),
]

PHISHING_PII_PATTERNS = [
    re.compile(r"(online\s+banking\s+password|bank\s+pin|account\s+password|routing\s+pin)", re.IGNORECASE),
    re.compile(r"(credit\s+card\s+cvv|security\s+code\s+on\s+back\s+of\s+card)", re.IGNORECASE),
]

SCHOLARSHIP_APP_FEE_PATTERN = re.compile(
    r"(scholarship\s+application\s+fee|fee\s+to\s+apply\s+for\s+this\s+scholarship)", re.IGNORECASE
)

LEGITIMATE_ACADEMIC_FEE_PATTERNS = [
    re.compile(r"(common\s+app(lication)?\s+fee|undergraduate\s+application\s+fee|admissions\s+application\s+fee)", re.IGNORECASE),
    re.compile(r"(toefl|ielts|sat|act|duolingo)\s+(fee|exam\s+fee|test\s+fee)", re.IGNORECASE),
    re.compile(r"(css\s+profile|isfaa)\s+submission", re.IGNORECASE),
]


class RiskTriageResult(NamedTuple):
    """Outcome of contextual risk triage evaluation."""
    is_quarantined: bool
    quarantine_reasons: List[QuarantineReason]
    quarantine_notes: Optional[str]
    warnings: List[str]


class RiskTriager:
    """Evaluates extracted evidence text and opportunity metadata for safety, fee context, and phishing signals."""

    @classmethod
    def evaluate(
        cls,
        evidence_text: str,
        opportunity_description: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> RiskTriageResult:
        full_text = f"{evidence_text or ""} {opportunity_description or ""}"
        reasons: List[QuarantineReason] = []
        warnings: List[str] = []
        notes_parts: List[str] = []

        # 1. Phishing & credential theft check
        for pattern in PHISHING_PII_PATTERNS:
            if pattern.search(full_text):
                reasons.append(QuarantineReason.PHISHING_INDICATOR)
                notes_parts.append("Critical risk: Page requests sensitive credentials, passwords, or banking security codes.")
                break

        # 2. Fraudulent disbursement fee check
        for pattern in HIGH_RISK_PAYMENT_PATTERNS:
            if pattern.search(full_text):
                reasons.append(QuarantineReason.SUSPICIOUS_PAYMENT_REQUEST)
                notes_parts.append("High risk: Pre-disbursement fee, wire transfer, or cryptocurrency payment demanded to release grant.")
                break

        # 3. Contextual fee check (scholarship application fee vs college admissions fee)
        if SCHOLARSHIP_APP_FEE_PATTERN.search(full_text):
            is_standard_academic = any(pat.search(full_text) for pat in LEGITIMATE_ACADEMIC_FEE_PATTERNS)
            if not is_standard_academic:
                warnings.append("Notice: An application fee specifically for this scholarship was detected. Requires manual review.")
                reasons.append(QuarantineReason.UNSUPPORTED_MATERIAL_CLAIM)
                notes_parts.append("Non-standard fee: Dedicated scholarship application fee detected. Quarantined for staff review.")

        is_quarantined = len(reasons) > 0
        quarantine_notes = " ".join(notes_parts) if notes_parts else None

        return RiskTriageResult(
            is_quarantined=is_quarantined,
            quarantine_reasons=reasons,
            quarantine_notes=quarantine_notes,
            warnings=warnings,
        )
