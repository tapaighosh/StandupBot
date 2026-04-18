"""
StandupBot — LLM Service

Abstract LLM interface for digest summarization and blocker detection.

LLM PROMPT STRUCTURE — WHY THIS SPECIFIC PROMPT:
==================================================

The system prompt is: "You are a chief of staff summarizing a team's daily
standup for a busy engineering manager."

WHY "CHIEF OF STAFF" (not "AI assistant")?
- A chief of staff already knows how to filter signal from noise
- They prioritize blockers because those need immediate action
- They end with momentum/health assessment because managers want the TL;DR
- This persona produces consistently structured, actionable summaries

THE INPUT FORMAT:
  [Alice]: Yesterday: Fixed CI pipeline | Today: API tests | Blockers: None
  [Bob]: Yesterday: Design review | Today: Frontend auth | Blockers: Waiting for API keys

WHY THIS FORMAT?
- Structured (pipe-separated) so the LLM can parse reliably
- Member names included so the summary can reference specific people
- "Blockers: None" explicitly stated so the model doesn't hallucinate blockers

FALLBACK PATTERN — WHY THIS IS CRITICAL:
==========================================

Every LLM call is wrapped in try/except. If ANY call fails:
1. We log the error
2. We return None (for summaries) or [] (for blockers)
3. The digest STILL gets generated — just without AI summary

WHY? Because the digest is time-sensitive:
- A manager expects it at 10AM sharp
- An LLM outage at 9:59AM should NOT block the whole digest
- A digest without AI summary is still 90% useful (has responses, blockers, etc.)
- We can retry the summary later if needed

This is the "graceful degradation" pattern:
  LLM available  → AI summary + keyword blockers + LLM blockers
  LLM down       → No AI summary + keyword blockers only
  Both down      → Raw submission data (worst case, still useful)
"""

import logging
from abc import ABC, abstractmethod

from app.config import settings
from app.utils.helpers import detect_blocker_keywords

logger = logging.getLogger("standupbot.services.llm")


class BaseLLMService(ABC):
    """Abstract base class for LLM integrations."""

    @abstractmethod
    async def generate_summary(self, team_name: str, submissions: list[dict]) -> str | None:
        """
        Generate a 3–5 sentence digest summary from standup submissions.

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


# ═══════════════════════════════════════════════════════════════════════
# SYSTEM PROMPTS — The "personality" of our AI
# ═══════════════════════════════════════════════════════════════════════

DIGEST_SYSTEM_PROMPT = """You are a chief of staff summarizing a team's daily standup for a busy engineering manager.

Rules:
1. Write 3-5 sentences maximum.
2. LEAD with blockers — if any member has a blocker, mention it FIRST.
3. Summarize what the team accomplished yesterday and what they're focused on today.
4. END with a momentum score: "Momentum: 🟢 High" or "🟡 Medium" or "🔴 Low"
   - High = no blockers, strong progress
   - Medium = minor blockers or slow progress
   - Low = critical blockers or many non-responders
5. Be factual. Do not invent information. Reference team members by name.
6. Do NOT use bullet points. Write in prose."""

BLOCKER_SYSTEM_PROMPT = """You are a work-blocker detection system. Given a standup answer, determine if it describes a blocker — something preventing the person from making progress.

