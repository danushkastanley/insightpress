"""Draft post composer with editorial quality enforcement."""

import logging
import random
from pathlib import Path
from typing import Optional

from ..config import Config
from ..models import Draft, RankedItem
from ..processing.rank import get_matched_topics
from .hashtags import get_relevant_hashtags

logger = logging.getLogger(__name__)


# Implication-focused templates
# Each template MUST include a concrete "why this matters" statement
IMPLICATION_TEMPLATES = [
    {
        "pattern": "{hook} {implication}",
        "implications": [
            "This changes how teams will need to handle {domain}.",
            "Worth understanding the operational cost before adopting.",
            "This is the kind of guardrail teams need to stop {risk}.",
            "Could shift security posture for {domain} workflows.",
            "Likely to impact how we think about {domain} trade-offs.",
            "Matters for anyone running {domain} in production.",
            "This addresses a real gap in {domain} tooling.",
        ],
    },
    {
        "pattern": "{hook} {implication} {action}",
        "implications": [
            "Implications for {domain} teams are non-trivial.",
            "This could reduce operational overhead in {domain}.",
            "Security implications worth reviewing.",
            "Performance trade-offs here matter at scale.",
            "Changes the risk calculus for {domain} deployments.",
        ],
        "actions": [
            "Test in non-prod first.",
            "Review the trade-offs before adopting.",
            "Worth a look at the architecture.",
            "Check compatibility with existing workflows.",
        ],
    },
    {
        "pattern": "{hook} {implication}",
        "implications": [
            "This affects anyone responsible for {domain} reliability.",
            "Cost implications need review before rollout.",
            "Could help reduce toil in {domain} operations.",
            "Worth watching if you manage {domain} at scale.",
            "Security model here is different than most assume.",
        ],
    },
]

# Domain mapping for implication context
DOMAIN_MAP = {
    "kubernetes": "container orchestration",
    "docker": "containerization",
    "ai": "AI systems",
    "llm": "LLM deployments",
    "ml": "ML pipelines",
    "security": "production security",
    "devops": "DevOps",
    "cloud": "cloud infrastructure",
    "observability": "observability",
    "rust": "systems programming",
    "python": "Python development",
}

# Risk/concern mapping for implications
RISK_MAP = {
    "ai": "AI tooling creeping into prod",
    "llm": "unvetted LLM usage",
    "security": "unpatched vulnerabilities",
    "kubernetes": "cluster misconfigurations",
    "cloud": "runaway cloud costs",
}


def generate_drafts(
    ranked_items: list[RankedItem],
    count: Optional[int] = None,
    style: Optional[str] = None,
    llm_client=None,
) -> list[Draft]:
    """
    Generate draft X posts with strict editorial quality.

    Args:
        ranked_items: List of RankedItem objects (should be pre-sorted)
        count: Number of drafts to generate (uses config default if None)
        style: Draft style (uses config default if None)
        llm_client: Optional LLM client for AI-powered drafting

    Returns:
        List of Draft objects (all under CHAR_LIMIT)
    """
    count = count or Config.DRAFTS_COUNT
    style = style or Config.DRAFT_STYLE

    generation_mode = "template"
    if llm_client:
        provider = Config.LLM_PROVIDER
        generation_mode = f"llm:{provider}"
        logger.info(f"Generating up to {count} drafts with LLM provider: {provider}")
    else:
        logger.info(f"Generating up to {count} drafts with template-based drafting")

    logger.info(f"Hard character limit: {Config.CHAR_LIMIT}")

    # Load voice guidance if available
    voice_guidance = _load_voice_guidance()

    drafts = []
    used_titles = set()  # Prevent repetition

    # Try to generate required number of drafts
    for i, ranked_item in enumerate(ranked_items):
        if len(drafts) >= count:
            break

        # Skip if title is too similar to already used
        if ranked_item.item.title in used_titles:
            logger.debug(f"Skipping similar title: {ranked_item.item.title[:50]}...")
            continue

        # Try LLM generation first if client is available
        draft = None
        if llm_client:
            draft = _compose_draft_with_llm(ranked_item, llm_client, generation_mode)

        # Fall back to template if LLM failed or not available
        if not draft:
            if llm_client:
                logger.debug("LLM generation failed, falling back to template")
            draft = _compose_draft(ranked_item, voice_guidance)

        if draft:
            # Enforce hard character limit
            if draft.char_count <= Config.CHAR_LIMIT:
                drafts.append(draft)
                used_titles.add(ranked_item.item.title)
                logger.debug(f"Generated draft {len(drafts)}: {draft.char_count} chars [{draft.generation_mode}]")
            else:
                # Try to trim intelligently
                trimmed_draft = _trim_draft(draft, ranked_item)
                if trimmed_draft and trimmed_draft.char_count <= Config.CHAR_LIMIT:
                    drafts.append(trimmed_draft)
                    used_titles.add(ranked_item.item.title)
                    logger.debug(f"Generated draft {len(drafts)} (trimmed): {trimmed_draft.char_count} chars [{trimmed_draft.generation_mode}]")
                else:
                    logger.debug(f"Skipping over-limit draft: {draft.char_count} chars")

    logger.info(f"Successfully generated {len(drafts)} drafts (all under {Config.CHAR_LIMIT} chars)")
    return drafts


