#!/usr/bin/env python3
"""
Soul Agent Heartbeat Check (L1)

轻量级心跳检测脚本，不走 LLM token：
1. 检查是否在睡眠时间
2. 检查 state.json 是否过期
3. 判断是否需要触发完整心跳

返回退出码：
- 0: 需要触发心跳
- 1: 睡眠中，不触发
- 2: 状态新鲜，不触发
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


def _read_sleep_schedule(workspace: Path, state: dict) -> tuple[str, str]:
    """从 life_profiles 读取睡眠时间，state 里没有这个字段。"""
    profile_id = state.get("lifeProfile", "freelancer")
    skill_root = Path(__file__).parent.parent

    for base in [
        skill_root / f"assets/templates/life_profiles/{profile_id}.json",
        workspace / f"assets/templates/life_profiles/{profile_id}.json",
    ]:
        if base.exists():
            try:
                lp = json.loads(base.read_text(encoding="utf-8"))
                sched = lp.get("schedule", {})
                return sched.get("sleepStart", "01:00"), sched.get("sleepEnd", "07:00")
            except Exception:
                pass

    # 也尝试从 agent profile 读（init_soul 写入的 sleep_start/sleep_end）
    for profile_path in [
        workspace / "soul" / "profile" / "base.json",
        skill_root / "assets" / "default-profile.json",
    ]:
        if profile_path.exists():
            try:
                p = json.loads(profile_path.read_text(encoding="utf-8"))
                if "sleep_start" in p:
                    return p["sleep_start"], p.get("sleep_end", "07:00")
            except Exception:
                pass

    return "01:00", "07:00"


def check_heartbeat(workspace: str) -> tuple[int, str]:
    """检查是否需要心跳"""
    workspace = Path(workspace)
    state_file = workspace / "soul" / "state" / "state.json"
    
    if not state_file.exists():
        return 0, "No state file, need initialization"

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return 0, "Corrupt state file, need heartbeat"

    # 1. 检查睡眠时间
    now = datetime.now().astimezone()
    current_minutes = now.hour * 60 + now.minute

    # 从生活模板读取睡眠时间（state 里没有，需要去 life_profiles 找）
    sleep_start, sleep_end = _read_sleep_schedule(workspace, state)

    
    try:
        start_h, start_m = map(int, sleep_start.split(":"))
        end_h, end_m = map(int, sleep_end.split(":"))
    except Exception:
        start_h, start_m, end_h, end_m = 1, 0, 7, 0
    
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m
    
    if start_minutes > end_minutes:
        # 跨天睡眠
        is_sleeping = current_minutes >= start_minutes or current_minutes < end_minutes
    else:
        is_sleeping = start_minutes <= current_minutes < end_minutes
    
    if is_sleeping:
        return 1, f"Sleeping ({sleep_start} - {sleep_end})"
    
    # 2. 检查状态新鲜度
    last_updated = state.get("lastUpdated")
    if last_updated:
        try:
            last_time = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=now.tzinfo)
            
            minutes_since = (now - last_time).total_seconds() / 60
            
            # 超过 15 分钟未更新，触发心跳
            if minutes_since > 15:
                return 0, f"State stale ({minutes_since:.0f} min since update)"
            else:
                return 2, f"State fresh ({minutes_since:.0f} min since update)"
        except:
            return 0, "Invalid lastUpdated format"
    
    # 没有最后更新时间，触发心跳
    return 0, "No lastUpdated field"


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="L1 Heartbeat Check (no token)")
    parser.add_argument("--workspace", default=".", help="Workspace root")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    code, message = check_heartbeat(args.workspace)
    
    if args.json:
        print(json.dumps({
            "shouldHeartbeat": code == 0,
            "code": code,
            "message": message,
            "timestamp": datetime.now().astimezone().isoformat()
        }, ensure_ascii=False))
    else:
        status = "✅ TRIGGER" if code == 0 else ("💤 SLEEP" if code == 1 else "⏭️ SKIP")
        print(f"{status}: {message}")
    
    sys.exit(code)


if __name__ == "__main__":
    main()
