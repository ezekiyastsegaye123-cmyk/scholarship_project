"""Provider factory for AI Counselor integrations."""
import os
from typing import Optional

from scholarship_intelligence.ai.providers.base import BaseAIProvider
from scholarship_intelligence.ai.providers.external import ExternalAIProvider
from scholarship_intelligence.ai.providers.mock import MockAIProvider


def get_ai_provider(provider_type: Optional[str] = None) -> BaseAIProvider:
    """Instantiates and returns the configured AI provider.

    Defaults to 'mock' for 100% offline, zero-key, deterministic testing.
    Can be set to 'external' via environment variable AI_PROVIDER=external.
    """
    selected = provider_type or os.environ.get("AI_PROVIDER", "mock").strip().lower()

    if selected == "external":
        return ExternalAIProvider()
    elif selected == "mock":
        return MockAIProvider()
    else:
        # Fallback to mock for unknown provider to maintain availability and safety
        return MockAIProvider()