def _load_voice_guidance() -> Optional[dict]:
    """Load voice.md if present for tone consistency."""
    if not Config.VOICE_FILE or not Config.VOICE_FILE.exists():
        return None

    try:
        with open(Config.VOICE_FILE, "r") as f:
            content = f.read()

        # Extract heuristics from example posts
        lines = [line.strip() for line in content.split("\n") if line.strip()]

        if not lines:
            return None

        # Calculate average sentence length
        avg_length = sum(len(line) for line in lines) / len(lines)

        return {
            "avg_sentence_length": avg_length,
            "example_count": len(lines),
        }
    except Exception as e:
        logger.warning(f"Failed to load voice guidance: {e}")
        return None


def _compose_draft_with_llm(
    ranked_item: RankedItem,
    llm_client,
    generation_mode: str,
) -> Optional[Draft]:
    """
    Compose a draft using LLM provider.

    Args:
        ranked_item: Ranked item to generate draft for
        llm_client: LLM client instance
        generation_mode: Generation mode string (e.g., "llm:openai")

    Returns:
        Draft object if successful, None if LLM generation failed
    """
    item = ranked_item.item

    # Get matched topics for context
    topics_lower = [t.lower().strip() for t in Config.TOPICS]
    matched_topics = get_matched_topics(item, topics_lower)

    # Get allowed hashtags from whitelist
    from .hashtags import HashtagMapper
    hashtag_mapper = HashtagMapper()
    allowed_hashtags = hashtag_mapper.get_hashtags(item, max_tags=Config.HASHTAGS_MAX)

    try:
        # Call LLM
        llm_response = llm_client.generate_draft(
            title=item.title,
            url=item.url,
            source=item.source,
            published_at=item.published_at.isoformat(),
            summary=item.summary,
            matched_topics=matched_topics,
            allowed_hashtags=allowed_hashtags,
        )

        if not llm_response:
            return None

        # Create Draft from LLM response
        draft = Draft(
            content=llm_response.final_post,
            source_item=item,
            hashtags=llm_response.hashtags,
            generation_mode=generation_mode,
        )

        logger.debug(f"LLM generated draft: {draft.char_count} chars")
        return draft

    except Exception as e:
        logger.error(f"LLM draft generation error: {e}")
        return None


def _compose_draft(ranked_item: RankedItem, voice_guidance: Optional[dict]) -> Optional[Draft]:
    """Compose a single draft from a ranked item."""
    item = ranked_item.item

    # Select template
    template = random.choice(IMPLICATION_TEMPLATES)

    # Build hook (avoid verbatim headline)
    hook = _create_hook(item.title)

    # Build implication (MANDATORY)
    implication = _create_implication(item, ranked_item, template)

    if not implication:
        logger.debug(f"Could not create implication for: {item.title[:50]}...")
        return None

    # Build action (optional)
    action = None
    if "actions" in template and random.random() > 0.5:  # 50% chance
        action = random.choice(template["actions"])

    # Assemble content
    parts = []

    if "action" in template["pattern"]:
        if action:
            content_text = template["pattern"].format(
                hook=hook,
                implication=implication,
                action=action,
            )
        else:
            # Fallback to pattern without action
            content_text = f"{hook} {implication}"
    else:
        content_text = template["pattern"].format(
            hook=hook,
            implication=implication,
        )

    parts.append(content_text)

    # Add URL on its own line
    parts.append(f"\n{item.url}")

    # Get hashtags (0-3, strict)
    hashtags = get_relevant_hashtags(item)

    # Add hashtags if any
    if hashtags:
        hashtag_str = " ".join(f"#{tag}" for tag in hashtags)
        parts.append(f"\n{hashtag_str}")

    content = " ".join(parts)

    return Draft(
        content=content,
        source_item=item,
        hashtags=hashtags,
        generation_mode="template",
    )


