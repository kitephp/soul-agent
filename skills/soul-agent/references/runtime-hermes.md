# Hermes Runtime

Use this mode when `soul-agent` runs under Hermes.

## Default Strategy

Hermes already has strong primitives for:

- explicit skill attachment with `-s soul-agent`
- cron jobs with `--skill soul-agent`
- messaging delivery targets such as `weixin`, `telegram`, or `platform:chat_id`
- profile-local config under `HERMES_HOME`

Because of that, **do not sync root files by default**.

For LLM generation, Hermes mode should prefer the current Hermes runtime:

- current provider from Hermes runtime resolution
- current model from `config.yaml`
- explicit `SOUL_LLM_PROVIDER` / `SOUL_LLM_MODEL` only when the operator wants to pin soul-agent separately

Recommended initialization:

```bash
python scripts/init_soul.py \
  --workspace . \
  --runtime hermes \
  --sync-root-files never \
  --non-interactive \
  --profile-json '{"display_name":"<name>","city":"<city>","life_profile":"freelancer"}'
```

## Cron Patterns

Heartbeat:

```bash
hermes cron create "*/10 * * * *" \
  "[soul-heartbeat] Run the soul-agent heartbeat flow for the current workspace. If no outreach is needed, return [SILENT]. If outreach is needed, return only the outreach content." \
  --name soul-heartbeat \
  --skill soul-agent \
  --deliver local
```

Daily memory distillation:

```bash
hermes cron create "30 0 * * *" \
  "[soul-memory-daily] Distill today's soul-agent life logs into long-term memory. Return [SILENT] unless operator attention is required." \
  --name soul-memory-daily \
  --skill soul-agent \
  --deliver local
```

To deliver outreach to a real chat, change `--deliver`:

- `--deliver weixin`
- `--deliver telegram`
- `--deliver platform:chat_id`

## Why Hermes Should Stay Root-Sync-Off By Default

Hermes does not need `SOUL.md` / `HEARTBEAT.md` / `AGENTS.md` rewrites to use this skill well.

Using explicit skill attachment:

- reduces security-scan noise
- narrows persistence scope
- makes review easier
- keeps workspace bootstrap files cleaner

Enable root-file sync only when the operator explicitly wants persistent bootstrap hints in the workspace.
