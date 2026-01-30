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

CRITICAL: The final_post field MUST:
- Be the complete formatted post ready to publish
- Include the EXACT URL provided in the item metadata (not a placeholder)
- Format: hook + implication + optional action + newline + URL + newline + hashtags
- Use ONLY the URL provided in the metadata - never use example.com or placeholder URLs"""

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

CRITICAL INSTRUCTIONS:
1. Base your draft on the ACTUAL article title and summary provided above
2. The final_post MUST include the EXACT URL: {url}
3. Do NOT use placeholder URLs like example.com or generic content
4. Write specifically about what THIS article discusses, not generic topics
5. Final post ≤260 chars (HARD LIMIT)
6. Must include concrete implication specific to this article
7. Hashtags must be lowercase and from allowed list only

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
