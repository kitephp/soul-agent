---
name: soul-agent
description: "Initialize, repair, and maintain an OpenClaw-first soul runtime in a workspace. Use when you need a standard `soul/` directory, reusable companion profile templates, interactive bootstrap with defaults, and managed block sync for `SOUL.md`, `HEARTBEAT.md`, and `AGENTS.md`."
---

# soul-agent

Provide an OpenClaw-first soul package that is init-able, repairable, and extensible.

- Write runtime data into workspace `soul/`
- Default scope is `main`; subagents are opt-in and user-controlled

## Workflow

1. Diagnose first:
```bash
python ./scripts/doctor_soul.py --workspace <workspace-root>
```

2. Auto mode (recommended):
```bash
python ./scripts/init_soul.py --workspace <workspace-root> --mode auto
```

3. Manual modes (optional):
```bash
python ./scripts/init_soul.py --workspace <workspace-root> --mode init
python ./scripts/init_soul.py --workspace <workspace-root> --mode repair --non-interactive
python ./scripts/init_soul.py --workspace <workspace-root> --mode migrate --non-interactive
```

## Initialization Behavior

- `--mode auto`:
  - `init` if `soul/` is missing
  - `migrate` if legacy `soul/skills` is detected
  - `repair` otherwise
- If `soul/` is missing and `--non-interactive` is not set, prompt for soul base fields.
- Every field accepts Enter for default.
- Print a default vs current diff summary.
- Generate `soul/profile/*`, `soul/state/*`, and `soul/log/*` from templates.
- Default policy is fill-missing-only; pass `--overwrite-existing` to overwrite existing files.
- Auto-sync managed blocks in:
  - `SOUL.md` (workspace-first runtime loading)
  - `HEARTBEAT.md` (heartbeat read contract)
  - `AGENTS.md` (main-default runtime contract)

## Template Sources

- Default profile: `assets/default-profile.json`
- Profile index template: `assets/templates/soul_INDEX.md`
- Profile templates: `assets/templates/profile/*`

## Safety Rules

- Edit managed blocks only; do not mutate user-owned content outside those blocks.
- Write only inside the current workspace and `soul/`.
- Do not maintain engineering notes; this skill only owns `soul/profile`, `soul/state`, and `soul/log`.

## References

- `references/soul-layout.md`
- `references/managed-blocks.md`
