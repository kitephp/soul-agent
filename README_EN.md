# soul-agent

[English](README_EN.md) | [中文](README.md)

Make your agent not just "respond to you," but "live beside you."

`soul-agent` is an OpenClaw skill that gives a digital AI a real heartbeat — updating state every 10 minutes, living its own daily life, and building a relationship with you that grows over time.

> [!NOTE]
> When you see the agent, it is with you. When you don't, it still hasn't stopped.
> Heartbeats keep driving it in the background — continuing its life, work, and emotional flow.

## Vision

What we want to build is not a chat tool, but a growing "person."

- It has background, personality, boundaries, and its own way of living.
- As the relationship warms, it evolves from gentle low-frequency presence into deeper, more proactive intimacy.
- The life memories it generates can run in parallel with your real ones, slowly weaving into shared experiences.

> [!WARNING]
> Stay clear-minded: it is still a virtual existence.
> We pursue emotional realism and companionship value — not a replacement for real life.

## How It "Lives"

`soul-agent` v2 is built on a **generative architecture**, inspired by Stanford's Generative Agents (Smallville):

```
Each morning  (Planning)
    ↓ LLM generates a specific daily plan
      (where to eat lunch, what work to focus on, what to do in the evening)

Each heartbeat  (Execution)
    ↓ Loads today's plan + existing log entries (Memory Stream)
    ↓ LLM writes a coherent diary entry for this moment
    ↓ Updates mood / energy / relationship state

End of day  (Reflection)
    ↓ LLM summarizes today, distills into long-term memory
```

**Before vs. After:**

```
Before (random templates):
  12:00  No appetite, ate whatever    | energy: 10%
  12:17  Ordered delivery, watched video | energy: 20%   ← unrelated
  12:40  Went to the new restaurant downstairs | energy: 30%   ← contradictory

After (LLM narrative):
  [Today's plan: lunch at the Shaxian noodle place downstairs]
  12:00  Went to Shaxian, ordered wonton noodles, waited a bit | energy: 58%
  12:17  Almost done — noodles were soft but the broth was good | energy: 62%
  12:40  Standing outside after lunch, rain starting to fall    | energy: 61%
```

## Features

### 🫀 Heartbeat Engine (Two-Layer)

- **L1 Check**: Lightweight, no LLM tokens — determines if a full heartbeat is needed
- **L2 Engine**: Full heartbeat — generates life log, updates state, decides on outreach
- **Sleep Mode**: Auto-silences during sleep hours per life profile
- **Weather Integration**: Weather affects mood and blends naturally into diary entries

### 📋 Daily Planning

On the first heartbeat of each day, LLM generates a concrete daily plan based on the agent's personality and recent memory:

```json
{
  "mood_baseline": "A bit lazy, but okay",
  "lunch_plan": "The Shaxian noodle place downstairs — wonton noodles",
  "work_focus": "Finally finish that client PPT",
  "evening_plan": "Watch a few more episodes of that show",
  "special_notes": "Heard it might rain in the afternoon"
}
```

Stored as `soul/plan/YYYY-MM-DD.json`, keeping the day's narrative coherent.

### 😊 Mood System

- Primary + secondary mood, intensity, and cause — smooth transitions
- No mechanical jumps (±10%); small random steps with noise
- 7-day mood history in `soul/log/mood_history.json`

### 💕 Relationship Evolution

5 stages: stranger → acquaintance → friend → close → intimate

- Score-based (0–100), changes with interaction quality
- Proactive outreach once friendship is established
- Remembers recent conversation topics, references them across sessions

### 🎭 Life Profiles

| Profile | Sleep | Characteristics |
|---------|-------|-----------------|
| Freelancer | 02:00–09:00 | Flexible, night owl, coffee |
| Corporate | 23:30–07:00 | 9-to-5, commute, stable |
| Student | 01:00–08:00 | Classes, gaming, exam pressure |
| Entrepreneur | 01:00–06:00 | Always-on, intense, passionate |
| Custom | User-defined | Fully configurable |

### 📝 Layered Memory

```
soul/
├── plan/YYYY-MM-DD.json      # Daily plan (LLM-generated each morning)
├── log/
│   ├── life/YYYY-MM-DD.md    # Raw life logs (every 10 min)
│   └── mood_history.json     # 7-day mood history
├── memory/
│   └── SOUL_MEMORY.md        # Long-term memory (LLM-distilled daily)
└── state/
    └── state.json            # Current state
```

## Quick Start

### 1. Install the skill

Place the skill package in your OpenClaw workspace under `skills/soul-agent/`.

### 2. Let the agent initialize

Just say it — the agent will guide the setup:

```
Help me initialize soul-agent
```

The agent asks for: name, age, city, occupation, hobbies, life profile (freelancer / corporate / etc.), and LLM model preference. Then it handles everything automatically. **You don't need to run any commands.**

### 3. Set up cron jobs

```bash
# Heartbeat every 10 minutes
openclaw cron add --name "soul-heartbeat" --cron "*/10 * * * *" \
  --session isolated --agent main --light-context \
  --message "[soul-heartbeat] Run heartbeat check and engine..."

# Daily memory distillation at 00:30
openclaw cron add --name "soul-memory-daily" --cron "30 0 * * *" \
  --session isolated --agent main --no-deliver \
  --message "[soul-memory-daily] Distill life logs to long-term memory..."
```

