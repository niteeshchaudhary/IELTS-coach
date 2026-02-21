"""
LLM Engine — Provider abstraction for language model interactions.

Supports OpenAI, Google Gemini, and Ollama backends.
All LLM calls go through this module for consistency.
"""

import os
from abc import ABC, abstractmethod
from typing import Optional

import config


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        user_message: str,
        context: list[dict],
        system_prompt: str = "",
        temperature: float = config.LLM_TEMPERATURE,
        max_tokens: int = config.LLM_MAX_TOKENS,
    ) -> str:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    def classify(
        self,
        prompt: str,
        text: str,
        categories: list[str],
    ) -> dict:
        """Classify text into categories. Returns {category: score}."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, model: str = config.LLM_MODEL, api_key: str = None):
        self.model = model
        self._api_key = api_key or config.OPENAI_API_KEY
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def generate(
        self,
        user_message: str,
        context: list[dict],
        system_prompt: str = "",
        temperature: float = config.LLM_TEMPERATURE,
        max_tokens: int = config.LLM_MAX_TOKENS,
    ) -> str:
        client = self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(context)
        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content.strip()

    def classify(
        self,
        prompt: str,
        text: str,
        categories: list[str],
    ) -> dict:
        client = self._get_client()

        classification_prompt = (
            f"{prompt}\n\n"
            f"Text to classify: \"{text}\"\n\n"
            f"Categories: {', '.join(categories)}\n\n"
            f"Respond with ONLY a JSON object mapping each category to a score (0.0 to 1.0)."
        )

        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": classification_prompt}],
            temperature=0.1,
            max_tokens=200,
        )

        import json
        try:
            result_text = response.choices[0].message.content.strip()
            # Handle markdown code blocks
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(result_text)
        except (json.JSONDecodeError, IndexError):
            return {cat: 0.5 for cat in categories}


class GeminiProvider(LLMProvider):
    """Google Gemini provider."""

    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or "gemini-pro"
        self._api_key = api_key or config.GEMINI_API_KEY
        self._client = None

    def _get_client(self):
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            self._client = genai.GenerativeModel(self.model)
        return self._client

    def generate(
        self,
        user_message: str,
        context: list[dict],
        system_prompt: str = "",
        temperature: float = config.LLM_TEMPERATURE,
        max_tokens: int = config.LLM_MAX_TOKENS,
    ) -> str:
        client = self._get_client()

        # Build conversation for Gemini
        parts = []
        if system_prompt:
            parts.append(f"[System Instructions]\n{system_prompt}\n\n")

        for turn in context:
            role = "User" if turn["role"] == "user" else "Assistant"
            parts.append(f"{role}: {turn['content']}\n")

        parts.append(f"User: {user_message}\nAssistant:")

        full_prompt = "".join(parts)

        response = client.generate_content(
            full_prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )

        return response.text.strip()

    def classify(
        self,
        prompt: str,
        text: str,
        categories: list[str],
    ) -> dict:
        client = self._get_client()

        classification_prompt = (
            f"{prompt}\n\n"
            f"Text to classify: \"{text}\"\n\n"
            f"Categories: {', '.join(categories)}\n\n"
            f"Respond with ONLY a JSON object mapping each category to a score (0.0 to 1.0)."
        )

        response = client.generate_content(
            classification_prompt,
            generation_config={"temperature": 0.1, "max_output_tokens": 200},
        )

        import json
        try:
            result_text = response.text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(result_text)
        except (json.JSONDecodeError, IndexError):
            return {cat: 0.5 for cat in categories}


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(self, model: str = None, base_url: str = None):
        self.model = model or config.LLM_MODEL
        self.base_url = base_url or config.OLLAMA_BASE_URL

    def generate(
        self,
        user_message: str,
        context: list[dict],
        system_prompt: str = "",
        temperature: float = config.LLM_TEMPERATURE,
        max_tokens: int = config.LLM_MAX_TOKENS,
    ) -> str:
        import requests

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(context)
        messages.append({"role": "user", "content": user_message})

        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
            timeout=config.LLM_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()

    def classify(
        self,
        prompt: str,
        text: str,
        categories: list[str],
    ) -> dict:
        import requests

        classification_prompt = (
            f"{prompt}\n\n"
            f"Text to classify: \"{text}\"\n\n"
            f"Categories: {', '.join(categories)}\n\n"
            f"Respond with ONLY a JSON object mapping each category to a score (0.0 to 1.0)."
        )

        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": classification_prompt,
                "stream": False,
                "options": {"temperature": 0.1},
            },
            timeout=config.LLM_TIMEOUT,
        )
        response.raise_for_status()

        import json
        try:
            result_text = response.json()["response"].strip()
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(result_text)
        except (json.JSONDecodeError, KeyError):
            return {cat: 0.5 for cat in categories}


class GroqProvider(LLMProvider):
    """Groq Cloud provider (OpenAI compatible)."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or config.LLM_MODEL
        self._api_key = api_key or config.GROQ_API_KEY
        self._client = None

    def _get_client(self):
        if self._client is None:
            # Groq is OpenAI compatible, we use the groq library if available
            # or fallback to OpenAI with a custom base_url
            try:
                from groq import Groq
                self._client = Groq(api_key=self._api_key)
            except ImportError:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self._api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
        return self._client

    def generate(
        self,
        user_message: str,
        context: list[dict],
        system_prompt: str = "",
        temperature: float = config.LLM_TEMPERATURE,
        max_tokens: int = config.LLM_MAX_TOKENS,
    ) -> str:
        client = self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(context)
        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content.strip()

    def classify(
        self,
        prompt: str,
        text: str,
        categories: list[str],
    ) -> dict:
        client = self._get_client()

        classification_prompt = (
            f"{prompt}\n\n"
            f"Text to classify: \"{text}\"\n\n"
            f"Categories: {', '.join(categories)}\n\n"
            f"Respond with ONLY a JSON object mapping each category to a score (0.0 to 1.0)."
        )

        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": classification_prompt}],
            temperature=0.1,
            max_tokens=200,
            response_format={"type": "json_object"} if hasattr(client, "chat") else None
        )

        import json
        try:
            result_text = response.choices[0].message.content.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(result_text)
        except (json.JSONDecodeError, IndexError):
            return {cat: 0.5 for cat in categories}


def get_llm(provider: Optional[str] = None) -> LLMProvider:
    """
    Factory function to get the configured LLM provider.

    Args:
        provider: Override provider name. If None, uses config.LLM_PROVIDER.

    Returns:
        LLMProvider instance
    """
    provider = provider or config.LLM_PROVIDER

    if provider == "openai":
        return OpenAIProvider()
    elif provider == "gemini":
        return GeminiProvider()
    elif provider == "ollama":
        return OllamaProvider()
    elif provider == "groq":
        return GroqProvider()
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Supported: openai, gemini, ollama"
        )