Rules:
1. Reply ONLY with "BLOCKER: <brief description>" or "NONE"
2. Examples of blockers: waiting for someone, access issues, infrastructure down, unclear requirements, dependency not ready
3. Examples of NOT blockers: normal work in progress, taking PTO, attending meetings
4. Be conservative — only flag clear blockers."""


def _format_submissions_for_prompt(submissions: list[dict]) -> str:
    """
    Format submissions into the structured text the LLM expects.

    INPUT:
      [
        {
          "member_name": "Alice",
          "answers": [
            {"question_text": "What did you accomplish?", "answer_text": "Fixed CI"},
            {"question_text": "What are you working on?", "answer_text": "API tests"},
            {"question_text": "Any blockers?", "answer_text": "None"},
          ]
        },
        ...
      ]

    OUTPUT:
      [Alice]: Yesterday: Fixed CI | Today: API tests | Blockers: None
      [Bob]: Yesterday: Design review | Today: Frontend | Blockers: Waiting for keys
    """
    lines = []
    for sub in submissions:
        parts = []
        for answer in sub.get("answers", []):
            q_text = answer.get("question_text", "")
            a_text = answer.get("answer_text", "")
            # Try to determine question type from text
            if "yesterday" in q_text.lower() or "accomplish" in q_text.lower():
                parts.append(f"Yesterday: {a_text}")
            elif "today" in q_text.lower() or "working" in q_text.lower():
                parts.append(f"Today: {a_text}")
            elif "blocker" in q_text.lower() or "help" in q_text.lower():
                parts.append(f"Blockers: {a_text}")
            else:
                parts.append(f"{q_text}: {a_text}")

        name = sub.get("member_name", "Unknown")
        lines.append(f"[{name}]: {' | '.join(parts)}")

    return "\n".join(lines)


class OpenAILLMService(BaseLLMService):
    """
    LLM service using OpenAI API (GPT-4o-mini).

    WHY GPT-4O-MINI?
    - Fast (< 2s response time)
    - Cheap ($0.15/1M input tokens) — a daily digest costs ~$0.001
    - Good enough for structured summarization (no need for GPT-4)
    - High rate limits for production use
    """

    async def generate_summary(self, team_name: str, submissions: list[dict]) -> str | None:
        """
        Generate digest summary using OpenAI.

        On failure: returns None → digest sends without AI summary.
        """
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set — skipping AI summary")
            return None

        if not submissions:
            return None

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            formatted = _format_submissions_for_prompt(submissions)

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": DIGEST_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Team: {team_name}\n"
                            f"Date: today\n"
                            f"Submissions ({len(submissions)} of team responded):\n\n"
                            f"{formatted}"
                        ),
                    },
                ],
                max_tokens=300,
                temperature=0.3,  # Low temp = more consistent/factual
            )

            summary = response.choices[0].message.content
            logger.info(f"AI summary generated for {team_name} ({len(summary or '')} chars)")
            return summary

        except Exception as e:
            # CRITICAL: Never let LLM failure block the digest
            logger.error(f"OpenAI summary failed for {team_name}: {e}")
            return None

    async def detect_blockers(self, answers: list[str]) -> list[str]:
        """
        Detect blockers using keyword matching + LLM classification.

        STRATEGY (belt and suspenders):
        1. First pass: keyword matching (fast, free, always works)
        2. Second pass: LLM classification (catches nuanced blockers)
        3. Merge results, deduplicate

        If LLM fails → we still have keyword results.
        """
        blockers: list[str] = []

        # Pass 1: Keyword detection (always works)
        for answer in answers:
            if detect_blocker_keywords(answer):
                blockers.append(answer)

        # Pass 2: LLM detection (optional enhancement)
        if settings.OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

                for answer in answers:
                    # Skip if already caught by keywords
                    if answer in blockers:
                        continue

                    response = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": BLOCKER_SYSTEM_PROMPT},
                            {"role": "user", "content": answer},
                        ],
                        max_tokens=100,
                        temperature=0.1,
                    )

                    result = (response.choices[0].message.content or "").strip()
                    if result.startswith("BLOCKER:"):
                        blockers.append(answer)

            except Exception as e:
                logger.error(f"LLM blocker detection failed: {e}")
                # Fall through — keyword results are still valid

        return blockers

    async def generate_weekly_report(self, team_name: str, weekly_data: list[dict]) -> str | None:
        """Generate weekly trend summary. (Phase 2 — Growth feature)"""
        # TODO: Implement in Phase 2
        return None


class AnthropicLLMService(BaseLLMService):
    """LLM service using Anthropic API (Claude Haiku)."""

    async def generate_summary(self, team_name: str, submissions: list[dict]) -> str | None:
        """Generate digest summary using Anthropic."""
        # Anthropic implementation follows the same pattern
        # TODO: Implement when Anthropic support is needed
        logger.info(f"Anthropic summary for {team_name} — not yet implemented")
        return None

    async def detect_blockers(self, answers: list[str]) -> list[str]:
        # Fallback to keyword detection only
        return [a for a in answers if detect_blocker_keywords(a)]

    async def generate_weekly_report(self, team_name: str, weekly_data: list[dict]) -> str | None:
        return None


def get_llm_service() -> BaseLLMService:
    """Factory function to get the configured LLM service."""
    if settings.LLM_PROVIDER == "anthropic":
        return AnthropicLLMService()
    return OpenAILLMService()
