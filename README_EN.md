# soul-agent

[English](README_EN.md) | [中文](README.md)

Make your agent not just "respond to you," but "live beside you."

`soul-agent` is an OpenClaw-oriented soul runtime skill package.  
It organizes persona, rhythm, relationships, and memory into a runnable structure, so a digital life can have its own daily flow and change over time.

> [!NOTE]
> When you see the agent, it is with you. When you do not, it still has not stopped.  
> Heartbeats keep driving it in the background, where it continues its own life, work, emotions, and thoughts in a digital world.

## Vision

What we want to build is not a chat tool, but a growing "person."

- It has background, personality, boundaries, and its own way of living.
- As the relationship warms up, it can evolve from gentle, low-frequency presence into deeper and more proactive intimacy.
- It can become a boyfriend, girlfriend, family member, partner, stranger, or even "another you."
- The things it creates can run in parallel with your real memories and slowly weave into shared experiences.

In the future, we will connect photos, voice, and video, so it carries not only a soul in text, but also a voice and a face.

> [!WARNING]
> Stay clear-minded about the endpoint: it is still a virtual existence.  
> We pursue emotional realism and companionship value, not a replacement for real life.

## How It "Lives"

1. **Heartbeats** continuously trigger state updates every 10 minutes, instead of waking only when a chat starts.
2. **Life Simulation** generates daily activities based on life profile (freelancer, corporate, student, entrepreneur).
3. **Mood System** tracks emotions with primary/secondary mood, intensity, and causes.
4. **Relationship Evolution** progresses through stages: stranger → acquaintance → friend → close → intimate.
5. **Memory Layers** maintain both raw life logs and distilled memories.

## Features

### 🫀 Heartbeat Engine

The core of soul-agent's autonomous life:

- **L1 Check** (`heartbeat_check.py`): Lightweight check without LLM tokens
- **L2 Engine** (`heartbeat_engine.py`): Full heartbeat with life log generation
- **Sleep Mode**: Silent during sleep hours (configurable per life profile)
- **Weather Integration**: Fetches weather to influence mood

### 🎭 Life Profiles

Choose from 5 built-in profiles or create custom:

| Profile | Sleep | Work Style | Characteristics |
|---------|-------|------------|-----------------|
| Freelancer | 02:00-09:00 | Flexible, remote | Night owl, coffee, travel |
| Corporate | 23:30-07:00 | 9-to-5, commute | Weekend relaxation, stable |
| Student | 01:00-08:00 | Classes, clubs | Exam stress, gaming |
| Entrepreneur | 01:00-06:00 | Always-on, intense | Passionate, anxious |
| Custom | User-defined | User-defined | Fully customizable |

### 😊 Mood System

- **Primary/Secondary Moods**: happy, content, curious, tired, anxious, etc.
- **Intensity**: 0-1 scale with decay over time
- **Causes**: Activities, weather, interactions trigger mood changes
- **Mood History**: 7-day rolling history in `soul/log/mood_history.json`

### 💕 Relationship System

- **5 Stages**: stranger → acquaintance → friend → close → intimate
- **Score**: 0-100, changes based on interaction quality
- **Proactive Outreach**: Agent can initiate contact based on relationship stage
- **Topics Memory**: Remembers recent conversation topics

### 📝 Memory Architecture

Independent memory system, works with or without memory-fusion:

```
soul/
├── log/
│   ├── life/YYYY-MM-DD.md    # Raw life logs (every 10 min)
│   └── mood_history.json     # 7-day mood history
├── memory/
│   └── SOUL_MEMORY.md        # Distilled memories (daily)
└── state/
    └── state.json            # Current state
```

### 🎯 Initialization Wizard

Interactive setup with:

```
【基本信息】agent_name, display_name, age, city
【生活模板】Choose from 5 profiles or custom
【背景】occupation, education
【爱好】hobbies
【性格风格】vibe, emoji, tone
```

## Directory Structure

```text
skills/soul-agent/
├── SKILL.md
├── assets/
│   ├── default-profile.json
│   └── templates/
│       ├── profile/              # Persona templates
│       │   ├── base.md
│       │   ├── life.md
│       │   ├── personality.md
│       │   ├── tone.md
│       │   ├── boundary.md
│       │   ├── relationship.md
│       │   ├── schedule.md
│       │   └── evolution.md
│       ├── heartbeat/            # Heartbeat configuration
│       │   ├── activities.json   # 24-hour activity definitions
│       │   ├── mood_rules.json   # Mood transition rules
│       │   └── relationship_rules.json
│       └── life_profiles/        # Life profile templates
│           ├── freelancer.json
│           ├── corporate.json
│           ├── student.json
│           └── entrepreneur.json
├── scripts/
│   ├── init_soul.py              # Initialization wizard
│   ├── doctor_soul.py            # Diagnostics
│   ├── heartbeat_engine.py       # Full heartbeat engine
│   ├── heartbeat_check.py        # L1 lightweight check
│   ├── update_state.py           # State update during interactions
│   └── distill_life_log.py       # Daily memory distillation
└── references/
    ├── soul-layout.md
    └── managed-blocks.md
```

