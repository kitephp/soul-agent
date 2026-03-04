#!/usr/bin/env python3
"""Diagnose soul-agent structure and managed-block health."""

from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_PATHS = [
    "soul/INDEX.md",
    "soul/profile/base.md",
    "soul/profile/life.md",
    "soul/profile/personality.md",
    "soul/profile/tone.md",
    "soul/profile/boundary.md",
    "soul/profile/relationship.md",
    "soul/profile/schedule.md",
    "soul/profile/evolution.md",
    "soul/state/state.json",
    "soul/log/warnings.log",
    "soul/log/sync.log",
]

BLOCK_RULES = {
    "SOUL.md": ("<!-- SOUL-AGENT:SOUL-START -->", "<!-- SOUL-AGENT:SOUL-END -->"),
    "HEARTBEAT.md": (
        "<!-- SOUL-AGENT:HEARTBEAT-START -->",
        "<!-- SOUL-AGENT:HEARTBEAT-END -->",
    ),
    "AGENTS.md": ("<!-- SOUL-AGENT:AGENTS-START -->", "<!-- SOUL-AGENT:AGENTS-END -->"),
}

TEXT_FILES_TO_SCAN = ["SOUL.md", "HEARTBEAT.md", "AGENTS.md", "soul/INDEX.md", "soul/SKILLS.md"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check soul structure, managed blocks, and legacy path residue."
    )
    parser.add_argument("--workspace", default=".", help="Workspace root")
    return parser.parse_args()


def check_paths(workspace: Path) -> int:
    missing = []
    for rel in REQUIRED_PATHS:
        if not (workspace / rel).exists():
            missing.append(rel)
    if missing:
        print("Missing soul files:")
        for rel in missing:
            print(f"- {rel}")
        return 1
    print("Soul file structure: PASS")
    return 0


def check_blocks(workspace: Path) -> int:
    missing_blocks = []
    for rel, (start, end) in BLOCK_RULES.items():
        path = workspace / rel
        if not path.exists():
            missing_blocks.append(f"{rel} (file not found)")
            continue
        text = path.read_text(encoding="utf-8")
        if start not in text or end not in text:
            missing_blocks.append(rel)
    if missing_blocks:
        print("Missing managed blocks:")
        for item in missing_blocks:
            print(f"- {item}")
        return 1
    print("Managed blocks: PASS")
    return 0


def check_legacy_and_references(workspace: Path) -> int:
    warnings = []
    legacy_dir = workspace / "soul" / "skills"
    profile_dir = workspace / "soul" / "profile"
    if legacy_dir.exists() and profile_dir.exists():
        warnings.append(
            "Both soul/skills and soul/profile exist. Run migrate mode and clean legacy after review."
        )
    if (workspace / "soul" / "SKILLS.md").exists():
        warnings.append(
            "Legacy index file soul/SKILLS.md detected. Preferred index file is soul/INDEX.md."
        )

    for rel in TEXT_FILES_TO_SCAN:
        path = workspace / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if "soul/skills/" in text:
            warnings.append(f"{rel} still references legacy path soul/skills/*.")

    if warnings:
        print("Structure warnings:")
        for item in warnings:
            print(f"- {item}")
        return 0

    print("Paths and references: PASS")
    return 0


def check_main_scope_hints(workspace: Path) -> int:
    warnings = []
    soul_path = workspace / "SOUL.md"
    heartbeat_path = workspace / "HEARTBEAT.md"
    if soul_path.exists():
        text = soul_path.read_text(encoding="utf-8")
        if "main" not in text and "main session" not in text:
            warnings.append("SOUL.md does not explicitly mention main-default scope.")
    if heartbeat_path.exists():
        text = heartbeat_path.read_text(encoding="utf-8")
        if "heartbeat poll" not in text and "heartbeat" not in text:
            warnings.append("HEARTBEAT.md does not explicitly describe heartbeat poll scope.")

    if warnings:
        print("Scope hints:")
        for item in warnings:
            print(f"- {item}")
        return 0

    print("Scope hints: PASS")
    return 0


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace).resolve()
    code = 0
    code |= check_paths(workspace)
    code |= check_blocks(workspace)
    code |= check_legacy_and_references(workspace)
    code |= check_main_scope_hints(workspace)
    if code == 0:
        print("soul-agent diagnosis: PASS")
    else:
        print("soul-agent diagnosis: FAIL")
        print("Run `$soul-agent` init/repair flow (use migrate mode if needed).")
    return 1 if code else 0


if __name__ == "__main__":
    raise SystemExit(main())
