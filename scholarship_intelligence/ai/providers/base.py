"""Base abstract class for AI Counselor providers."""
from abc import ABC, abstractmethod
from typing import List

from scholarship_intelligence.ai.schemas import ChatMessage, CounselorContext


class BaseAIProvider(ABC):
    """Abstract interface decoupling the counselor service from specific model vendors."""

    @abstractmethod
    def generate_response(
        self,
        context: CounselorContext,
        user_message: str,
        conversation_history: List[ChatMessage],
    ) -> str:
        """Generates a natural-language counseling response grounded in the provided context.

        Args:
            context: Verified, privacy-sanitized scholarship and student intelligence facts.
            user_message: Untrusted student inquiry.
            conversation_history: Prior bounded conversation turns.

        Returns:
            Natural-language text response explaining the facts.
        """
        pass
