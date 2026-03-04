#!/usr/bin/env python3
"""Initialize, repair, and migrate OpenClaw soul runtime structure (soul-agent)."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List


SOUL_MARK_START = "<!-- SOUL-AGENT:SOUL-START -->"
SOUL_MARK_END = "<!-- SOUL-AGENT:SOUL-END -->"
HEARTBEAT_MARK_START = "<!-- SOUL-AGENT:HEARTBEAT-START -->"
HEARTBEAT_MARK_END = "<!-- SOUL-AGENT:HEARTBEAT-END -->"
AGENTS_MARK_START = "<!-- SOUL-AGENT:AGENTS-START -->"
AGENTS_MARK_END = "<!-- SOUL-AGENT:AGENTS-END -->"

PROFILE_FILE_NAMES = [
    "base",
    "life",
    "personality",
    "tone",
    "boundary",
    "relationship",
    "schedule",
    "evolution",
]
INDEX_FILENAME = "INDEX.md"
LEGACY_INDEX_FILENAME = "SKILLS.md"


@dataclass
class Context:
    workspace: Path
    skill_root: Path
    defaults: Dict[str, str]


@dataclass
class WriteStats:
    written: int = 0
    skipped: int = 0


@dataclass
class MigrateStats:
    copied: int = 0
    conflicts: int = 0
    index_rewritten: bool = False


class SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize/repair soul/ and sync managed blocks in SOUL/HEARTBEAT/AGENTS."
    )
    parser.add_argument("--workspace", default=".", help="Workspace root")
    parser.add_argument(
        "--mode",
        default="auto",
        choices=["auto", "init", "repair", "migrate"],
        help="Mode: auto | init | repair | migrate",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Do not prompt; use defaults and optional --profile-json overrides.",
    )
    parser.add_argument(
        "--profile-json",
        default="",
        help="Optional JSON object for partial profile overrides.",
    )
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Allow overwriting existing profile/state files (default: fill missing only).",
    )
    return parser.parse_args()


def load_defaults(skill_root: Path) -> Dict[str, str]:
    path = skill_root / "assets" / "default-profile.json"
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def parse_overrides(raw: str) -> Dict[str, str]:
    if not raw.strip():
        return {}
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError("--profile-json must be a JSON object.")
    return {str(k): str(v) for k, v in obj.items()}


def merge_profile(defaults: Dict[str, str], overrides: Dict[str, str]) -> Dict[str, str]:
    merged = dict(defaults)
    for key, value in overrides.items():
        text = str(value).strip()
        if text:
            merged[key] = text
    return merged


def ask_user_profile(defaults: Dict[str, str]) -> Dict[str, str]:
    print("soul-agent init: press Enter to use defaults.")
    ordered_keys = [
        "agent_name",
        "display_name",
        "age",
        "city",
        "timezone",
        "vibe",
        "emoji",
        "tone_style",
        "relationship_goal",
    ]
    result: Dict[str, str] = {}
    for key in ordered_keys:
        default_val = defaults.get(key, "")
        raw = input(f"{key} [{default_val}]: ").strip()
        result[key] = raw if raw else default_val
    return result


def safe_console(text: str) -> str:
    return text.encode("ascii", errors="backslashreplace").decode("ascii")


def print_profile_delta(defaults: Dict[str, str], profile: Dict[str, str]) -> None:
    print("\nDefaults diff (default -> current):")
    for key in sorted(defaults.keys()):
        d_val = defaults.get(key, "")
        p_val = profile.get(key, "")
        mark = "modified" if d_val != p_val else "default"
        print(f"- {key}: '{safe_console(d_val)}' -> '{safe_console(p_val)}' [{mark}]")
    print()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_with_policy(path: Path, text: str, overwrite: bool, stats: WriteStats) -> None:
    if path.exists() and not overwrite:
        stats.skipped += 1
        return
    write_text(path, text)
    stats.written += 1


def append_log(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line.rstrip() + "\n")


def render_template(skill_root: Path, rel_template_path: str, mapping: Dict[str, str]) -> str:
    tpl_path = skill_root / "assets" / "templates" / rel_template_path
    tpl = tpl_path.read_text(encoding="utf-8")
    return tpl.format_map(SafeDict(mapping))


def upsert_managed_block(path: Path, start: str, end: str, body: str) -> None:
    block = f"{start}\n{body.strip()}\n{end}\n"
    if not path.exists():
        path.write_text(block, encoding="utf-8")
        return

    original = path.read_text(encoding="utf-8")
    s_idx = original.find(start)
    e_idx = original.find(end)
    if s_idx != -1 and e_idx != -1 and e_idx > s_idx:
        e_idx += len(end)
        new_text = original[:s_idx] + block + original[e_idx:]
        path.write_text(new_text, encoding="utf-8")
        return

    sep = "" if original.endswith("\n") else "\n"
    path.write_text(original + sep + "\n" + block, encoding="utf-8")


def resolve_mode(requested_mode: str, workspace: Path) -> str:
    soul_dir = workspace / "soul"
    legacy_dir = soul_dir / "skills"
    if requested_mode != "auto":
        return requested_mode
    if not soul_dir.exists():
        return "init"
    if legacy_dir.exists():
        return "migrate"
    return "repair"


def migrate_legacy(workspace: Path, overwrite_existing: bool, warnings: List[str]) -> MigrateStats:
    stats = MigrateStats()
    soul_dir = workspace / "soul"
    legacy_dir = soul_dir / "skills"
    profile_dir = soul_dir / "profile"
    if not legacy_dir.exists():
        return stats

    ensure_dir(profile_dir)
    for name in PROFILE_FILE_NAMES:
        src = legacy_dir / f"{name}.md"
        dst = profile_dir / f"{name}.md"
        if not src.exists():
            continue
        if dst.exists() and not overwrite_existing:
            stats.conflicts += 1
            warnings.append(
                f"[WARN] Migration conflict: {dst} already exists; keep existing content. Use --overwrite-existing to overwrite."
            )
            continue
        write_text(dst, src.read_text(encoding="utf-8"))
        stats.copied += 1

    legacy_index = soul_dir / LEGACY_INDEX_FILENAME
    new_index = soul_dir / INDEX_FILENAME
    if legacy_index.exists():
        original = legacy_index.read_text(encoding="utf-8")
        updated = original.replace("soul/skills/", "soul/profile/")
        if not new_index.exists() or overwrite_existing:
            # Normalize title while preserving user ordering/content where possible.
            if updated.lstrip().startswith("# soul/SKILLS.md"):
                updated = updated.replace("# soul/SKILLS.md", "# soul/INDEX.md", 1)
            write_text(new_index, updated)
            stats.index_rewritten = True
        warnings.append(
            "[WARN] Legacy soul/SKILLS.md detected; migrated to soul/INDEX.md. Keep SKILLS.md for backup and remove it manually after review."
        )

    warnings.append(
        "[WARN] Legacy directory soul/skills detected and recognized files migrated to soul/profile. Legacy directory is intentionally not deleted; clean it manually after review."
    )
    return stats


def build_soul_files(
    ctx: Context,
    profile: Dict[str, str],
    overwrite_existing: bool,
    warnings: List[str],
) -> WriteStats:
    soul_dir = ctx.workspace / "soul"
    profile_dir = soul_dir / "profile"
    state_dir = soul_dir / "state"
    log_dir = soul_dir / "log"
    warnings_path = log_dir / "warnings.log"
    sync_path = log_dir / "sync.log"

    ensure_dir(profile_dir)
    ensure_dir(state_dir)
    ensure_dir(log_dir)
    if not warnings_path.exists():
        write_text(warnings_path, "# soul/log/warnings.log")

    stats = WriteStats()
    mapping = dict(profile)

    write_with_policy(
        soul_dir / INDEX_FILENAME,
        render_template(ctx.skill_root, "soul_INDEX.md", mapping),
        overwrite_existing,
        stats,
    )

    template_pairs = [
        ("profile/base.md", profile_dir / "base.md"),
        ("profile/life.md", profile_dir / "life.md"),
        ("profile/personality.md", profile_dir / "personality.md"),
        ("profile/tone.md", profile_dir / "tone.md"),
        ("profile/boundary.md", profile_dir / "boundary.md"),
        ("profile/relationship.md", profile_dir / "relationship.md"),
        ("profile/schedule.md", profile_dir / "schedule.md"),
        ("profile/evolution.md", profile_dir / "evolution.md"),
    ]
    for tpl_name, out_path in template_pairs:
        write_with_policy(
            out_path,
            render_template(ctx.skill_root, tpl_name, mapping),
            overwrite_existing,
            stats,
        )

    now_iso = datetime.now().astimezone().isoformat(timespec="seconds")
    state = {
        "version": 1,
        "agent": profile["agent_name"].lower(),
        "timezone": profile["timezone"],
        "lastUpdated": now_iso,
        "location": "home",
        "activity": "idle",
        "energy": 70,
        "mood": "calm",
        "socialBattery": 70,
        "relationship": {"stage": "stranger", "score": 20, "lastOutreachAt": None},
    }
    write_with_policy(
        state_dir / "state.json",
        json.dumps(state, ensure_ascii=False, indent=2),
        overwrite_existing,
        stats,
    )

    for warning in warnings:
        append_log(warnings_path, warning)
    append_log(sync_path, f"{now_iso} [INFO] soul-agent init/sync completed")
    return stats


def sync_openclaw_files(workspace: Path) -> None:
    soul_md = workspace / "SOUL.md"
    heartbeat_md = workspace / "HEARTBEAT.md"
    agents_md = workspace / "AGENTS.md"

    soul_block = """