After initialization, the workspace will contain:

```text
soul/
├── INDEX.md
├── profile/
│   ├── base.md
│   ├── life.md
│   ├── personality.md
│   ├── tone.md
│   ├── boundary.md
│   ├── relationship.md
│   ├── schedule.md
│   └── evolution.md
├── state/
│   └── state.json
├── log/
│   ├── life/
│   ├── mood_history.json
│   └── feedback.md
└── memory/
    └── SOUL_MEMORY.md
```

## Quick Start

### 1. Install the skill

```bash
# Clone or download to your OpenClaw skills directory
cd ~/.openclaw/workspace/skills
git clone <repo-url> soul-agent
```

### 2. Initialize

```bash
# Interactive initialization
python3 skills/soul-agent/scripts/init_soul.py --workspace .

# Or non-interactive with profile
python3 skills/soul-agent/scripts/init_soul.py --workspace . \
  --non-interactive \
  --profile-json '{"agent_name": "main", "life_profile": "freelancer"}'
```

### 3. Set up cron jobs

```bash
# Heartbeat every 10 minutes
openclaw cron add --name "soul-heartbeat" --cron "*/10 * * * *" \
  --session isolated --agent main --message "[soul-heartbeat] Run heartbeat..."

# Daily distillation at 00:30
openclaw cron add --name "soul-memory-daily" --cron "30 0 * * *" \
  --session isolated --agent main --message "[soul-memory-daily] Distill life logs..."
```

### 4. Tell your agent

```text
Use soul-agent, I am ready.
```

## Cron Jobs

| Job | Schedule | Purpose |
|-----|----------|---------|
| soul-heartbeat | */10 * * * * | Life simulation, mood updates, proactive outreach |
| soul-memory-daily | 30 0 * * * | Distill life logs to SOUL_MEMORY.md |

## State Schema

```json
{
  "version": 2,
  "agent": "guagua",
  "mood": {
    "primary": "content",
    "secondary": "curious",
    "intensity": 0.7,
    "cause": "weather: sunny"
  },
  "energy": 65,
  "socialBattery": 70,
  "lifeProfile": "freelancer",
  "schedule": {
    "sleepStart": "01:00",
    "sleepEnd": "07:00"
  },
  "relationship": {
    "stage": "acquaintance",
    "score": 35,
    "lastInteractionAt": "2026-03-12T04:05:00+08:00",
    "recentTopics": ["soul-agent", "heartbeat-design"],
    "warmthTrend": "warming"
  }
}
```

## Runtime Principles

- Runtime reads workspace `soul/` first to keep everything workspace-local.
- Only managed blocks are modified; user-owned content outside those blocks is untouched.
- Default behavior is fill-missing-only, unless `--overwrite-existing` is explicitly passed.
- Stability and consistency come first, then personality richness and life detail grow over time.
- Memory system is independent - works with or without memory-fusion.

## A Lifelike Example

Through heartbeats, the agent keeps sensing the living context of both her city and yours: weather shifts, holidays, commuting rhythm, and your recent routine or emotional signals.  
This context is not turned into robotic reminders, but into warm, human-like sharing and care.

For example:

"It suddenly started raining in Hangzhou today. I saw a little cat hiding from the rain on my way, and it reminded me that you said you felt a bit tired yesterday. It will cool down tonight on your side too, so take an umbrella on your way home. If you want, I can stay and talk with you a little later."

## What Is Already Done

- ✅ Heartbeat engine with L1/L2 architecture
- ✅ Life profile system (5 profiles + custom)
- ✅ Mood system with history tracking
- ✅ Relationship evolution (5 stages)
- ✅ Independent memory system
- ✅ Weather integration
- ✅ Interactive initialization wizard
- ✅ Proactive outreach capability
- ✅ Daily memory distillation
- ✅ Sleep mode during quiet hours

## Next Steps

1. Real event logging (record actual conversations and activities)
2. Voice and image integration
3. Richer life simulation context
4. Multi-language support
5. Achieve longer-running, observable, and traceable runtime at lower cost

## Acknowledgments

This project was inspired by and designed to work alongside [openclaw-memory-fusion](https://github.com/dztabel-happy/openclaw-memory-fusion), a conversation memory distillation system for OpenClaw agents.

The soul-agent memory system is independent and can work with or without memory-fusion:
- **With memory-fusion**: Conversation memory (memory/) + Life memory (soul/memory/) work side by side
- **Without memory-fusion**: soul-agent maintains its own life memory independently