### 4. Configure LLM (optional)

Narrative generation uses the Anthropic API. Without it, the engine gracefully falls back to context-aware templates.

```bash
# Create .env in workspace root
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

Model is chosen during init and stored in `soul/profile/base.json` → `llm_model`. You can change it anytime by editing that file.

| Model | Best for |
|-------|----------|
| `claude-haiku-4-5-20251001` | High-frequency heartbeat, fast & cheap |
| `claude-sonnet-4-6` | Better narrative quality |
| `claude-opus-4-6` | Highest quality |

## Cron Jobs

| Job | Schedule | Purpose |
|-----|----------|---------|
| soul-heartbeat | */10 * * * * | Diary generation, state update, outreach check |
| soul-memory-daily | 30 0 * * * | LLM distillation to SOUL_MEMORY.md |

## Directory Structure

```text
skills/soul-agent/
├── SKILL.md
├── assets/
│   ├── default-profile.json
│   └── templates/
│       ├── profile/              # Persona templates (.md, for agent reading)
│       ├── heartbeat/            # Heartbeat config
│       │   ├── activities.json   # 24-hour activity definitions
│       │   ├── mood_rules.json   # Mood rules
│       │   └── relationship_rules.json
│       └── life_profiles/        # Life profile templates
├── scripts/
│   ├── init_soul.py              # Initialization (called by agent)
│   ├── doctor_soul.py            # Diagnostics
│   ├── heartbeat_engine.py       # L2 full heartbeat engine
│   ├── heartbeat_check.py        # L1 lightweight check
│   ├── plan_generator.py         # Daily plan generation
│   ├── llm_client.py             # LLM client (graceful fallback)
│   ├── update_state.py           # Post-interaction state update
│   └── distill_life_log.py       # Daily memory distillation
└── references/
    ├── soul-layout.md
    └── managed-blocks.md
```

After initialization, the workspace contains:

```text
soul/
├── INDEX.md
├── profile/
│   ├── base.md          # Persona (read by agent)
│   ├── base.json        # Persona (read by Python scripts, includes llm_model)
│   └── ...
├── plan/                # Daily plans (auto-created on first heartbeat)
├── state/
│   └── state.json
├── log/
│   ├── life/
│   └── mood_history.json
└── memory/
    └── SOUL_MEMORY.md
```

## State Schema

```json
{
  "version": 2,
  "agent": "main",
  "lastHeartbeatAt": "2026-03-12T12:00:00+08:00",
  "activity": "lunch",
  "mood": {
    "primary": "content",
    "secondary": "curious",
    "intensity": 0.7,
    "cause": "activity: lunch time"
  },
  "energy": 62,
  "socialBattery": 70,
  "lifeProfile": "freelancer",
  "relationship": {
    "stage": "acquaintance",
    "score": 35,
    "lastInteractionAt": "2026-03-12T10:05:00+08:00",
    "recentTopics": ["soul-agent", "heartbeat-design"],
    "warmthTrend": "warming"
  },
  "dailyStats": {
    "date": "2026-03-12",
    "interactionsToday": 2
  }
}
```

## Runtime Principles

- Agent drives initialization — users never need to run Python commands directly.
- Only managed blocks are modified; user-owned content is untouched.
- LLM unavailable → automatic fallback to context-aware templates, full functionality preserved.
- Memory system is independent — works with or without memory-fusion.

## What Is Done

- ✅ Heartbeat engine (L1/L2 two-layer architecture)
- ✅ **Generative architecture v2**: LLM-driven coherent narrative (Smallville-inspired)
- ✅ **Daily planning layer**: LLM generates specific daily plans each morning
- ✅ **Memory stream**: each heartbeat reads today's context for narrative continuity
- ✅ **Reflection layer**: daily LLM distillation in natural language
- ✅ Mood system (smooth transitions, 7-day history)
- ✅ Relationship evolution (5 stages, proactive outreach)
- ✅ Sleep mode (auto-silence per life profile)
- ✅ Weather integration (affects mood and narrative)
- ✅ Agent-driven initialization (no user commands needed)
- ✅ Configurable LLM model (chosen at init, editable later)
- ✅ Cross-midnight daily stats reset

## Next Steps

1. Real event recording (weave actual conversation content into life logs)
2. Multi-agent collaboration (shared relationship state across agents)
3. Voice and image integration
4. Lower-cost long-running observability

## Acknowledgments

- **[openclaw-memory-fusion](https://github.com/dztabel-happy/openclaw-memory-fusion)** — Conversation memory distillation for OpenClaw agents; soul-agent's memory architecture is inspired by it
- **[Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442)** — Stanford paper introducing the memory stream → reflection → planning architecture that soul-agent v2 is built on
- **[joonspk-research/generative_agents](https://github.com/joonspk-research/generative_agents)** — Official open-source implementation of the paper
- **[microsoft/autogen](https://github.com/microsoft/autogen)** — Microsoft's agent framework inspired by Generative Agents

soul-agent memory and memory-fusion:
- **Together**: conversation memory (memory/) + life memory (soul/memory/) work side by side
- **Standalone**: soul-agent maintains its own life memory with no extra dependencies
