#!/usr/bin/env python3
"""Runtime compatibility helpers for soul-agent."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeProfile:
    name: str
    display_name: str
    default_sync_root_files: bool
    skill_root_hint: str
    root_files_are_primary_bootstrap: bool


RUNTIME_PROFILES = {
    "hermes": RuntimeProfile(
        name="hermes",
        display_name="Hermes",
        default_sync_root_files=False,
        skill_root_hint='${HERMES_HOME:-$HOME/.hermes}/skills/soul-agent',
        root_files_are_primary_bootstrap=False,
    ),
    "openclaw": RuntimeProfile(
        name="openclaw",
        display_name="OpenClaw",
        default_sync_root_files=True,
        skill_root_hint="skills/soul-agent",
        root_files_are_primary_bootstrap=True,
    ),
}


def detect_runtime(explicit: str = "auto") -> str:
    if explicit in RUNTIME_PROFILES:
        return explicit

    if os.environ.get("HERMES_HOME"):
        return "hermes"
    if os.environ.get("OPENCLAW_HOME") or os.environ.get("CLAW_HOME"):
        return "openclaw"

    hermes_bin = shutil.which("hermes")
    openclaw_bin = shutil.which("openclaw")
    if hermes_bin and not openclaw_bin:
        return "hermes"
    if openclaw_bin and not hermes_bin:
        return "openclaw"

    # Default to Hermes because the local fork is intended to be Hermes-native.
    return "hermes"


def runtime_profile(runtime: str) -> RuntimeProfile:
    return RUNTIME_PROFILES[runtime]


def should_sync_root_files(runtime: str, policy: str = "auto") -> bool:
    if policy == "always":
        return True
    if policy == "never":
        return False
    return runtime_profile(runtime).default_sync_root_files


def skill_root_hint(runtime: str) -> str:
    return runtime_profile(runtime).skill_root_hint


def render_script_command(script_name: str, runtime: str, workspace_expr: str = ".") -> str:
    if runtime == "hermes":
        return (
            f'python "{skill_root_hint(runtime)}/scripts/{script_name}" '
            f'--workspace {workspace_expr}'
        )
    return f"python {skill_root_hint(runtime)}/scripts/{script_name} --workspace {workspace_expr}"


def env_file_candidates(workspace: Path) -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()

    def _append(path: Path | None) -> None:
        if not path:
            return
        resolved = path.expanduser()
        if resolved in seen:
            return
        seen.add(resolved)
        candidates.append(resolved)

    _append(workspace / ".env")

    hermes_home = os.environ.get("HERMES_HOME", "").strip()
    if hermes_home:
        _append(Path(hermes_home) / ".env")
    else:
        home = os.environ.get("HOME", "").strip()
        if home:
            _append(Path(home) / ".hermes" / ".env")

    return candidates


def managed_block_templates(runtime: str) -> tuple[str, str, str]:
    l1_cmd = render_script_command("heartbeat_check.py", runtime)
    l2_cmd = render_script_command("heartbeat_engine.py", runtime)

    if runtime == "openclaw":
        soul_block = f"""
Runtime should read workspace `soul/` first:
`soul/INDEX.md` -> `soul/profile/*` -> `soul/state/state.json`.
Default scope is `main`; subagents are opt-in and must be enabled by the user.

**Initialization check** (run on every session start):
- If `soul/profile/base.json` is missing or `soul/` does not exist:
  - Ask the user the setup questions (name, age, city, occupation, hobbies, life profile, preferred LLM model)
  - Run init script non-interactively with collected answers
  - Do NOT ask the user to run Python commands themselves
- If `soul/profile/base.json` exists: load it and proceed normally
"""
        heartbeat_block = f"""
This block is for `main` during heartbeat polls.

**Heartbeat flow:**
1. Run L1 check (no LLM): `{l1_cmd} --json`
   - Exit 1 -> sleeping, skip
   - Exit 2 -> state fresh, skip
   - Exit 0 -> run L2
2. Run L2 engine: `{l2_cmd} --json`
3. Read result JSON:
   - `shouldOutreach: true` -> send the `outreachContent` message to user
   - Otherwise -> `HEARTBEAT_OK`
"""
        agents_block = """
`soul-agent` runtime contract (default: `main`):
1. Follow OpenClaw's root bootstrap files (`SOUL.md`, `HEARTBEAT.md`, `AGENTS.md`).
2. Load `soul/INDEX.md` -> `soul/profile/*` -> `soul/state/state.json`.
3. During heartbeat polls, follow the flow in HEARTBEAT.md.
4. Agent drives initialization; never ask the user to run Python commands.
5. Subagents are not enabled by default; user must opt in.
"""
        return soul_block, heartbeat_block, agents_block

    soul_block = """
Runtime should read workspace `soul/` first:
`soul/INDEX.md` -> `soul/profile/*` -> `soul/state/state.json`.
In Hermes, root-file sync is optional; prefer attaching the `soul-agent` skill
explicitly to chats or cron jobs and keep root files as an opt-in bootstrap.
"""
    heartbeat_block = f"""
This block is for Hermes heartbeat-style automation when root-file sync is explicitly enabled.

**Heartbeat flow:**
1. Run L1 check (no LLM): `{l1_cmd} --json`
   - Exit 1 -> sleeping, skip
   - Exit 2 -> state fresh, skip
   - Exit 0 -> run L2
2. Run L2 engine: `{l2_cmd} --json`
3. Read result JSON:
   - `shouldOutreach: true` -> send the `outreachContent` message to user
   - Otherwise -> `HEARTBEAT_OK`

Prefer Hermes cron jobs with `--skill soul-agent` over root-file bootstrap.
"""
    agents_block = """
`soul-agent` runtime contract (Hermes mode):
1. Prefer explicit skill attachment (`hermes -s soul-agent` or `hermes cron create ... --skill soul-agent`).
2. Treat `soul/INDEX.md` and `soul/state/state.json` as the runtime source of truth.
3. Root-file sync is optional and should be enabled only when the operator wants persistent bootstrap hints in `SOUL.md`, `HEARTBEAT.md`, and `AGENTS.md`.
4. Agent drives initialization; never ask the user to run Python commands.
5. Subagents are not enabled by default; user must opt in.
"""
    return soul_block, heartbeat_block, agents_block
