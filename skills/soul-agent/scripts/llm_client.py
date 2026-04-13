#!/usr/bin/env python3
"""
LLM client for soul-agent.

Runtime behavior:
- Hermes: reuse Hermes provider resolution and model routing
- OpenClaw: keep the original Anthropic-first logic for now

Model resolution priority:
1. SOUL_LLM_MODEL
2. soul/profile/base.json -> llm_model
3. Hermes config.yaml model.default (Hermes runtime only)
4. Provider default model (Hermes runtime only)
5. claude-haiku-4-5-20251001

Provider resolution priority (Hermes runtime):
1. SOUL_LLM_PROVIDER
2. soul/profile/base.json -> llm_provider
3. active Hermes provider/runtime resolution

API key resolution (OpenClaw compatibility path):
1. ANTHROPIC_API_KEY env var
2. workspace/.env
3. HERMES_HOME/.env
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from runtime_compat import detect_runtime, env_file_candidates

# Original upstream defaults remain for OpenClaw compatibility.
KNOWN_MODELS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-6",
}
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


class LLMClient:
    def __init__(self, workspace: Optional[str] = None, runtime: str = "auto"):
        self.workspace = Path(workspace) if workspace else Path(".")
        self.runtime = detect_runtime(runtime)
        self.provider = ""
        self.model = ""
        self.api_key = None
        self.base_url = ""
        self.api_mode = "chat_completions"
        self._client: Any = None
        self._runtime_info: Optional[dict[str, Any]] = None

        if self.runtime == "hermes":
            self._initialize_hermes_runtime()
        else:
            self.api_key = self._resolve_api_key_openclaw()
            self.model = self._resolve_model_openclaw()

    def _load_profile_config(self) -> dict[str, Any]:
        candidate = self.workspace / "soul" / "profile" / "base.json"
        if not candidate.exists():
            return {}
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _resolve_profile_value(self, key: str) -> str:
        profile = self._load_profile_config()
        value = profile.get(key)
        return str(value or "").strip()

    def _resolve_provider_override(self) -> str:
        env_provider = os.environ.get("SOUL_LLM_PROVIDER", "").strip()
        if env_provider:
            return env_provider
        return self._resolve_profile_value("llm_provider")

    def _load_hermes_model_config(self) -> dict[str, Any]:
        try:
            from hermes_cli.config import load_config

            cfg = load_config()
        except Exception:
            return {}

        model_cfg = cfg.get("model", {})
        if isinstance(model_cfg, dict):
            return model_cfg
        if isinstance(model_cfg, str) and model_cfg.strip():
            return {"default": model_cfg.strip()}
        return {}

    def _resolve_model_openclaw(self) -> str:
        env_model = os.environ.get("SOUL_LLM_MODEL", "").strip()
        if env_model:
            return env_model

        profile_model = self._resolve_profile_value("llm_model")
        if profile_model:
            return profile_model

        return DEFAULT_MODEL

    def _resolve_model_hermes(self, provider: str) -> str:
        env_model = os.environ.get("SOUL_LLM_MODEL", "").strip()
        if env_model:
            return env_model

        profile_model = self._resolve_profile_value("llm_model")
        if profile_model:
            return profile_model

        model_cfg = self._load_hermes_model_config()
        configured = str(model_cfg.get("default") or model_cfg.get("model") or "").strip()
        if configured:
            return configured

        try:
            from hermes_cli.models import get_default_model_for_provider

            fallback = get_default_model_for_provider(provider)
            if fallback:
                return fallback
        except Exception:
            pass

        return DEFAULT_MODEL

    def _resolve_api_key_openclaw(self) -> Optional[str]:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if key:
            return key

        for env_file in env_file_candidates(self.workspace):
            if not env_file.exists():
                continue
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        return None

    def _initialize_hermes_runtime(self) -> None:
        try:
            from hermes_cli.runtime_provider import (
                format_runtime_provider_error,
                resolve_runtime_provider,
            )

            explicit_provider = self._resolve_provider_override() or None
            explicit_base_url = os.environ.get("SOUL_LLM_BASE_URL", "").strip() or None
            explicit_api_key = os.environ.get("SOUL_LLM_API_KEY", "").strip() or None

            runtime = resolve_runtime_provider(
                requested=explicit_provider,
                explicit_api_key=explicit_api_key,
                explicit_base_url=explicit_base_url,
            )
            provider = str(runtime.get("provider") or "").strip() or "openrouter"
            model = self._resolve_model_hermes(provider)

            self._runtime_info = dict(runtime)
            self.provider = provider
            self.model = model
            self.api_key = str(runtime.get("api_key") or "").strip() or None
            self.base_url = str(runtime.get("base_url") or "").strip()
            self.api_mode = str(runtime.get("api_mode") or "chat_completions").strip()
        except Exception as exc:
            self._runtime_info = {
                "error": str(exc),
            }
            self.provider = self._resolve_provider_override() or "auto"
            self.model = self._resolve_model_openclaw()
            self.api_key = None
            self.base_url = ""
            self.api_mode = "chat_completions"
            try:
                self._runtime_info["error_message"] = format_runtime_provider_error(exc)  # type: ignore[name-defined]
            except Exception:
                pass

    def _get_openclaw_client(self):
        if self._client is not None:
            return self._client
        if not self.api_key:
            return None
        try:
            import anthropic

            self._client = anthropic.Anthropic(api_key=self.api_key)
            return self._client
        except ImportError:
            return None

    def _get_hermes_client(self):
        if self._client is not None:
            return self._client

        try:
            from agent.auxiliary_client import resolve_provider_client
        except Exception:
            return None

        if not self.provider:
            return None

        client, resolved_model = resolve_provider_client(
            self.provider,
            model=self.model,
            explicit_base_url=self.base_url or None,
            explicit_api_key=self.api_key or None,
            api_mode=self.api_mode or None,
        )
        if client is None:
            return None
        if resolved_model:
            self.model = resolved_model
        self._client = client
        return self._client

    def _get_client(self):
        if self.runtime == "hermes":
            return self._get_hermes_client()
        return self._get_openclaw_client()

    def available(self) -> bool:
        return self._get_client() is not None

    def _generate_via_hermes(self, prompt: str, max_tokens: int = 300, system: Optional[str] = None) -> Optional[str]:
        try:
            from agent.auxiliary_client import call_llm
        except Exception:
            return None

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = call_llm(
                provider=self.provider,
                model=self.model,
                base_url=self.base_url or None,
                api_key=self.api_key or None,
                messages=messages,
                max_tokens=max_tokens,
            )
        except Exception:
            return None

        try:
            return response.choices[0].message.content.strip()
        except Exception:
            return None

    def _generate_via_openclaw(self, prompt: str, max_tokens: int = 300, system: Optional[str] = None) -> Optional[str]:
        client = self._get_openclaw_client()
        if not client:
            return None

        kwargs = dict(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        if system:
            kwargs["system"] = system

        try:
            response = client.messages.create(**kwargs)
            return response.content[0].text.strip()
        except Exception:
            return None

    def generate(self, prompt: str, max_tokens: int = 300, system: Optional[str] = None) -> Optional[str]:
        """Generate text. Returns None on any failure."""
        if self.runtime == "hermes":
            return self._generate_via_hermes(prompt, max_tokens=max_tokens, system=system)
        return self._generate_via_openclaw(prompt, max_tokens=max_tokens, system=system)

    def generate_json(self, prompt: str, max_tokens: int = 400, system: Optional[str] = None) -> Optional[dict]:
        """Generate and parse JSON. Returns None on failure."""
        text = self.generate(prompt, max_tokens=max_tokens, system=system)
        if not text:
            return None
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                return parsed if isinstance(parsed, dict) else None
        except Exception:
            pass
        return None
