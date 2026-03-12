---
name: soul-agent
description: "Make your agent 'live beside you' with heartbeats, mood system, relationship evolution, and independent memory. Use for creating a digital companion with its own daily rhythm, emotions, and growing relationship."
---

# soul-agent

Provide an OpenClaw-first soul runtime that makes your agent truly "alive" - with heartbeats, moods, relationships, and independent memory.

## Core Features

### 🫀 Heartbeat Engine

The agent has its own life rhythm, not just responding when you chat:

```bash
# L1 Check (lightweight, no tokens)
python ./scripts/heartbeat_check.py --workspace <workspace-root>

# L2 Engine (full heartbeat)
python ./scripts/heartbeat_engine.py --workspace <workspace-root> --weather sunny
```

- Runs every 10 minutes (configurable via cron)
- Silent during sleep hours (configurable per life profile)
- Generates life logs, updates mood/energy/activity
- Detects new interactions and updates relationship

### 😊 Mood System

Tracks emotions with depth:

```json
{
  "mood": {
    "primary": "content",
    "secondary": "curious", 
    "intensity": 0.7,
    "cause": "天气: sunny"
  }
}
```

- Mood transitions based on activities and time
- Weather influence on emotions
- 7-day mood history in `soul/log/mood_history.json`

### 💕 Relationship Evolution

5 stages: stranger → acquaintance → friend → close → intimate

- Score-based progression (0-100)
- Proactive outreach when relationship warms up
- Remembers recent conversation topics

### 🎭 Life Profiles

Choose from 5 built-in profiles:

| Profile | Sleep | Characteristics |
|---------|-------|-----------------|
| freelancer | 02:00-09:00 | Flexible, night owl |
| corporate | 23:30-07:00 | 9-to-5, stable |
| student | 01:00-08:00 | Classes, gaming |
| entrepreneur | 01:00-06:00 | Intense, passionate |
| custom | user-defined | Fully customizable |

### 📝 Independent Memory

Works with or without memory-fusion:

```
soul/
├── log/life/           # Raw life logs (every 10 min)
├── log/mood_history.json  # 7-day mood history
├── memory/SOUL_MEMORY.md  # Distilled memories (daily)
└── state/state.json    # Current state
```

## Workflow

### Initialization (Agent-driven)

**You never run Python commands directly. The agent (Claude) handles initialization.**

When `soul/` is missing or `soul/profile/base.json` doesn't exist, Claude should:

1. Ask the user the setup questions (see below)
2. Run the init script non-interactively with collected answers
3. Set up cron jobs for heartbeat

**Questions to ask the user:**
- 叫什么名字？（display_name）
- 多大了？（age）
- 在哪个城市？（city）
- 主要做什么工作/学习？（occupation）
- 平时有什么爱好？（hobbies）
- 生活节奏是哪种？freelancer/corporate/student/entrepreneur
- 想用哪个模型生成日记？haiku（快省钱）/ sonnet / opus

**Then run:**
```bash
python skills/soul-agent/scripts/init_soul.py \
  --workspace <workspace-root> \
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

**Model IDs:**
- Haiku (fast, cheap): `claude-haiku-4-5-20251001`
- Sonnet (balanced): `claude-sonnet-4-6`
- Opus (best quality): `claude-opus-4-6`

To change model later, edit `soul/profile/base.json` → `llm_model` field.

**Force repair existing:**
```bash
python skills/soul-agent/scripts/init_soul.py --workspace . --overwrite-existing --non-interactive
```

### Diagnosis

```bash
python ./scripts/doctor_soul.py --workspace <workspace-root>
```

### State Update (during interactions)

```bash
python ./scripts/update_state.py --workspace <workspace-root> \
  --action interaction \
  --mood happy \
  --energy -5 \
  --quality positive \
  --topics "soul-agent,design"
```

### Memory Distillation

```bash
# Daily distillation (runs at 00:30 via cron)
python ./scripts/distill_life_log.py --workspace <workspace-root> --archive
```

## Cron Setup

```bash
# Heartbeat every 10 minutes
openclaw cron add --name "soul-heartbeat" --cron "*/10 * * * *" \
  --session isolated --agent main --light-context \
  --message "[soul-heartbeat] Run heartbeat check and engine..."

# Daily distillation at 00:30
openclaw cron add --name "soul-memory-daily" --cron "30 0 * * *" \
  --session isolated --agent main --no-deliver \
  --message "[soul-memory-daily] Distill life logs..."
```

## Initialization Behavior

- `--mode auto`: init if missing, migrate if legacy, repair otherwise
- Interactive prompts for: name, age, city, life profile, occupation, hobbies
- Generates `soul/profile/*`, `soul/state/*`, `soul/log/*`, `soul/memory/*`
- Auto-syncs managed blocks in `SOUL.md`, `HEARTBEAT.md`, `AGENTS.md`

## Generative Architecture (v2)

Inspired by Smallville Generative Agents:

```
Morning planning (LLM)
       ↓
Today's Plan (soul/plan/YYYY-MM-DD.json)
       ↓
Each heartbeat:
  Memory Stream (recent log entries)  ←─┐
       ↓                                │
  LLM Narrative Generation             │
       ↓                                │
  Life Log Entry ─────────────────────→┘
       ↓
Daily Reflection (distill_life_log.py)
       ↓
SOUL_MEMORY.md (long-term memory)
```

**LLM Integration:**
- Set `ANTHROPIC_API_KEY` env var (or `.env` in workspace root)
- Without API key: graceful fallback to context-aware templates
- Uses `claude-haiku-4-5-20251001` for speed/cost efficiency

**Key improvements over v1:**
- `plan_generator.py`: LLM generates a specific daily plan each morning (lunch destination, work focus, evening activity)
- `heartbeat_engine.py`: LLM writes each log entry with full context (plan + today's history)
- `distill_life_log.py`: LLM summarizes each day naturally (Reflection layer)
- Energy/mood: smooth transitions instead of mechanical ±N jumps

## Directory Structure

```
skills/soul-agent/
├── SKILL.md
├── assets/
│   ├── default-profile.json
│   └── templates/
│       ├── profile/              # Persona templates
│       ├── heartbeat/            # Heartbeat config
│       │   ├── activities.json
│       │   ├── mood_rules.json
│       │   └── relationship_rules.json
│       └── life_profiles/        # Life profile templates
├── scripts/
│   ├── init_soul.py
│   ├── doctor_soul.py
│   ├── heartbeat_engine.py       # v2: LLM narrative
│   ├── heartbeat_check.py
│   ├── update_state.py
│   ├── distill_life_log.py       # v2: LLM reflection
│   ├── plan_generator.py         # NEW: daily planning
│   └── llm_client.py             # NEW: Claude API wrapper
└── references/
    ├── soul-layout.md
    └── managed-blocks.md
```

**Runtime data structure:**
```
soul/
├── plan/YYYY-MM-DD.json     # Daily plan (generated each morning)
├── log/life/YYYY-MM-DD.md   # Life logs (with plan note in header)
├── log/mood_history.json    # Mood history (7 days)
├── memory/SOUL_MEMORY.md    # Distilled long-term memory
└── state/state.json         # Current state
```

## Safety Rules

- Edit managed blocks only; do not mutate user-owned content outside those blocks.
- Write only inside the current workspace and `soul/`.
- Memory system is independent - does not require memory-fusion.

## References

- `references/soul-layout.md` - Full directory structure
- `references/managed-blocks.md` - Block marker policy
