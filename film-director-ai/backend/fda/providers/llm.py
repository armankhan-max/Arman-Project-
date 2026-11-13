"""Reasoning models. Claude is the primary provider; others share the same interface."""
from dataclasses import dataclass

from .base import CredField, Provider, ProviderError, http


@dataclass
class LLMResult:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


class LLMProvider(Provider):
    default_model = ""

    def model(self):
        return (self.config or {}).get("model") or self.default_model

    def complete(self, system: str, messages: list, max_tokens=2000, temperature=0.7, json_mode=False) -> LLMResult:
        raise NotImplementedError


class Anthropic(LLMProvider):
    default_model = "claude-sonnet-5-5"

    def __init__(self):
        super().__init__(name="anthropic", label="Anthropic Claude", caps=("llm",), paid=True, unit="1k tokens",
                         fields=(CredField("api_key", "API key", "ANTHROPIC_API_KEY"),), docs="https://docs.anthropic.com",
                         notes="Primary reasoning model for the Director and specialist agents.")

    def complete(self, system, messages, max_tokens=2000, temperature=0.7, json_mode=False):
        self.need()
        r = http("POST", "https://api.anthropic.com/v1/messages", timeout=300,
                 headers={"x-api-key": self.creds["api_key"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
                 json={"model": self.model(), "max_tokens": max_tokens, "temperature": temperature, "system": system, "messages": messages})
        j = r.json()
        u = j.get("usage") or {}
        return LLMResult("".join(b.get("text", "") for b in j.get("content", []) if b.get("type") == "text"), j.get("model", self.model()),
                         u.get("input_tokens", 0), u.get("output_tokens", 0))

    def validate(self):
        if not self.configured():
            return False, "Missing API key"
        try:
            self.complete("Reply with OK.", [{"role": "user", "content": "ping"}], max_tokens=5)
            return True, "Connected (%s)" % self.model()
        except ProviderError as e:
            return False, str(e)


class OpenAICompatible(LLMProvider):
    base_url = ""

    def complete(self, system, messages, max_tokens=2000, temperature=0.7, json_mode=False):
        self.need()
        body = {"model": self.model(), "messages": [{"role": "system", "content": system}] + messages, "max_tokens": max_tokens, "temperature": temperature}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        headers = {"content-type": "application/json"}
        if self.creds.get("api_key"):
            headers["authorization"] = "Bearer " + self.creds["api_key"]
        self._tweak(body)
        j = http("POST", self.base_url, timeout=300, headers=headers, json=body).json()
        if "choices" not in j:
            raise ProviderError("Unexpected reply: %s" % str(j)[:200])
        u = j.get("usage") or {}
        return LLMResult(j["choices"][0]["message"].get("content") or "", j.get("model", self.model()), u.get("prompt_tokens", 0), u.get("completion_tokens", 0))

    def _tweak(self, body):
        pass

    def validate(self):
        if not self.configured():
            return False, "Missing API key"
        try:
            self.complete("Reply with OK.", [{"role": "user", "content": "ping"}], max_tokens=5)
            return True, "Connected (%s)" % self.model()
        except ProviderError as e:
            return False, str(e)


class OpenAI(OpenAICompatible):
    default_model = "gpt-4.1-mini"
    base_url = "https://api.openai.com/v1/chat/completions"

    def __init__(self):
        super().__init__(name="openai", label="OpenAI", caps=("llm",), paid=True, unit="1k tokens",
                         fields=(CredField("api_key", "API key", "OPENAI_API_KEY"),), docs="https://platform.openai.com/docs")


class Groq(OpenAICompatible):
    default_model = "llama-3.3-70b-versatile"
    base_url = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self):
        super().__init__(name="groq", label="Groq", caps=("llm",), paid=True, unit="1k tokens",
                         fields=(CredField("api_key", "API key", "GROQ_API_KEY"),), docs="https://console.groq.com/docs")


class Pollinations(OpenAICompatible):
    """Free, keyless community endpoint. Good enough to run the studio without any paid account; weaker than Claude."""
    default_model = "openai"
    base_url = "https://text.pollinations.ai/openai"

    def __init__(self):
        super().__init__(name="pollinations_text", label="Pollinations (free text)", caps=("llm",), paid=False, unit="requests",
                         docs="https://pollinations.ai", notes="No key, no cost, rate-limited, smaller model. Used only when no paid LLM is configured.")

    def _tweak(self, body):
        body["max_tokens"] = max(6000, body["max_tokens"] * 3)  # reasoning tokens count against the limit
        body["reasoning_effort"] = "low"
        body.pop("temperature", None)

    def validate(self):
        try:
            self.complete("Reply with OK.", [{"role": "user", "content": "ping"}], max_tokens=20)
            return True, "Reachable"
        except ProviderError as e:
            return False, str(e)
