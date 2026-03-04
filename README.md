# soul-agent

[English](README.md) | [中文](README_CN.md)

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

1. Heartbeats continuously trigger state updates, instead of waking only when a chat starts.
2. `soul/profile/*` defines the personality skeleton, `soul/state/*` stores current state, and `soul/log/*` records runtime traces.
3. Relationship and tone evolve with interaction quality, rather than being fixed once and forever.

## A Lifelike Example

Through heartbeats, the agent keeps sensing the living context of both her city and yours: weather shifts, holidays, commuting rhythm, and your recent routine or emotional signals.  
This context is not turned into robotic reminders, but into warm, human-like sharing and care.

For example:

"It suddenly started raining in Hangzhou today. I saw a little cat hiding from the rain on my way, and it reminded me that you said you felt a bit tired yesterday. It will cool down tonight on your side too, so take an umbrella on your way home. If you want, I can stay and talk with you a little later."

## What Is Already Done

- Initial `soul-agent` architecture has been designed and implemented.
- Workspace-first runtime layout under `soul/` is in place.
- Persona layering is complete: `base` / `life` / `personality` / `tone` / `boundary` / `relationship` / `schedule` / `evolution`.
- Managed-block sync is implemented for `SOUL.md`, `HEARTBEAT.md`, and `AGENTS.md`.
- Lifecycle operations are supported: `init`, `repair`, and `migrate`.

## Quick Start

1. Install this skill package (`soul-agent`).
2. Tell your agent:

```text
Use soul-agent, I am ready.
```

## Directory Structure

```text
skills/soul-agent/
├── SKILL.md
├── assets/
│   ├── default-profile.json
│   └── templates/
│       ├── soul_INDEX.md
│       └── profile/
├── scripts/
│   ├── doctor_soul.py
│   └── init_soul.py
└── references/
    ├── soul-layout.md
    └── managed-blocks.md
```

After initialization, the workspace will contain:

```text
soul/
├── INDEX.md
├── profile/
├── state/state.json
└── log/
```

## Runtime Principles

- Runtime reads workspace `soul/` first to keep everything workspace-local.
- Only managed blocks are modified; user-owned content outside those blocks is untouched.
- Default behavior is fill-missing-only, unless `--overwrite-existing` is explicitly passed.
- Stability and consistency come first, then personality richness and life detail grow over time.

## Next Steps

1. Improve naturalness and credibility during relationship warm-up.
2. Strengthen long-horizon life flow and memory integration under heartbeat driving.
3. Add multimodal input/output with image, voice, and video.
4. Achieve longer-running, observable, and traceable runtime at lower cost.
