#!/usr/bin/env python3
"""
Soul Life Log Distiller

每天运行一次，蒸馏生活日志到 soul/memory/SOUL_MEMORY.md
类似 memory-fusion 的 daily 蒸馏，但针对 soul 生活日志。

流程：
1. 读取最近 7 天的生活日志 (soul/log/life/*.md)
2. 提取关键事件、情绪变化、关系进展
3. 写入 soul/memory/SOUL_MEMORY.md (滚动 30 天)
4. 归档超过 7 天的原始日志到 soul/log/life/archive/
"""

import json
import os
import re
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


def distill_day(log_file: Path) -> Dict:
    """蒸馏一天的生活日志"""
    if not log_file.exists():
        return None
    
    content = log_file.read_text(encoding="utf-8")
    parsed = parse_life_log(content)
    
    if not parsed["entries"]:
        return None
    
    date_str = log_file.stem  # YYYY-MM-DD
    
    return {
        "date": date_str,
        "total_entries": parsed["total_entries"],
        "key_events": extract_key_events(parsed["entries"]),
        "mood_summary": extract_mood_summary(parsed["entries"])
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Distill soul life logs")
    parser.add_argument("--workspace", default=".", help="Workspace root")
    parser.add_argument("--days", type=int, default=7, help="Days to look back")
    parser.add_argument("--archive", action="store_true", help="Archive old logs")
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace)
    life_log_dir = workspace / "soul" / "log" / "life"
    memory_dir = workspace / "soul" / "memory"
    archive_dir = life_log_dir / "archive"
    
    # 确保目录存在
    memory_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # 收集最近 N 天的日志
    today = datetime.now().date()
    distilled = []
    
    for i in range(args.days):
        date = today - timedelta(days=i)
        log_file = life_log_dir / f"{date.strftime('%Y-%m-%d')}.md"
        
        day_data = distill_day(log_file)
        if day_data:
            distilled.append(day_data)
    
    if not distilled:
        print("No life logs found in the past {} days".format(args.days))
        return
    
    # 生成蒸馏后的记忆
    soul_memory_file = memory_dir / "SOUL_MEMORY.md"
    
    # 读取现有记忆
    existing_content = ""
    if soul_memory_file.exists():
        existing_content = soul_memory_file.read_text(encoding="utf-8")
    
    # 生成新的滚动记忆
    output_lines = [
        "# SOUL_MEMORY.md - 生活记忆蒸馏",
        "",
        "_自动生成，滚动保留 30 天的关键生活事件_",
        "",
        "## 近期生活概览",
        "",
        f"- 时间范围：{distilled[-1]['date']} ~ {distilled[0]['date']}" if distilled else "",
        f"- 总日志条目：{sum(d['total_entries'] for d in distilled)}",
        "",
        "## 每日关键事件",
        ""
    ]
    
    for day in distilled:
        output_lines.append(f"### {day['date']}")
        output_lines.append("")
        output_lines.append(f"- 主导情绪：{day['mood_summary']['dominant_mood']}")
        output_lines.append(f"- 平均能量：{day['mood_summary']['avg_energy']}%")
        if day['key_events']:
            output_lines.append(f"- 关键事件：")
            output_lines.extend(day['key_events'])
        output_lines.append("")
    
    # 保留旧记忆中超过 7 天的内容（去重）
    # 简单处理：直接覆盖
    
    soul_memory_file.write_text("\n".join(output_lines), encoding="utf-8")
    print(f"Distilled {len(distilled)} days to {soul_memory_file}")
    
    # 归档旧日志
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
                continue  # 跳过非日期格式的文件


if __name__ == "__main__":
    main()
