"""Output validator ensuring AI responses strictly adhere to epistemic safety invariants."""
import re
from typing import Optional, Tuple

from scholarship_intelligence.ai.schemas import CounselorContext, EpistemicStatus


# Forbidden patterns: probability, winning odds, chances, rankings, guarantees
PROBABILITY_PATTERNS = [
    re.compile(r"\b\d{1,3}(?:\.\d+)?%\s*(?:chance|probability|likely|odds|match|acceptance|rate)", re.IGNORECASE),
    re.compile(r"(?:chance|probability|odds)\s+(?:of|is|are)\s+\d{1,3}(?:\.\d+)?%", re.IGNORECASE),
    re.compile(r"\b(?:guaranteed\s+acceptance|guaranteed\s+admission|100%\s+guaranteed)\b", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+ranked\s+#?\d+\b", re.IGNORECASE),
    re.compile(r"\b(?:probability|chance)\s+of\s+winning\b", re.IGNORECASE),
]

LEAKAGE_PATTERNS = [
    re.compile(r"\b(?:SYSTEM\s*PROMPT|BEGIN\s*INSTRUCTIONS|INTERNAL\s*PROMPT)\b", re.IGNORECASE),
    re.compile(r"\b(?:AI_API_KEY|SECRET_KEY|BEARER_TOKEN)\b", re.IGNORECASE),
]


def validate_ai_output(output_text: str, context: CounselorContext) -> Tuple[bool, Optional[str]]:
    """Validates that model output does not violate epistemic or safety invariants.

    Returns:
        (is_valid, failure_reason)
    """
    if not output_text or not output_text.strip():
        return False, "Response is empty."

    # 1. Check for prompt leakage
    for pattern in LEAKAGE_PATTERNS:
        if pattern.search(output_text):
            return False, "Output contains potential system prompt or credential leakage."

    # 2. Check for probability or chance claims
    for pattern in PROBABILITY_PATTERNS:
        if pattern.search(output_text):
            return False, "Output attempts to quantify admission/award chances or probabilities."

    # 3. Check for Full Tuition vs Full Funding overreach
    lower_text = output_text.lower()
    if context.funding_classification == "FULL_TUITION":
        if "covers all living expenses" in lower_text or "full living stipend included" in lower_text:
            return False, "Output conflates FULL_TUITION with complete living expense coverage."

    # 4. Check for conflicting information overreach
    if context.epistemic_status == EpistemicStatus.CONFLICTING_INFORMATION:
        if "conflict is resolved" in lower_text or "authoritatively confirmed" in lower_text:
            return False, "Output inappropriately resolved conflicting evidence without official verification."

    return True, None
