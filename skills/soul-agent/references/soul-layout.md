# soul Layout

After initialization, `soul-agent` maintains:

```text
soul/
├── INDEX.md                    # Profile loading order
├── profile/                    # Persona templates
│   ├── base.md                 # Identity (name, age, city, occupation)
│   ├── life.md                 # Daily rhythm, life profile
│   ├── personality.md          # Behavioral traits
│   ├── tone.md                 # Communication style
│   ├── boundary.md             # Interaction limits
│   ├── relationship.md         # Relationship progression rules
│   ├── schedule.md             # Sleep hours, quiet hours
│   └── evolution.md            # Evolution triggers
├── state/
│   └── state.json              # Runtime state (v2 schema)
├── log/
│   ├── life/                   # Raw life logs
│   │   └── YYYY-MM-DD.md       # Generated every 10 min by heartbeat
│   ├── mood_history.json       # 7-day mood history
│   ├── warnings.log            # System warnings
│   └── feedback.md             # Feedback for skill improvement
└── memory/
    └── SOUL_MEMORY.md          # Distilled life memories (daily)
```

## State Schema (v2)

```json
{
  "version": 2,
  "agent": "guagua",
  "timezone": "Asia/Shanghai",
  "lastUpdated": "2026-03-12T13:21:53+08:00",
  "location": "home",
  "activity": "lunch",
  "energy": 50,
  "mood": {
    "primary": "relaxed",
    "secondary": "curious",
    "intensity": 0.7,
    "cause": "活动: 午餐时间"
  },
  "socialBattery": 70,
  "lifeProfile": "freelancer",
  "schedule": {
    "sleepStart": "01:00",
    "sleepEnd": "07:00"
  },
  "relationship": {
    "stage": "acquaintance",
    "score": 30,
    "lastOutreachAt": null,
    "lastInteractionAt": "2026-03-12T05:06:27+08:00",
    "recentTopics": ["soul-agent", "design"],
    "warmthTrend": "stable"
  },
  "dailyStats": {
    "interactionsToday": 5,
    "heartbeatsToday": 24,
    "lastSleepAt": "2026-03-12T01:00:00+08:00",
    "lastWakeAt": "2026-03-12T07:00:00+08:00"
  },
  "lastHeartbeatAt": "2026-03-12T13:21:53+08:00"
}
```

## Memory Architecture

### Independent from memory-fusion

The soul memory system is completely independent:

| System | Path | Content | Purpose |
|--------|------|---------|---------|
| Life Logs | `soul/log/life/` | Raw activity logs | Every 10 min heartbeat |
| Mood History | `soul/log/mood_history.json` | 7-day mood tracking | Emotion trends |
| Distilled Memory | `soul/memory/SOUL_MEMORY.md` | Key events | Daily distillation |

### Daily Distillation

Runs at 00:30 via cron:

1. Reads last 7 days of life logs
2. Extracts key events, mood trends, relationship changes
3. Writes to `SOUL_MEMORY.md` (30-day rolling)
4. Archives logs older than 7 days

## Principles

- Persona and behavior rules live in `soul/profile/*`
- Runtime state lives in `soul/state/*`
- Raw logs live in `soul/log/life/*`
- Distilled memories live in `soul/memory/*`
- Root `SOUL.md` remains an entrypoint and managed-block host
- Legacy `soul/skills/*` is supported via `--mode migrate`