Runtime should read workspace `soul/` first:
`soul/INDEX.md` -> `soul/profile/*` -> `soul/state/state.json`.
Default scope is `main`; subagents are opt-in and must be enabled by the user.
If `soul/` is missing, use a minimal companion baseline and prompt to run `$soul-agent` initialization.
"""
    heartbeat_block = """
This block is intended for `main` during heartbeat polls by default.
Heartbeat must read:
- `soul/state/state.json`
- `soul/profile/life.md`
- `soul/profile/schedule.md`

If no actionable item exists, return `HEARTBEAT_OK`.
"""
    agents_block = """
`soul-agent` runtime contract (default: `main`):
1. Follow OpenClaw's default bootstrap order for root files (including `SOUL.md` and `HEARTBEAT.md`).
2. Inside SOUL logic, load `soul/INDEX.md` and `soul/profile/*`.
3. During heartbeat polls, read `soul/state/state.json` and cadence rules.
4. Subagents are not enabled by default; user must opt in manually.
"""

    upsert_managed_block(soul_md, SOUL_MARK_START, SOUL_MARK_END, soul_block)
    upsert_managed_block(
        heartbeat_md, HEARTBEAT_MARK_START, HEARTBEAT_MARK_END, heartbeat_block
    )
    upsert_managed_block(agents_md, AGENTS_MARK_START, AGENTS_MARK_END, agents_block)


def main() -> int:
    args = parse_args()
    skill_root = Path(__file__).resolve().parents[1]
    workspace = Path(args.workspace).resolve()
    defaults = load_defaults(skill_root)
    ctx = Context(workspace=workspace, skill_root=skill_root, defaults=defaults)

    try:
        overrides = parse_overrides(args.profile_json)
    except ValueError as exc:
        print(str(exc))
        return 2

    merged = merge_profile(defaults, overrides)
    mode = resolve_mode(args.mode, workspace)
    profile = merged
    if mode == "init" and not args.non_interactive:
        user_profile = ask_user_profile(merged)
        profile = merge_profile(merged, user_profile)

    print(f"Mode: {mode}")
    print_profile_delta(defaults, profile)

    warnings: List[str] = []
    migration_stats = MigrateStats()
    if mode == "migrate":
        migration_stats = migrate_legacy(workspace, args.overwrite_existing, warnings)

    stats = build_soul_files(ctx, profile, args.overwrite_existing, warnings)
    sync_openclaw_files(workspace)

    print("soul-agent: init/sync completed.")
    print(f"Workspace: {workspace}")
    print(f"Soul dir: {workspace / 'soul'}")
    print(
        f"Write stats: written={stats.written}, skipped={stats.skipped}, "
        f"migrated={migration_stats.copied}, conflicts={migration_stats.conflicts}"
    )
    if migration_stats.index_rewritten:
        print("Migration note: migrated legacy soul/SKILLS.md to soul/INDEX.md and rewrote soul/skills/* paths.")
    if warnings:
        print(f"Warnings: {len(warnings)} entries written to soul/log/warnings.log")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
