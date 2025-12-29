"""Model clients for OpenAI and Ollama via OpenAI-compatible API."""

from langchain_openai import ChatOpenAI


def get_openai_client(
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    streaming: bool = True,
) -> ChatOpenAI:
    """Get OpenAI client.
    
    Requires OPENAI_API_KEY environment variable to be set.
    """
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        streaming=streaming,
    )


def get_ollama_client(
    model: str = "llama3.2",
    temperature: float = 0.7,
    streaming: bool = True,
    base_url: str = "http://localhost:11434/v1",
) -> ChatOpenAI:
    """Get Ollama client via OpenAI-compatible API."""
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        streaming=streaming,
        base_url=base_url,
        api_key="ollama",  # Ollama doesn't require a real API key
    )


def get_model_client(
    provider: str = "openai",
    model: str | None = None,
    temperature: float = 0.7,
    streaming: bool = True,
) -> ChatOpenAI:
    """Get model client based on provider.
    
    For now, defaults to OpenAI. Routing logic can be expanded later.
    """
    if provider == "ollama":
        return get_ollama_client(
            model=model or "llama3.2",
            temperature=temperature,
            streaming=streaming,
        )
    # Default to OpenAI
    return get_openai_client(
        model=model or "gpt-4o-mini",
        temperature=temperature,
        streaming=streaming,
    )
