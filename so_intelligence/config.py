import logging
from textwrap import dedent
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

DEFAULT_TAGS: List[str] = [
    "cloudspanner",
    "alloydb",
    "google-cloud-storage",
    "cloudsql",
    "memorystore-redis",
    "memorystore-valkey",
    "google-cloud-bigtable",
    "google-cloud-firestore",
]


class AgentConfig(BaseSettings):
    so_api_token: str = Field("", env="SO_API_TOKEN")
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:70b"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_temperature: float = 0.0
    ollama_timeout: int = 120
    ollama_max_retries: int = 3
    default_tags: List[str] = DEFAULT_TAGS
    date_range_days: int = 30
    min_answer_score: int = 5
    confidence_threshold: float = 0.60
    db_path: str = "so_intelligence.db"
    cache_ttl_days: int = 90
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra='ignore'
    )

    def __init__(self, **values):
        super().__init__(**values)
        self._print_startup_validation_summary()

    def _print_startup_validation_summary(self) -> None:
        token_status = "FOUND" if self.so_api_token else "MISSING"
        summary = dedent(
            f"""
            AgentConfig loaded successfully.
            -------------------------------
            SO API token: {token_status}
            Ollama base URL: {self.ollama_base_url}
            Ollama model: {self.ollama_model}
            Ollama embed model: {self.ollama_embed_model}
            Ollama temperature: {self.ollama_temperature}
            Ollama timeout: {self.ollama_timeout}s
            Ollama max retries: {self.ollama_max_retries}
            Database path: {self.db_path}
            Cache TTL days: {self.cache_ttl_days}
            Confidence threshold: {self.confidence_threshold}
            Default tags: {', '.join(self.default_tags)}
            Log level: {self.log_level}
            """
        ).strip()
        print(summary)
        logger.debug(summary)


config = AgentConfig()
