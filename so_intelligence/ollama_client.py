import json
import logging
import time
from typing import Any, Dict, List, Optional

import httpx
import ollama
from pydantic import ValidationError

from .config import AgentConfig

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "You are a data analysis assistant. You must only make claims that are directly supported by "
    "the data provided to you in this prompt. Never invent post IDs, vote counts, dates, or titles. "
    "If you are uncertain, say UNCERTAIN and explain why."
)


class OllamaConnectionError(Exception):
    pass


class OllamaJSONParseError(Exception):
    def __init__(self, raw_response: str, message: str) -> None:
        self.raw_response = raw_response
        super().__init__(message)


class OllamaClient:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = ollama.Client(
            host=self.config.ollama_base_url,
            timeout=self.config.ollama_timeout,
        )
        self._embeddings_cache: Dict[str, List[float]] = {}

    def _build_system_instruction(self, system: Optional[str]) -> str:
        if system:
            return f"{SYSTEM_INSTRUCTION}\n\n{system}"
        return SYSTEM_INSTRUCTION

    def _log_call(self, prompt: str, response_text: str, duration_ms: int) -> None:
        self.logger.info(
            "Ollama call finished: model=%s prompt_length=%d response_length=%d duration_ms=%d",
            self.config.ollama_model,
            len(prompt),
            len(response_text),
            duration_ms,
        )

    def _strip_markdown_fences(self, text: str) -> str:
        if "```" in text:
            # strip fenced code blocks, including ```json
            parts = text.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        return text.strip()

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        last_error: Optional[BaseException] = None
        for attempt in range(1, self.config.ollama_max_retries + 1):
            try:
                messages = [
                    {"role": "system", "content": self._build_system_instruction(system)},
                    {"role": "user", "content": prompt},
                ]
                start = time.perf_counter()
                response = self.client.chat(
                    model=self.config.ollama_model,
                    messages=messages,
                    stream=False,
                )
                duration_ms = int((time.perf_counter() - start) * 1000)
                result = response.message.content or ""
                result = result.strip()
                self._log_call(prompt, result, duration_ms)
                return result
            except (ConnectionError, httpx.TimeoutException) as exc:
                last_error = exc
                self.logger.warning(
                    "Ollama connection failure on attempt %d/%d: %s",
                    attempt,
                    self.config.ollama_max_retries,
                    exc,
                )
                if attempt == self.config.ollama_max_retries:
                    raise OllamaConnectionError(
                        f"Ollama is not responding at {self.config.ollama_base_url}. "
                        "Run 'ollama serve' to start the service."
                    ) from exc
            except Exception as exc:
                raise OllamaConnectionError(
                    f"Ollama generate failed: {exc}"
                ) from exc

        raise OllamaConnectionError(
            f"Ollama generate failed after {self.config.ollama_max_retries} attempts."
        )

    def generate_json(self, prompt: str, schema_hint: str, retry_count: int = 0) -> Dict[str, Any]:
        json_prompt = (
            f"{prompt}\n\nRespond ONLY with valid JSON matching this schema: {schema_hint}\n"
            "Do not include any text before or after the JSON object."
        )
        raw_response = self.generate(json_prompt)
        stripped = self._strip_markdown_fences(raw_response)

        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError as exc:
            if retry_count < 1:
                self.logger.warning("Ollama JSON parse failed; retrying once.")
                return self.generate_json(prompt, schema_hint, retry_count + 1)
            raise OllamaJSONParseError(raw_response, f"Ollama JSON parse failed: {exc}") from exc

        if not isinstance(parsed, dict):
            if retry_count < 1:
                self.logger.warning("Ollama JSON result was not an object; retrying once.")
                return self.generate_json(prompt, schema_hint, retry_count + 1)
            raise OllamaJSONParseError(
                raw_response,
                "Ollama returned JSON that is not an object.",
            )

        return parsed

    def embed(self, text: str) -> List[float]:
        if text in self._embeddings_cache:
            return self._embeddings_cache[text]

        start = time.perf_counter()
        response = self.client.embeddings(
            model=self.config.ollama_embed_model,
            prompt=text,
        )
        duration_ms = int((time.perf_counter() - start) * 1000)
        embedding_result = response.embeddings

        if not embedding_result:
            raise OllamaConnectionError("Ollama returned an empty embedding response.")

        embedding_vector = list(embedding_result[0]) if isinstance(embedding_result[0], (list, tuple)) else list(embedding_result)  # type: ignore[arg-type]
        self._embeddings_cache[text] = embedding_vector
        self.logger.info(
            "Ollama embed finished: model=%s prompt_length=%d embedding_length=%d duration_ms=%d",
            self.config.ollama_embed_model,
            len(text),
            len(embedding_vector),
            duration_ms,
        )
        return embedding_vector

    def ping(self) -> bool:
        try:
            self.client.list()
            return True
        except Exception as exc:
            self.logger.warning("Ollama ping failed: %s", exc)
            return False
