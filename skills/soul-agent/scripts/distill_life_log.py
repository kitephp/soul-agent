#!/usr/bin/env python3
"""
Soul Life Log Distiller (v2)

每天运行一次，蒸馏生活日志到 soul/memory/SOUL_MEMORY.md

v2 改进：
- 优先用 LLM 生成自然语言摘要（Smallville: Reflection layer）
- LLM 不可用时降级到关键词提取
- 摘要更有温度，像真人在回顾自己的一天

流程：
1. 读取最近 N 天的生活日志 (soul/log/life/*.md)
2. LLM 总结每天的关键事件和情绪弧线
3. 写入 soul/memory/SOUL_MEMORY.md (滚动 30 天)
4. 归档超过 7 天的原始日志
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


def parse_life_log(content: str) -> Dict:
    """解析生活日志，提取结构化信息"""
    entries = []
    
    # 匹配时间块
    pattern = r"### (\d{2}:\d{2}) - (.+?)\n\n(.+?)\n\n\*状态: (.+?) \| 能量: (\d+)%\*"
    matches = re.findall(pattern, content, re.DOTALL)
    
    for time_str, activity, log_text, mood, energy in matches:
        entries.append({
            "time": time_str,
            "activity": activity.strip(),
            "log": log_text.strip(),
            "mood": mood.strip(),
            "energy": int(energy)
        })
    
    return {
        "entries": entries,
        "total_entries": len(entries)
    }


def extract_key_events(entries: List[Dict]) -> List[str]:
    """提取关键事件（有趣/特别/情绪波动的）"""
    key_events = []
    
    # 关键词
    interesting_keywords = [
        "有趣", "开心", "兴奋", "难过", "生气", "惊讶", 
        "特别", "第一次", "终于", "没想到", "发现",
        "朋友", "聚会", "旅行", "电影", "书", "游戏"
    ]
    
    for entry in entries:
        log = entry.get("log", "")
        mood = entry.get("mood", "neutral")
        
        # 情绪波动
        if mood not in ["neutral", "calm", "content"]:
            key_events.append(f"- [{entry['time']}] {mood}: {log}")
        # 包含关键词
        elif any(kw in log for kw in interesting_keywords):
            key_events.append(f"- [{entry['time']}] {log}")
    
    return key_events[:10]  # 最多 10 条


def extract_mood_summary(entries: List[Dict]) -> Dict:
    """统计情绪分布"""
    mood_counts = {}
    energy_values = []
    
    for entry in entries:
        mood = entry.get("mood", "neutral")
        mood_counts[mood] = mood_counts.get(mood, 0) + 1
        energy_values.append(entry.get("energy", 50))
    
    avg_energy = sum(energy_values) / len(energy_values) if energy_values else 50
    dominant_mood = max(mood_counts.items(), key=lambda x: x[1])[0] if mood_counts else "neutral"
    
    return {
        "mood_distribution": mood_counts,
        "dominant_mood": dominant_mood,
        "avg_energy": round(avg_energy, 1)
    }


def _load_day_plan(log_file: Path) -> Optional[str]:
    """尝试加载当天的 daily plan 摘要，作为反思的额外上下文"""
    date_str = log_file.stem
    # soul/plan/YYYY-MM-DD.json 相对于 log_file 位置推断
    # log_file: soul/log/life/YYYY-MM-DD.md → soul/plan/YYYY-MM-DD.json
    plan_file = log_file.parent.parent.parent / "plan" / f"{date_str}.json"
    if not plan_file.exists():
        return None
    try:
        plan = json.loads(plan_file.read_text(encoding="utf-8"))
        parts = []
        if plan.get("mood_baseline"):
            parts.append(f"情绪基调：{plan['mood_baseline']}")
        if plan.get("lunch_plan"):
            parts.append(f"午饭计划：{plan['lunch_plan']}")
        if plan.get("work_focus"):
            parts.append(f"工作重点：{plan['work_focus']}")
        if plan.get("evening_plan"):
            parts.append(f"晚上打算：{plan['evening_plan']}")
        if plan.get("special_notes"):
            parts.append(f"备注：{plan['special_notes']}")
        return "；".join(parts) if parts else None
    except Exception:
        return None


def distill_day_with_llm(log_file: Path, llm, profile: Dict) -> Optional[str]:
    """用 LLM 生成一天的自然语言摘要（Reflection 层）"""
    if not log_file.exists() or not llm or not llm.available():
        return None

    content = log_file.read_text(encoding="utf-8")
    parsed = parse_life_log(content)
    if not parsed["entries"]:
        return None

    date_str = log_file.stem
    name = profile.get("display_name", "我")
    entries_text = "\n".join(
        f"[{e['time']}] {e['activity']}: {e['log']} (情绪:{e['mood']}, 能量:{e['energy']}%)"
        for e in parsed["entries"][:20]
    )

    # 加入当日计划作为上下文（让反思更有"我原来打算..."的质感）
    day_plan = _load_day_plan(log_file)
    plan_context = f"\n今天早上的计划：{day_plan}" if day_plan else ""

    system = (
        f"你是{name}，在整理自己的日记记忆。"
        "用第一人称，简短自然地总结这一天。像真人在回忆，不要列表，不要标题，就是几句话。"
        "可以对比一下计划和实际发生的事，保留有温度的细节，忽略无聊的重复。100字以内。"
    )

    prompt = (
        f"这是{date_str}的日志记录：{plan_context}\n\n{entries_text}\n\n"
        "用2-4句话总结这一天，像在回忆一段生活片段。"
    )

    try:
        result = llm.generate(prompt, max_tokens=150, system=system)
        if result and len(result) > 10:
            return result.strip()
    except Exception:
        pass
    return None


def distill_day(log_file: Path, llm=None, profile: Dict = None) -> Optional[Dict]:
    """蒸馏一天的生活日志"""
    if not log_file.exists():
        return None

    content = log_file.read_text(encoding="utf-8")
    parsed = parse_life_log(content)

    if not parsed["entries"]:
        return None

    date_str = log_file.stem  # YYYY-MM-DD

    # 尝试 LLM 摘要
    llm_summary = None
    if llm and profile:
        llm_summary = distill_day_with_llm(log_file, llm, profile)

    return {
        "date": date_str,
        "total_entries": parsed["total_entries"],
        "key_events": extract_key_events(parsed["entries"]),
        "mood_summary": extract_mood_summary(parsed["entries"]),
        "llm_summary": llm_summary,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Distill soul life logs (v2)")
    parser.add_argument("--workspace", default=".", help="Workspace root")
    parser.add_argument("--days", type=int, default=7, help="Days to look back")
    parser.add_argument("--archive", action="store_true", help="Archive old logs")

    args = parser.parse_args()

    workspace = Path(args.workspace)
    life_log_dir = workspace / "soul" / "log" / "life"
    memory_dir = workspace / "soul" / "memory"
    archive_dir = life_log_dir / "archive"

    memory_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    # 初始化 LLM（可选）
    llm = None
    profile = {}
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from llm_client import LLMClient
        llm = LLMClient(args.workspace)

        # 加载 profile 供 LLM 使用
        for candidate in [
            workspace / "soul" / "profile" / "base.json",
            Path(__file__).parent.parent / "assets" / "default-profile.json",
        ]:
            if candidate.exists():
                try:
                    profile = json.loads(candidate.read_text(encoding="utf-8"))
                    break
                except Exception:
                    pass
    except Exception:
        pass

    today = datetime.now().date()
    distilled = []

    for i in range(args.days):
        date = today - timedelta(days=i)
        log_file = life_log_dir / f"{date.strftime('%Y-%m-%d')}.md"
        day_data = distill_day(log_file, llm=llm, profile=profile)
        if day_data:
            distilled.append(day_data)

    if not distilled:
        print(f"No life logs found in the past {args.days} days")
        return

    soul_memory_file = memory_dir / "SOUL_MEMORY.md"
    output_lines = [
        "# SOUL_MEMORY.md - 生活记忆蒸馏",
        "",
        "_自动生成，滚动保留 30 天的关键生活事件_",
        "",
        "## 近期生活概览",
        "",
        f"- 时间范围：{distilled[-1]['date']} ~ {distilled[0]['date']}",
        f"- 总日志条目：{sum(d['total_entries'] for d in distilled)}",
        "",
        "## 每日回顾",
        "",
    ]

    for day in distilled:
        output_lines.append(f"### {day['date']}")
        output_lines.append("")

        # 优先展示 LLM 自然语言摘要
        if day.get("llm_summary"):
            output_lines.append(day["llm_summary"])
        else:
            output_lines.append(f"- 主导情绪：{day['mood_summary']['dominant_mood']}")
            output_lines.append(f"- 平均能量：{day['mood_summary']['avg_energy']}%")
            if day["key_events"]:
                output_lines.append("- 关键事件：")
                output_lines.extend(day["key_events"])

        output_lines.append("")

    soul_memory_file.write_text("\n".join(output_lines), encoding="utf-8")
    mode = "llm" if (llm and llm.available()) else "keyword"
    print(f"Distilled {len(distilled)} days → {soul_memory_file} [{mode} mode]")

    if args.archive:
        archive_threshold = today - timedelta(days=7)
        for log_file in life_log_dir.glob("*.md"):
            try:
                file_date = datetime.strptime(log_file.stem, "%Y-%m-%d").date()
                if file_date < archive_threshold:
                    archive_path = archive_dir / log_file.name
                    log_file.rename(archive_path)
                    print(f"Archived {log_file.name}")
            except ValueError:
                continue


if __name__ == "__main__":
    main()
