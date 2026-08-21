import os

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from app.utils.config import MAIN_OPENAI_LLM_MODEL, OPENAI_TEMPERATURE, SECONDARY_OPENAI_LLM_MODEL

PROVIDER = os.getenv("LLM_PROVIDER")

OPENAI_PROVIDER = "openai"

def get_llm(provider: str = None, model: str = None, **kwargs) -> BaseChatModel:
    """Factory that returns a configured chat model for any supported provider.

    If `provider` is omitted, the module-level `PROVIDER` environment value is used.
    """
    provider = provider or PROVIDER

    if provider == OPENAI_PROVIDER:
        temperature = kwargs.pop("temperature", OPENAI_TEMPERATURE)
        return ChatOpenAI(model=MAIN_OPENAI_LLM_MODEL, temperature=temperature, **kwargs)

    raise ValueError(f"Unknown provider: {provider}")


def get_secondary_llm(provider: str = None, model: str = None, **kwargs) -> BaseChatModel:
    """Factory that returns a configured secondary chat model for any supported provider.

    If `provider` is omitted, the module-level `PROVIDER` environment value is used.
    """
    provider = provider or PROVIDER

    if provider == OPENAI_PROVIDER:
        temperature = kwargs.pop("temperature", OPENAI_TEMPERATURE)
        return ChatOpenAI(model=SECONDARY_OPENAI_LLM_MODEL, temperature=temperature, **kwargs)

    raise ValueError(f"Unknown provider: {provider}")