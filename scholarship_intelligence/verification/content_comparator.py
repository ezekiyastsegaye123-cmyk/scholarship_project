"""Content hash comparison and change detection."""
from typing import NamedTuple, Optional


class ContentComparisonResult(NamedTuple):
    """Outcome of comparing previous and current content hashes."""
    content_changed: bool
    old_hash: Optional[str]
    new_hash: str
    message: str


class ContentComparator:
    """Compares source content digests to determine if a page has modified content.
    
    Mandatory rule:
    Content changed (old_hash != new_hash) does NOT automatically imply that
    scholarship facts have changed. It signals that fact-level re-extraction
    and verification must be executed.
    """

    @staticmethod
    def compare(old_hash: Optional[str], new_hash: str) -> ContentComparisonResult:
        if not old_hash:
            return ContentComparisonResult(
                content_changed=True,
                old_hash=None,
                new_hash=new_hash,
                message="Initial content baseline established.",
            )
        
        changed = (old_hash.strip().lower() != new_hash.strip().lower())
        if changed:
            message = "Content SHA-256 hash changed. Fact-level verification required."
        else:
            message = "Content SHA-256 hash unchanged. Preserved evidence remains intact."

        return ContentComparisonResult(
            content_changed=changed,
            old_hash=old_hash,
            new_hash=new_hash,
            message=message,
        )
