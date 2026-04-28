# Managed Block Policy

`soul-agent` updates only managed blocks in:
- `SOUL.md`
- `HEARTBEAT.md`
- `AGENTS.md`

Runtime policy:

- **Hermes**: root-file sync is optional and should usually stay off
- **OpenClaw**: root-file sync is usually part of the bootstrap contract

## Block Markers

```
<!-- SOUL-AGENT:SOUL-START -->
...block content...
<!-- SOUL-AGENT:SOUL-END -->

<!-- SOUL-AGENT:HEARTBEAT-START -->
...block content...
<!-- SOUL-AGENT:HEARTBEAT-END -->

<!-- SOUL-AGENT:AGENTS-START -->
...block content...
<!-- SOUL-AGENT:AGENTS-END -->
```

## Rules

- If a block exists, replace only block content.
- If file exists without block, append block.
- If file does not exist, create it with block.
- Never modify user content outside managed blocks.

## Block Semantics

### SOUL.md

Runtime loading contract:

```
Runtime should read workspace `soul/` first:
`soul/INDEX.md` -> `soul/profile/*` -> `soul/state/state.json`.
Default scope is `main`; subagents are opt-in and must be enabled by the user.
If `soul/` is missing, use a minimal companion baseline and prompt to initialize `soul-agent`.
```

### HEARTBEAT.md

Heartbeat behavior:

```
This block is intended for `main` during heartbeat polls by default.
Heartbeat must read:
- `soul/state/state.json`
- `soul/profile/life.md`
- `soul/profile/schedule.md`

If no actionable item exists, return `HEARTBEAT_OK`.
```

### AGENTS.md

Runtime contract:

```
`soul-agent` runtime contract (default: `main`):
1. Follow Hermes's root context files (including `SOUL.md`, `AGENTS.md`, and `HEARTBEAT.md` during heartbeat runs).
2. Inside SOUL logic, load `soul/INDEX.md` and `soul/profile/*`.
3. During heartbeat polls, read `soul/state/state.json` and cadence rules.
4. Subagents are not enabled by default; user must opt in manually.
```

## Memory Loading

Agent should load memory at appropriate times:

| When | What to Read |
|------|--------------|
| Startup | `SOUL.md` and runtime-specific memory files |
| Heartbeat | `soul/state/state.json`, `soul/profile/schedule.md` |
| Recalling | `soul/memory/SOUL_MEMORY.md` (distilled) |
| Detail needed | `soul/log/life/YYYY-MM-DD.md` (raw) |

Do NOT load all memory at every startup - that wastes tokens. Load on-demand.
