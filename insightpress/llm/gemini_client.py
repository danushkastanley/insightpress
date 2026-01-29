"""Google Gemini provider implementation."""

import json
import logging
from typing import Optional

import requests

from .base import BaseLLMClient, LLMResponse
from .prompts import SYSTEM_PROMPT, build_correction_prompt, build_user_prompt

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """Google Gemini API client using direct HTTP calls."""

    API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def generate_draft(
        self,
        title: str,
        url: str,
        source: str,
        published_at: str,
        summary: Optional[str],
        matched_topics: list[str],
        allowed_hashtags: list[str],
    ) -> Optional[LLMResponse]:
        """Generate draft using Gemini API."""
        user_prompt = build_user_prompt(
            title=title,
            url=url,
            source=source,
            published_at=published_at,
            summary=summary or "",
            matched_topics=matched_topics,
            allowed_hashtags=allowed_hashtags,
        )

        # First attempt
        response_text = self._call_api(user_prompt)
        if not response_text:
            return None

        llm_response = self._parse_response(response_text)
        if llm_response:
            return llm_response

        # Retry with correction prompt
        logger.debug("First attempt failed validation, retrying with correction")
        for attempt in range(self.max_retries):
            correction_prompt = build_correction_prompt(
                error="Invalid JSON or validation failed. Ensure final_post ≤260 chars with concrete implication."
            )
            response_text = self._call_api(correction_prompt)
            if not response_text:
                continue

            llm_response = self._parse_response(response_text)
            if llm_response:
                return llm_response

        logger.warning("Failed to generate valid draft after retries")
        return None

    def _call_api(self, user_message: str) -> Optional[str]:
        """Call Gemini API."""
        api_url = self.API_URL_TEMPLATE.format(model=self.model)

        # Gemini uses API key as query parameter
        params = {"key": self.api_key}

        # Gemini combines system and user in contents
        full_prompt = f"{SYSTEM_PROMPT}\n\n{user_message}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": full_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": 500,
            },
        }

        try:
            response = requests.post(
                api_url,
                params=params,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            return content.strip()

        except requests.exceptions.Timeout:
            logger.error("Gemini API timeout")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API error: {e}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected Gemini response format: {e}")
            return None

    def _parse_response(self, response_text: str) -> Optional[LLMResponse]:
        """Parse and validate LLM response."""
        try:
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            data = json.loads(response_text)

            llm_response = LLMResponse(
                hook=data.get("hook", ""),
                implication=data.get("implication", ""),
                action=data.get("action"),
                hashtags=data.get("hashtags", []),
                final_post=data.get("final_post", ""),
                char_count=len(data.get("final_post", "")),
            )

            # Validate (260 char limit, 3 hashtag max)
            is_valid, error = llm_response.is_valid(max_chars=260, max_hashtags=3)
            if not is_valid:
                logger.debug(f"Response validation failed: {error}")
                return None

            return llm_response

        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected parsing error: {e}")
            return None
