"""Typed LLM failures so HTTP and fallback adapters do not sniff message text."""


class LLMError(RuntimeError):
    """Cloud model failed; may be mapped to HTTP 502."""


class LLMTimeoutError(LLMError):
    """Cloud model exceeded the voice-turn deadline; maps to HTTP 504."""


class LLMUnavailableError(LLMError):
    """Cloud model empty, saturated, or temporarily down; retryable."""


class LLMQuotaError(LLMError):
    """Per-model quota or retired model id; try the next Flash in the cascade."""