def _create_hook(title: str) -> str:
    """
    Create hook from title.

    RULES:
    - Never use verbatim headline
    - Keep it short and direct
    - Focus on what changed
    """
    # Remove common prefixes
    prefixes = [
        "Show HN: ",
        "Ask HN: ",
        "Tell HN: ",
        "Launch HN: ",
        "Announcing ",
        "Introducing ",
    ]

    for prefix in prefixes:
        if title.startswith(prefix):
            title = title[len(prefix):]

    # Shorten if too long (be aggressive to leave room for implication + URL + hashtags)
    max_hook_length = 50
    if len(title) > max_hook_length:
        # Try to cut at sentence boundary
        if "." in title[:max_hook_length]:
            title = title[:title.find(".", 0, max_hook_length) + 1]
        else:
            # Cut at last space to avoid mid-word truncation
            if " " in title[:max_hook_length]:
                last_space = title[:max_hook_length].rfind(" ")
                truncated = title[:last_space].strip()

                # Check if we're ending on incomplete phrases like "a", "the", "an", "in", "of", "to"
                incomplete_words = ["a", "an", "the", "in", "of", "to", "for", "at", "by", "on"]
                words = truncated.split()
                if words and words[-1].lower() in incomplete_words:
                    # Remove the incomplete word and try again
                    truncated = " ".join(words[:-1])

                # Strip trailing punctuation (except periods which indicate sentence end)
                title = truncated.rstrip(",;:")
            else:
                # No spaces found, just cut and clean
                title = title[:max_hook_length].rstrip(",;:")

    return title


def _create_implication(
    item,
    ranked_item: RankedItem,
    template: dict,
) -> Optional[str]:
    """
    Create explicit implication statement.

    MANDATORY: Must express concrete risk/cost/workflow impact.
    """
    text = f"{item.title} {item.summary or ''}".lower()

    # Identify domain
    domain = "production systems"  # default
    risk = "operational issues"  # default

    for keyword, domain_name in DOMAIN_MAP.items():
        if keyword in text:
            domain = domain_name
            break

    for keyword, risk_name in RISK_MAP.items():
        if keyword in text:
            risk = risk_name
            break

    # Select implication template
    implication_template = random.choice(template["implications"])

    # Fill in context
    try:
        implication = implication_template.format(domain=domain, risk=risk)
        return implication
    except KeyError:
        # Template doesn't use variables
        return implication_template


def _trim_draft(draft: Draft, ranked_item: RankedItem) -> Optional[Draft]:
    """
    Intelligently trim draft to fit character limit.

    Strategy:
    1. Remove action clause if present
    2. Shorten hook
    3. Reduce hashtags
    """
    content = draft.content
    item = draft.source_item

    # Try removing action clause (last sentence before URL)
    lines = content.split("\n")
    if len(lines) >= 2:
        # Try removing last sentence of first paragraph
        first_para = lines[0]
        sentences = first_para.split(". ")

        if len(sentences) > 2:
            # Remove last sentence (likely action)
            trimmed_text = ". ".join(sentences[:-1]) + "."
            new_lines = [trimmed_text] + lines[1:]
            new_content = "\n".join(new_lines)

            if len(new_content) <= Config.CHAR_LIMIT:
                return Draft(
                    content=new_content,
                    source_item=item,
                    hashtags=draft.hashtags,
                    generation_mode=draft.generation_mode,
                )

    # Try reducing hashtags
    if len(draft.hashtags) > 1:
        reduced_hashtags = draft.hashtags[:1]  # Keep only first hashtag
        parts = content.split("\n#")  # Split at hashtag line
        if len(parts) > 1:
            new_hashtag_str = "#" + reduced_hashtags[0]
            new_content = parts[0] + "\n" + new_hashtag_str

            if len(new_content) <= Config.CHAR_LIMIT:
                return Draft(
                    content=new_content,
                    source_item=item,
                    hashtags=reduced_hashtags,
                    generation_mode=draft.generation_mode,
                )

    # Try removing all hashtags
    lines = content.split("\n")
    if len(lines) >= 3:  # Has hashtags
        new_content = "\n".join(lines[:-1])  # Remove hashtag line

        if len(new_content) <= Config.CHAR_LIMIT:
            return Draft(
                content=new_content,
                source_item=item,
                hashtags=[],
                generation_mode=draft.generation_mode,
            )

    # Could not trim enough
    logger.debug(f"Could not trim draft to {Config.CHAR_LIMIT} chars: {len(content)}")
    return None
