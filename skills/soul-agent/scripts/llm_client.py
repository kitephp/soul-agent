#!/usr/bin/env python3
"""
LLM Client for Soul Agent

模型解析优先级（从高到低）：
1. 环境变量 SOUL_LLM_MODEL（脚本覆盖用，一般不设置）
2. soul/profile/base.json → llm_model（init 时由 agent 配置）
3. 默认：claude-haiku-4-5-20251001

API Key：环境变量 ANTHROPIC_API_KEY 或 workspace/.env
"""

import json
import os
import re
from pathlib import Path
from typing import Optional

# 已知可用模型，供 init 向导展示
KNOWN_MODELS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-6",
}
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


class LLMClient:
    def __init__(self, workspace: Optional[str] = None):
        self.api_key = self._resolve_api_key(workspace)
        self.model = self._resolve_model(workspace)
        self._client = None

    def _resolve_api_key(self, workspace: Optional[str]) -> Optional[str]:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if key:
            return key
        if workspace:
            env_file = Path(workspace) / ".env"
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("ANTHROPIC_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        return None

    def _resolve_model(self, workspace: Optional[str]) -> str:
        # 1. 环境变量（最高优先，方便 CI/脚本覆盖）
        env_model = os.environ.get("SOUL_LLM_MODEL", "").strip()
        if env_model:
            return env_model

        # 2. soul 配置文件
        if workspace:
            for candidate in [
                Path(workspace) / "soul" / "profile" / "base.json",
            ]:
                if candidate.exists():
                    try:
                        p = json.loads(candidate.read_text(encoding="utf-8"))
                        m = p.get("llm_model", "").strip()
                        if m:
                            return m
                    except Exception:
                        pass

        return DEFAULT_MODEL

    def _get_client(self):
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

    def available(self) -> bool:
        return bool(self.api_key) and self._get_client() is not None

    def generate(self, prompt: str, max_tokens: int = 300, system: Optional[str] = None) -> Optional[str]:
        """Generate text. Returns None on any failure."""
        client = self._get_client()
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

    def generate_json(self, prompt: str, max_tokens: int = 400, system: Optional[str] = None) -> Optional[dict]:
        """Generate and parse JSON. Returns None on failure."""
        text = self.generate(prompt, max_tokens=max_tokens, system=system)
        if not text:
            return None
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return None
