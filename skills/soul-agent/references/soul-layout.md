# soul Layout

After initialization, `soul-agent` maintains:

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
└── log/
    ├── warnings.log
    └── sync.log
```

Principles:
- Persona and behavior rules live in `soul/profile/*`
- Runtime state lives in `soul/state/*`
- Runtime logs live in `soul/log/*`
- Root `SOUL.md` remains an entrypoint and managed-block host
- Legacy `soul/skills/*` is supported via `--mode migrate` (non-overwriting by default)
