#!/usr/bin/env python3
"""
Soul State Updater

在对话结束后更新状态：
- 能量变化
- 情绪变化
- 活动变化
- 关系更新

使用方式：
python3 update_state.py --workspace . --action interaction --mood happy --energy -5 --topics "soul-agent,心跳设计"
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List


def load_state(workspace: Path) -> Dict:
    """加载当前状态"""
    state_file = workspace / "soul" / "state" / "state.json"
    if state_file.exists():
        return json.loads(state_file.read_text(encoding="utf-8"))
    return {}


def save_state(workspace: Path, state: Dict):
    """保存状态"""
    state_file = workspace / "soul" / "state" / "state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state["lastUpdated"] = datetime.now().astimezone().isoformat(timespec="seconds")
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def update_after_interaction(
    state: Dict,
    mood: Optional[str] = None,
    mood_intensity: Optional[float] = None,
    energy_delta: Optional[int] = None,
    topics: Optional[List[str]] = None,
    interaction_quality: str = "neutral"
) -> Dict:
    """对话后更新状态"""
    now = datetime.now().astimezone()
    
    # 时间阈值检查：如果距离上次更新 < 5 分钟，跳过
    last_updated = state.get("lastUpdated")
    if last_updated:
        try:
            last_time = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=now.tzinfo)
            minutes_since = (now - last_time).total_seconds() / 60
            if minutes_since < 5:
                return {"skipped": True, "reason": f"updated {minutes_since:.0f} min ago"}
        except:
            pass
    
    # 更新活动
    state["activity"] = "interacting"
    
    # 更新情绪
    current_mood = state.get("mood", {})
    if isinstance(current_mood, str):
        current_mood = {"primary": current_mood, "intensity": 0.5}
    
    if mood:
        # 根据互动质量调整情绪
        quality_mood_map = {
            "positive": ["happy", "content", "excited", "grateful"],
            "neutral": ["neutral", "calm", "thoughtful"],
            "negative": ["frustrated", "sad", "anxious"]
        }
        available_moods = quality_mood_map.get(interaction_quality, [mood])
        if mood in available_moods:
            current_mood["primary"] = mood
        current_mood["cause"] = f"对话: {interaction_quality}"
    
    if mood_intensity is not None:
        current_mood["intensity"] = max(0, min(1, mood_intensity))
    
    state["mood"] = current_mood
    
    # 更新能量
    if energy_delta:
        current_energy = state.get("energy", 70)
        state["energy"] = max(0, min(100, current_energy + energy_delta))
    
    # 更新关系
    rel = state.get("relationship", {})
    rel["lastInteractionAt"] = now.isoformat()
    
    # 根据互动质量更新分数
    score_delta = {
        "positive": 3,
        "neutral": 1,
        "negative": -2
    }.get(interaction_quality, 0)
    
    current_score = rel.get("score", 20)
    rel["score"] = max(0, min(100, current_score + score_delta))
    
    # 更新话题
    if topics:
        recent = rel.get("recentTopics", [])
        for topic in topics:
            if topic not in recent:
                recent.insert(0, topic)
        rel["recentTopics"] = recent[:10]  # 保留最近 10 个
    
    # 更新关系阶段（从 relationship_rules.json 读取，保持单一来源）
    rel_rules_path = Path(__file__).parent.parent / "assets/templates/heartbeat/relationship_rules.json"
    stages_from_config = []
    if rel_rules_path.exists():
        try:
            rules = json.loads(rel_rules_path.read_text(encoding="utf-8"))
            for stage_name, info in rules.get("stages", {}).items():
                sr = info.get("scoreRange", [0, 20])
                if len(sr) == 2:
                    stages_from_config.append((stage_name, sr[0], sr[1]))
        except Exception:
            pass
    if not stages_from_config:
        # 硬编码降级，与 relationship_rules.json 保持一致
        stages_from_config = [
            ("stranger", 0, 20), ("acquaintance", 21, 40), ("friend", 41, 60),
            ("close", 61, 80), ("intimate", 81, 100),
        ]
    for stage, low, high in stages_from_config:
        if low <= rel["score"] <= high:
            rel["stage"] = stage
            break
    
    # 更新温暖趋势
    if score_delta > 0:
        rel["warmthTrend"] = "warming"
    elif score_delta < 0:
        rel["warmthTrend"] = "cooling"
    else:
        rel["warmthTrend"] = "stable"
    
    state["relationship"] = rel
    
    # 更新每日统计
    stats = state.get("dailyStats", {})
    stats["interactionsToday"] = stats.get("interactionsToday", 0) + 1
    state["dailyStats"] = stats
    
    return {"updated": True, "state": state}


def main():
    parser = argparse.ArgumentParser(description="Update soul state")
    parser.add_argument("--workspace", default=".", help="Workspace root")
    parser.add_argument("--action", choices=["interaction", "energy", "mood"], required=True)
    parser.add_argument("--mood", help="New mood (happy/sad/neutral/etc)")
    parser.add_argument("--mood-intensity", type=float, help="Mood intensity 0-1")
    parser.add_argument("--energy", type=int, help="Energy delta (+/-)")
    parser.add_argument("--topics", help="Comma-separated topics")
    parser.add_argument("--quality", default="neutral", help="Interaction quality (positive/neutral/negative)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace)
    state = load_state(workspace)
    
    topics = [t.strip() for t in args.topics.split(",")] if args.topics else None
    
    if args.action == "interaction":
        result = update_after_interaction(
            state,
            mood=args.mood,
            mood_intensity=args.mood_intensity,
            energy_delta=args.energy,
            topics=topics,
            interaction_quality=args.quality
        )
    else:
        result = {"error": f"Unknown action: {args.action}"}
    
    if result.get("updated"):
        save_state(workspace, result["state"])
    
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("skipped"):
            print(f"⏭️ Skipped: {result['reason']}")
        elif result.get("updated"):
            print(f"✅ Updated state")
            print(f"   Mood: {result['state'].get('mood', {}).get('primary', 'unknown')}")
            print(f"   Energy: {result['state'].get('energy', 'unknown')}")
            print(f"   Relationship: {result['state'].get('relationship', {}).get('stage', 'unknown')} ({result['state'].get('relationship', {}).get('score', 0)})")
        else:
            print(f"❌ Error: {result.get('error', 'unknown')}")


if __name__ == "__main__":
    main()
