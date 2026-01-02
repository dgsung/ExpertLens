"""HuggingFace Inference API client for ExpertLens."""

import json
import os
from typing import Any

from huggingface_hub import InferenceClient


class HuggingFaceClient:
    """Client for HuggingFace Inference API.

    Uses the huggingface_hub InferenceClient for text generation.
    """

    # Free, open models
    DEFAULT_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
    BACKUP_MODELS = [
        "Qwen/Qwen2.5-72B-Instruct",
        "microsoft/Phi-3-mini-4k-instruct",
    ]

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float = 60.0,
    ):
        """Initialize HuggingFace client.

        Args:
            model: Model ID to use. Defaults to Mistral-7B-Instruct.
            api_key: Optional HuggingFace API token.
            timeout: Request timeout in seconds.
        """
        self.model = model or self.DEFAULT_MODEL
        self.api_key = api_key or os.environ.get("HF_API_KEY") or os.environ.get("HF_TOKEN")
        self.timeout = timeout
        self._client = InferenceClient(token=self.api_key, timeout=timeout)

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 1024,
        temperature: float = 0.1,
        return_full_text: bool = False,
    ) -> str:
        """Generate text completion using chat API.

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
        try:
            # Use chat completion API for better model compatibility
            response = self._client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=max_new_tokens,
                temperature=temperature if temperature > 0 else 0.01,
            )
            return response.choices[0].message.content

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
        """Close the client (no-op for InferenceClient)."""
        pass  # InferenceClient handles its own connection management

    def __enter__(self) -> "HuggingFaceClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()
