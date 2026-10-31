from functools import lru_cache  # Cache the Settings object so .env is read only once
from typing import Literal  # Literal restricts a string field to a fixed set of values

from pydantic import SecretStr  # A string wrapper that hides its value when printed
from pydantic_settings import BaseSettings, SettingsConfigDict  # Env-var-driven config models


class Settings(BaseSettings):
    """All configuration for Brightdesk. Every field can be set with an env var of the same name."""

    # Read variables from a local .env file (if present); ignore unknown variables.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Which LLM backend to use -------------------------------------------------
    llm_provider: Literal["anthropic", "openai", "local", "fake"] = "anthropic"

    # --- Anthropic (primary provider in this book) --------------------------------
    anthropic_api_key: SecretStr | None = None  # Read from ANTHROPIC_API_KEY
    anthropic_model: str = "claude-haiku-5-5"  # Small, fast, cheap default model

    # --- OpenAI (secondary provider) ----------------------------------------------
    openai_api_key: SecretStr | None = None  # Read from OPENAI_API_KEY
    openai_model: str = "gpt-6.1-sol"  # Model IDs change often: check the provider's models page

    # --- Local / open-weight models via any OpenAI-compatible server (e.g. Ollama) --
    local_base_url: str = "http://localhost:11434/v1"  # Ollama's OpenAI-compatible endpoint
    local_model: str = "llama3.2"  # Any model you have pulled locally

    # --- Reliability knobs shared by all providers --------------------------------
    llm_timeout_s: float = 60.0  # Give up on a single request after this many seconds
    llm_max_retries: int = 2  # The SDKs retry 429/5xx errors with backoff this many times

    # --- Retrieval -------------------------------------------------------------------
    embedding_backend: Literal["hash", "sentence-transformers", "openai"] = "hash"
    embedding_model: str = "BAAI/bge-small-en-v1.5"  # Used by the sentence-transformers backend

    # --- Infrastructure --------------------------------------------------------------
    database_url: str | None = None  # e.g. postgresql://user:pass@localhost:5432/brightdesk
    log_level: str = "INFO"

@lru_cache  # The first call builds Settings; later calls return the same object
def get_settings() -> Settings:
    """Return the process-wide settings object."""
    return Settings()