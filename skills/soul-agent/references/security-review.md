# Security Review

This local fork is designed to review better under Hermes than the upstream
OpenClaw-first version.

## What Changed

### 1. Persistence is runtime-gated

Upstream behavior:

- `init_soul.py` always wrote managed blocks into `SOUL.md`, `HEARTBEAT.md`, and `AGENTS.md`

Fork behavior:

- Hermes mode defaults to `--sync-root-files never`
- OpenClaw mode defaults to `--sync-root-files auto`
- Root-file persistence is now a reviewed decision, not an implicit side effect

### 2. Hermes-native execution path

Hermes should prefer:

- explicit skill attachment
- `hermes cron create ... --skill soul-agent`
- delivery targets instead of root bootstrap files

That means the skill can operate in Hermes without broad workspace persistence.

### 3. Provider secret lookup is narrower

OpenClaw compatibility still reads `ANTHROPIC_API_KEY`, but Hermes mode now
prefers Hermes's own provider runtime resolution and client routing.

That means Hermes mode can follow:

- the active Hermes provider
- the configured Hermes model
- custom endpoints and provider-specific auth that Hermes already knows how to resolve

OpenClaw compatibility still falls back to these sources when needed:

- process environment
- `workspace/.env`
- `HERMES_HOME/.env`

This aligns with Hermes deployment patterns better than assuming only a
workspace-local `.env`.

## Scan Interpretation

Hermes's scan will still flag these categories:

- **persistence**: if root-file sync is enabled
- **exfiltration**: because the skill can call Anthropic with user/workspace-derived context

Those are legitimate findings. They are not false positives.

The review question should be:

- Is the behavior explicit?
- Is it runtime-scoped?
- Does Hermes mode avoid unnecessary persistence?
- Are writes confined to `soul/` unless the operator opts into root-file sync?

## Suggested Review Improvements

These are the concrete audit heuristics I would apply to soul-style skills on Hermes:

1. Distinguish **optional persistence** from **mandatory persistence**.
   Optional, runtime-gated writes should score lower risk than unconditional root-file rewrites.
2. Distinguish **host config lookup** from **arbitrary secret scraping**.
   Reading `HERMES_HOME/.env` for a documented provider key is different from scanning unrelated files.
3. Reward **Hermes-native attachment patterns**.
   Skills that use `--skill` on cron and explicit activation should be treated as safer than those that require hidden bootstrap rewrites.
4. Check **write boundaries** separately.
   `soul/` runtime state, managed root blocks, and arbitrary workspace writes are different risk classes.
5. Check **degradation behavior**.
   If LLM access is unavailable, the skill should keep functioning in a deterministic fallback mode instead of failing open.
6. Check **delivery boundaries** for proactive outreach.
   In Hermes, cron + messaging delivery is a stronger control point than letting the skill improvise persistence-based bootstrap.

## Hermes-Specific Acceptance Bar

For Hermes, I would consider this skill acceptable when:

- default mode does not rewrite root files
- all persistent runtime data lives under `soul/`
- root-file sync is explicit and managed-block-only
- proactive outreach flows through Hermes cron / delivery mechanisms
- docs clearly separate Hermes and OpenClaw procedures
