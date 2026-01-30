"""OpenAI provider implementation."""

import json
import logging
from typing import Optional

import requests

from .base import BaseLLMClient, LLMResponse
from .prompts import SYSTEM_PROMPT, build_correction_prompt, build_user_prompt

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI API client using direct HTTP calls."""

    API_URL = "https://api.openai.com/v1/chat/completions"

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
        """Generate draft using OpenAI API."""
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

        llm_response = self._parse_response(response_text, expected_url=url)
        if llm_response:
            return llm_response

        # Retry with correction prompt
        logger.debug("First attempt failed validation, retrying with correction")
        for attempt in range(self.max_retries):
            correction_prompt = build_correction_prompt(
                error=f"Invalid JSON or validation failed. CRITICAL: Use the actual URL {url} not example.com. Ensure final_post ≤260 chars with concrete implication."
            )
            response_text = self._call_api(correction_prompt)
            if not response_text:
                continue

            llm_response = self._parse_response(response_text, expected_url=url)
            if llm_response:
                return llm_response

        logger.warning("Failed to generate valid draft after retries")
        return None

    def _call_api(self, user_message: str) -> Optional[str]:
        """Call OpenAI API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "temperature": self.temperature,
            "max_tokens": 500,  # Enough for structured response
        }

        try:
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip()

        except requests.exceptions.Timeout:
            logger.error("OpenAI API timeout")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API error: {e}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected OpenAI response format: {e}")
            return None

    def _parse_response(self, response_text: str, expected_url: str) -> Optional[LLMResponse]:
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
                expected_url=expected_url,
            )

            # Validate (260 char limit, 3 hashtag max, correct URL)
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
