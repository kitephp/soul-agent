---
name: soul-agent
description: "Dual-runtime companion skill for Hermes and OpenClaw. Adds heartbeat-driven life logs, moods, relationship evolution, daily planning, and independent memory. Use when building a persistent digital companion or automating companion-style outreach."
metadata:
  hermes:
    tags: [companion, heartbeat, cron, memory, weixin, autonomous]
---

# soul-agent

Build a persistent companion runtime with:

- heartbeat-driven life logs
- daily planning + reflection
- mood and energy updates
- relationship evolution
- independent long-term memory under `soul/`

The local fork supports **Hermes** and **OpenClaw** explicitly.

## Runtime Choice

Use the runtime that matches the host agent:

- **Hermes**: Prefer explicit skill attachment such as `hermes -s soul-agent` or `hermes cron create ... --skill soul-agent`.
  Root-file sync is **optional** and should stay off unless the operator explicitly wants managed blocks written into `SOUL.md`, `HEARTBEAT.md`, and `AGENTS.md`.
- **OpenClaw**: Root-file sync is usually part of the bootstrap contract, so it defaults on.

Runtime-specific references:

- `references/runtime-hermes.md`
- `references/runtime-openclaw.md`
- `references/security-review.md`
- `references/managed-blocks.md`

## Core Workflow

When `soul/` is missing or `soul/profile/base.json` does not exist:

1. Ask the user for companion profile fields:
   `display_name`, `age`, `city`, `occupation`, `hobbies`, `life_profile`, `llm_model`
2. Initialize with `scripts/init_soul.py`
3. Add heartbeat / distillation automation for the host runtime

### Initialization Command

Use `--runtime hermes` or `--runtime openclaw` explicitly when you know the host.

```bash
python scripts/init_soul.py \
  --workspace <workspace-root> \
  --runtime <hermes|openclaw> \
  --sync-root-files <auto|always|never> \
  --non-interactive \
  --profile-json '{
    "display_name": "<name>",
    "age": "<age>",
    "city": "<city>",
    "occupation": "<occupation>",
    "hobbies": "<hobbies>",
    "life_profile": "<profile>",
    "llm_model": "<model-id>"
  }'
```

Hermes default:

- `--runtime hermes`
- `--sync-root-files never` unless the operator explicitly wants root-file bootstrap
- leave `llm_model` empty to follow Hermes's current configured model/provider

Advanced Hermes override:

- set `SOUL_LLM_PROVIDER` to pin a specific Hermes provider
- set `SOUL_LLM_MODEL` to pin a specific model
- or write `llm_provider` / `llm_model` into `soul/profile/base.json`

OpenClaw default:

- `--runtime openclaw`
- `--sync-root-files auto`

### Heartbeat Scripts

```bash
python scripts/heartbeat_check.py --workspace <workspace-root> --json
python scripts/heartbeat_engine.py --workspace <workspace-root> --json
python scripts/update_state.py --workspace <workspace-root> --action interaction --json
python scripts/distill_life_log.py --workspace <workspace-root> --archive
```

## Hermes Guidance

Hermes is the better fit for this skill when you want:

- chat-platform delivery such as Weixin / Telegram / Discord
- cron jobs that attach the skill explicitly
- optional persistence instead of mandatory root-file rewrites
- cleaner review boundaries around workspace writes

Use `references/runtime-hermes.md` when configuring Hermes jobs or delivery targets.

## OpenClaw Guidance

Use `references/runtime-openclaw.md` when you need compatibility with an older OpenClaw workspace or when root bootstrap files are part of the expected contract.

## Safety Model

- Always write runtime state under `soul/`
- Treat root-file sync as a separate persistence surface
- In Hermes mode, prefer **no root sync by default**
- If root sync is enabled, edit only managed blocks
- LLM usage should degrade gracefully when Anthropic is unavailable

The review checklist and audit recommendations live in `references/security-review.md`.
