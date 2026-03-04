# Managed Block Policy

`soul-agent` updates only managed blocks in:
- `SOUL.md`
- `HEARTBEAT.md`
- `AGENTS.md`

Block markers:
- `<!-- SOUL-AGENT:SOUL-START --> ... <!-- SOUL-AGENT:SOUL-END -->`
- `<!-- SOUL-AGENT:HEARTBEAT-START --> ... <!-- SOUL-AGENT:HEARTBEAT-END -->`
- `<!-- SOUL-AGENT:AGENTS-START --> ... <!-- SOUL-AGENT:AGENTS-END -->`

Rules:
- If a block exists, replace only block content.
- If file exists without block, append block.
- If file does not exist, create it with block.
- Never modify user content outside managed blocks.

Block semantics:
- `SOUL.md`: runtime is workspace-first (`soul/`), fallback prompts to run `$soul-agent` init
- `HEARTBEAT.md`: default scope is `main` during heartbeat polls
- `AGENTS.md`: main-default contract; subagents must be explicitly enabled by the user
