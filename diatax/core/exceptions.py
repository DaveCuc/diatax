class LLMError(Exception):
    """Excepción base para errores relacionados con el LLM."""
    pass

class LLMAuthenticationError(LLMError):
    """Error cuando las credenciales del proveedor son inválidas."""
    pass

class LLMRateLimitError(LLMError):
    """Error cuando se alcanza el límite de peticiones del proveedor."""
    pass

class LLMNetworkError(LLMError):
    """Error de conexión o timeout con el proveedor de IA."""
    pass

class LLMConfigError(LLMError):
    """Error cuando la configuración local es inexistente o inválida."""
    pass
