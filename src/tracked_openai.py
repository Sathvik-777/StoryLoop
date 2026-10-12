"""OpenAI client proxy that records token usage without changing call sites."""

from __future__ import annotations

from typing import Any

from openai import OpenAI

from api_cost_tracker import get_cost_tracker


class _Responses:
    def __init__(self, client: OpenAI):
        self._client = client

    def create(self, *args: Any, **kwargs: Any) -> Any:
        model = kwargs.get("model", "unknown")
        try:
            response = self._client.responses.create(*args, **kwargs)
        except Exception:
            get_cost_tracker().record_openai_error("responses.create", str(model))
            raise
        get_cost_tracker().record_openai_response(response, str(model))
        return response


class _Speech:
    def __init__(self, client: OpenAI):
        self._client = client

    def create(self, *args: Any, **kwargs: Any) -> Any:
        model = str(kwargs.get("model", "unknown"))
        text = str(kwargs.get("input", ""))
        try:
            response = self._client.audio.speech.create(*args, **kwargs)
        except Exception:
            get_cost_tracker().record_openai_error("audio.speech.create", model)
            raise
        get_cost_tracker().record_speech(model, text)
        return response


class _Audio:
    def __init__(self, client: OpenAI):
        self.speech = _Speech(client)


class TrackedOpenAIClient:
    """Drop-in proxy for the OpenAI endpoints used by StoryLoop."""

    def __init__(self, client: OpenAI | None = None):
        self._client = client or OpenAI()
        self.responses = _Responses(self._client)
        self.audio = _Audio(self._client)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)
