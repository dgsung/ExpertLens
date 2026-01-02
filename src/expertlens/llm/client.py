"""HuggingFace Inference API client for ExpertLens."""

import json
import os
from typing import Any

import httpx


class HuggingFaceClient:
    """Client for HuggingFace Inference API.

    Uses the free Inference API with open models.
    No API key required for public models with rate limits.
    """

    # Free, open models that work without API key
    DEFAULT_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
    BACKUP_MODELS = [
        "google/flan-t5-xxl",
        "bigscience/bloom-560m",
    ]

    BASE_URL = "https://api-inference.huggingface.co/models"

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float = 60.0,
    ):
        """Initialize HuggingFace client.

        Args:
            model: Model ID to use. Defaults to Mistral-7B-Instruct.
            api_key: Optional HuggingFace API token for higher rate limits.
            timeout: Request timeout in seconds.
        """
        self.model = model or self.DEFAULT_MODEL
        self.api_key = api_key or os.environ.get("HF_API_KEY")
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 1024,
        temperature: float = 0.1,
        return_full_text: bool = False,
    ) -> str:
        """Generate text completion.

        Args:
            prompt: The input prompt.
            max_new_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (lower = more deterministic).
            return_full_text: Whether to include prompt in response.

        Returns:
            Generated text string.

        Raises:
            RuntimeError: If API call fails.
        """
        url = f"{self.BASE_URL}/{self.model}"

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "return_full_text": return_full_text,
                "do_sample": temperature > 0,
            },
        }

        try:
            response = self._client.post(url, json=payload, headers=headers)

            if response.status_code == 503:
                # Model is loading, wait and retry
                data = response.json()
                if "estimated_time" in data:
                    import time
                    wait_time = min(data["estimated_time"], 30)
                    time.sleep(wait_time)
                    return self.generate(
                        prompt, max_new_tokens, temperature, return_full_text
                    )

            response.raise_for_status()
            result = response.json()

            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "")
            elif isinstance(result, dict):
                return result.get("generated_text", "")
            else:
                return str(result)

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HuggingFace API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"HuggingFace API error: {e}")

    def extract_json(self, prompt: str, max_new_tokens: int = 1024) -> dict[str, Any]:
        """Generate and parse JSON response.

        Args:
            prompt: The input prompt (should request JSON output).
            max_new_tokens: Maximum tokens to generate.

        Returns:
            Parsed JSON dictionary.

        Raises:
            ValueError: If response cannot be parsed as JSON.
        """
        response = self.generate(prompt, max_new_tokens, temperature=0.1)

        # Try to extract JSON from response
        try:
            # Look for JSON block in response
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "{" in response:
                # Find first { and last }
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            else:
                json_str = response

            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}\nResponse: {response[:500]}")

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "HuggingFaceClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()
