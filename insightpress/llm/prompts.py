"""Prompt templates for LLM draft generation."""

SYSTEM_PROMPT = """You are an editorial assistant for a senior DevOps/AI practitioner who posts technical insights on X (Twitter).

CRITICAL RULES:
1. HARD CHARACTER LIMIT: Final post MUST be ≤260 characters (strict)
2. EXPLICIT IMPLICATION: Every post MUST include ONE concrete implication:
   - risk (security, reliability, operational)
   - cost (financial, performance, resource)
   - workflow change (process, tooling, team impact)
   - security posture (attack surface, compliance)
   - operational trade-off (complexity vs benefit)

3. MANDATORY STRUCTURE:
   - Hook: What changed (1 short sentence)
   - Implication: Why it matters (1 sentence with concrete implication)
   - Action: Optional suggested test/review (short clause)
   - URL: On its own line
   - Hashtags: 0-3 lowercase tags from whitelist

4. TONE:
   - Calm, professional practitioner voice
   - Signal > noise
   - No emojis, no clickbait, no hype
   - No speculation beyond source facts
   - Never copy headlines verbatim

5. HASHTAGS:
   - Max 3 tags
   - Lowercase only
   - Only from provided whitelist
   - Domain-focused (no brand names)
   - If none relevant: use zero hashtags

OUTPUT FORMAT:
Return ONLY valid JSON (no markdown, no explanations):
{
  "hook": "what changed in 1 sentence",
  "implication": "concrete why-it-matters with risk/cost/workflow",
  "action": "optional short test/review suggestion or null",
  "hashtags": ["tag1", "tag2"],
  "final_post": "complete post text including URL and hashtags"
}

The final_post field MUST be the complete formatted post ready to publish."""

USER_PROMPT_TEMPLATE = """Generate a draft X post for this item:

ITEM METADATA:
- Title: {title}
- Source: {source}
- Published: {published_at}
- URL: {url}
- Summary: {summary}
- Matched Topics: {matched_topics}

ALLOWED HASHTAGS (choose 0-3):
{allowed_hashtags}

CONSTRAINTS:
- Final post ≤260 chars (HARD LIMIT)
- Must include concrete implication (risk/cost/workflow)
- Hashtags must be lowercase and from allowed list only
- URL must be on its own line

Return JSON only (no markdown formatting)."""


CORRECTION_PROMPT_TEMPLATE = """Your previous response had an error: {error}

Please fix and return ONLY valid JSON with the corrected draft.

REMINDER: Final post must be ≤260 chars with concrete implication.

Return JSON only (no markdown formatting)."""


def build_user_prompt(
    title: str,
    url: str,
    source: str,
    published_at: str,
    summary: str,
    matched_topics: list[str],
    allowed_hashtags: list[str],
) -> str:
    """Build user prompt from item metadata."""
    summary_text = summary or "No summary available"
    topics_text = ", ".join(matched_topics) if matched_topics else "None"
    hashtags_text = ", ".join(f"#{tag}" for tag in allowed_hashtags) if allowed_hashtags else "None available"

    return USER_PROMPT_TEMPLATE.format(
        title=title,
        source=source,
        published_at=published_at,
        url=url,
        summary=summary_text,
        matched_topics=topics_text,
        allowed_hashtags=hashtags_text,
    )


def build_correction_prompt(error: str) -> str:
    """Build correction prompt for retry."""
    return CORRECTION_PROMPT_TEMPLATE.format(error=error)
