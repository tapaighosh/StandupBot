"""
StandupBot — LLM Service

Abstract LLM interface for digest summarization, blocker detection,
and weekly trend reports. Supports OpenAI and Anthropic.
Stub — implement in Module 4.
"""

import logging
from abc import ABC, abstractmethod

from app.config import settings
from app.exceptions import ExternalServiceError

logger = logging.getLogger("standupbot.services.llm")


class BaseLLMService(ABC):
    """Abstract base class for LLM integrations."""

    @abstractmethod
    async def generate_summary(self, team_name: str, submissions: list[dict]) -> str | None:
        """
        Generate a 3–5 sentence digest summary from standup submissions.

        System prompt: "You are a chief of staff summarizing a team's daily standup
        for a manager. Be concise, factual, and surface blockers clearly."

        Returns: Summary text, or None if LLM fails (digest continues without summary).
        """
        ...

    @abstractmethod
    async def detect_blockers(self, answers: list[str]) -> list[str]:
        """
        Scan submission answers and identify blockers.

        Returns: List of blocker descriptions.
        """
        ...

    @abstractmethod
    async def generate_weekly_report(self, team_name: str, weekly_data: list[dict]) -> str | None:
        """
        Generate a weekly trend summary (Growth feature).

        Returns: Weekly rollup with themes, recurring blockers, and momentum score.
        """
        ...


class OpenAILLMService(BaseLLMService):
    """LLM service using OpenAI API (GPT-4o-mini)."""

    async def generate_summary(self, team_name: str, submissions: list[dict]) -> str | None:
        """Generate digest summary using OpenAI."""
        # TODO: Implement in Module 4
        try:
            # from openai import AsyncOpenAI
            # client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            # response = await client.chat.completions.create(...)
            logger.info(f"OpenAI summary generation for {team_name} — not yet implemented")
            return None
        except Exception as e:
            logger.error(f"OpenAI summary failed: {e}")
            return None  # Fallback: digest sends without summary

    async def detect_blockers(self, answers: list[str]) -> list[str]:
        # TODO: Implement in Module 4
        return []

    async def generate_weekly_report(self, team_name: str, weekly_data: list[dict]) -> str | None:
        # TODO: Implement in Phase 2 (Growth)
        return None


class AnthropicLLMService(BaseLLMService):
    """LLM service using Anthropic API (Claude Haiku)."""

    async def generate_summary(self, team_name: str, submissions: list[dict]) -> str | None:
        """Generate digest summary using Anthropic."""
        # TODO: Implement in Module 4
        try:
            logger.info(f"Anthropic summary generation for {team_name} — not yet implemented")
            return None
        except Exception as e:
            logger.error(f"Anthropic summary failed: {e}")
            return None

    async def detect_blockers(self, answers: list[str]) -> list[str]:
        # TODO: Implement in Module 4
        return []

    async def generate_weekly_report(self, team_name: str, weekly_data: list[dict]) -> str | None:
        # TODO: Implement in Phase 2 (Growth)
        return None


def get_llm_service() -> BaseLLMService:
    """Factory function to get the configured LLM service."""
    if settings.LLM_PROVIDER == "anthropic":
        return AnthropicLLMService()
    return OpenAILLMService()
