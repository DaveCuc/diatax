class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass

class LLMAuthenticationError(LLMError):
    """Error when provider credentials are invalid."""
    pass

class LLMRateLimitError(LLMError):
    """Error when provider request limit is reached."""
    pass

class LLMNetworkError(LLMError):
    """Connection or timeout error with the AI provider."""
    pass

class LLMConfigError(LLMError):
    """Error when local configuration is missing or invalid."""
    pass

class LLMFormatError(LLMError):
    """Error when the LLM response format is invalid or cannot be parsed."""
    pass
