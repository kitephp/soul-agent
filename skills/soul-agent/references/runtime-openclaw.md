# OpenClaw Runtime

Use this mode when `soul-agent` runs inside an OpenClaw-style workspace.

## Default Strategy

OpenClaw workflows often rely on workspace bootstrap files. In that environment,
managed blocks in `SOUL.md`, `HEARTBEAT.md`, and `AGENTS.md` are part of the
normal runtime contract.

Recommended initialization:

```bash
python scripts/init_soul.py \
  --workspace . \
  --runtime openclaw \
  --sync-root-files auto \
  --non-interactive \
  --profile-json '{"display_name":"<name>","city":"<city>","life_profile":"freelancer"}'
```

## Cron Note

The original upstream examples used `openclaw cron add`. Keep using the host's
native cron interface when running under OpenClaw. Do not copy Hermes cron
commands into an OpenClaw workspace verbatim.

## Compatibility Goal

The local fork keeps OpenClaw support intact, but the implementation now makes
the persistence surface explicit instead of assuming every runtime needs the same
bootstrap writes.
