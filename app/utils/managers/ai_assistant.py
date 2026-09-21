"""
Generic AI prompting client.

Sole responsibility: send a prompt, get a structured response back, in a
provider-agnostic way. Knows nothing about penalties, tasks, or any domain
concept — prompt templates and result interpretation live in
``PenaltyEvaluator`` (penalty_evaluator.py).

Transport config comes from ``provider_config.yaml`` (base_url, default_model,
timeout, retries, api-key env var name). Provider exceptions are abstracted
into ``AssistantError`` so callers never touch SDK exception classes.

No per-request auth is attached beyond an optional ``OMNIROUTE_API_KEY``
Bearer token: OmniRoute combos carry their own provider connection auth
server-side, so a session id header is neither required nor sent.
"""
from pathlib import Path
import os
import json
import socket
import time
from urllib.parse import urlparse
from typing import Optional

import yaml
from openai import OpenAI, APIConnectionError, APITimeoutError, APIStatusError, APIError

from app.utils.logger import external_apis_logger
from app.config import assistant_config_folder
from app.utils.exceptions import AssistantError


def _extract_json(content: str) -> dict:
    """Parse a JSON object out of an assistant reply.

    Combo providers wrap responses inconsistently (bare JSON vs markdown code
    fences, occasional trailing prose), so fall back to slicing the first
    {...} block before raising.
    """
    try:
        result = json.loads(content)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        result = json.loads(content[start:end + 1])
        if isinstance(result, dict):
            return result
    raise ValueError()


class AIAssistant:
    """Send prompts to a configured LLM provider and return parsed JSON."""

    def __init__(self, config_path: str = "provider_config.yaml"):
        self.logger = external_apis_logger
        self.config = self._load_config(Path(assistant_config_folder) / config_path)
        self.timeout = self._resolve_timeout()
        self.client = self._build_client()

    def _resolve_timeout(self) -> float:
        env_timeout = os.getenv("OMNIROUTE_TIMEOUT")
        if env_timeout is not None:
            try:
                return float(env_timeout)
            except (TypeError, ValueError):
                self.logger.warning("Invalid OMNIROUTE_TIMEOUT=%r; ignoring", env_timeout)
        return float(self.config.get("timeout", 90.0))

    def _load_config(self, config_path: Path) -> dict:
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
            return config or {}
        except Exception as e:
            self.logger.error("Provider config load failed: %s", str(e))
            raise AssistantError("Provider configuration loading failed") from e

    def _build_client(self):
        api_key = os.getenv(self.config.get("api_key_env", ""), None) or "not-needed"
        base_url = os.getenv("OMNIROUTE_URL") or self.config.get("base_url", "http://127.0.0.1:20128/v1")
        try:
            return OpenAI(
                base_url=base_url,
                api_key=api_key,
                timeout=self.timeout,
                max_retries=0,
            )
        except Exception as e:
            self.logger.error("Failed to build AI client: %s", str(e))
            raise AssistantError("Failed to configure AI provider") from e

    def health_check(self) -> tuple:
        """Check provider reachability without issuing a chat request.

        Opens a bounded TCP connection to the configured base_url host:port.
        Returns (ok: bool, latency_ms: int, detail: str). Connection-refused
        fails in milliseconds; black-holed hosts hit the configured timeout.
        """
        base_url = os.getenv("OMNIROUTE_URL") or self.config.get("base_url", "http://127.0.0.1:20128/v1")
        try:
            parsed = urlparse(base_url)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
        except Exception as e:
            self.logger.warning("Health check could not parse base_url: %s", e)
            return False, 0, f"Bad base_url: {e}"

        started = time.monotonic()
        try:
            with socket.create_connection((host, port), timeout=self.timeout):
                latency_ms = int((time.monotonic() - started) * 1000)
                return True, latency_ms, f"{host}:{port} reachable"
        except OSError as e:
            latency_ms = int((time.monotonic() - started) * 1000)
            self.logger.warning("Health check failed (%s:%s): %s", host, port, e)
            return False, latency_ms, f"{host}:{port} unreachable: {e}"

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = None,
        response_format: str = "json_object",
        temperature: float = 0.3,
        retries: int = None,
    ) -> Optional[dict]:
        """Send the prompt and return the parsed JSON dict.

        Retries transient transport failures up to ``retries`` times. Returns
        None if the provider stays unreachable; raises ``AssistantError`` only
        for unrecoverable/config errors (bad request, provider-level failures,
        malformed JSON response).
        """
        if retries is None:
            retries = int(self.config.get("retries", 3))
        model = model or os.getenv("OMNIROUTE_MODEL") or self.config.get("default_model")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        self.logger.debug("LLM request - model=%s", model)

        last_error = None
        decode_error = None
        for attempt in range(max(1, retries)):
            if attempt:
                time.sleep(0.5)
            try:
                response = self.client.chat.completions.create(
                    messages=messages,
                    model=model,
                    response_format={"type": response_format},
                    temperature=temperature,
                )
                content = response.choices[0].message.content
                if not content:
                    last_error = None
                    self.logger.warning("LLM returned empty content (model=%s, attempt=%s)", model, attempt + 1)
                    continue
                try:
                    result = _extract_json(content)
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    decode_error = AssistantError(
                        message="Invalid LLM response format",
                        status_code=502,
                        model=model,
                    )
                    last_error = decode_error
                    self.logger.warning("LLM response was not JSON (model=%s, attempt=%s): %s", model, attempt + 1, e)
                    continue
                if not isinstance(result, dict):
                    last_error = None
                    self.logger.warning("LLM JSON was not a dict (model=%s)", model)
                    return None
                return result

            except (APIConnectionError, APITimeoutError) as e:
                last_error = e
                self.logger.warning("LLM connection issue (model=%s): %s", model, e)
                continue
            except APIStatusError as e:
                if e.status_code == 429 or e.status_code >= 500:
                    last_error = e
                    self.logger.warning("LLM transient status %s (model=%s): %s", e.status_code, model, e)
                    continue
                error = AssistantError(
                    message=f"LLM API request failed: {e}",
                    status_code=e.status_code,
                )
                self.logger.error("LLM API request failed: %s", e)
                raise error
            except APIError as e:
                error = AssistantError(
                    message=f"LLM API request failed: {e}",
                    status_code=getattr(e, "status_code", 500),
                )
                self.logger.error("LLM API request failed: %s", e)
                raise error

        self.logger.error("LLM unreachable after %s attempts (model=%s)", retries, model)
        if decode_error is not None:
            raise decode_error
        return None