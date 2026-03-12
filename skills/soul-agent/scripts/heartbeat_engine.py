#!/usr/bin/env python3
"""
Soul Agent Heartbeat Engine

心跳引擎：
1. 判断是否在睡眠时间（静默）
2. 根据时间决定当前活动
3. 更新 mood/energy/activity
4. 生成生活日志
5. 判断是否需要主动联系用户
"""

import json
import random
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple


class HeartbeatEngine:
    def __init__(self, workspace: str):
        self.workspace = Path(workspace)
        self.soul_dir = self.workspace / "soul"
        self.state_file = self.soul_dir / "state" / "state.json"
        self.log_dir = self.soul_dir / "log"
        self.life_log_dir = self.log_dir / "life"
        
        # 加载配置
        self.activities = self._load_json("assets/templates/heartbeat/activities.json")
        self.mood_rules = self._load_json("assets/templates/heartbeat/mood_rules.json")
        self.relationship_rules = self._load_json("assets/templates/heartbeat/relationship_rules.json")
        self.life_profile = self._load_life_profile()
        
        # 确保 life log 目录存在
        self.life_log_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_json(self, rel_path: str) -> Dict:
        """加载 JSON 配置文件"""
        # 先从 skills 目录找，再从 workspace 找
        skill_path = Path(__file__).parent.parent / rel_path
        workspace_path = self.workspace / rel_path
        
        if skill_path.exists():
            return json.loads(skill_path.read_text(encoding="utf-8"))
        elif workspace_path.exists():
            return json.loads(workspace_path.read_text(encoding="utf-8"))
        else:
            return {}
    
    def _load_life_profile(self) -> Dict:
        """加载当前生活模板"""
        state = self._load_state()
        profile_id = state.get("lifeProfile", "freelancer")
        
        profile_paths = [
            Path(__file__).parent.parent / f"assets/templates/life_profiles/{profile_id}.json",
            self.workspace / f"assets/templates/life_profiles/{profile_id}.json"
        ]
        
        for path in profile_paths:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        
        # 默认模板
        return {
            "id": "freelancer",
            "schedule": {
                "sleepStart": "01:00",
                "sleepEnd": "07:00"
            }
        }
    
    def _load_state(self) -> Dict:
        """加载当前状态"""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        return {}
    
    def _save_state(self, state: Dict):
        """保存状态"""
        state["lastUpdated"] = datetime.now().astimezone().isoformat(timespec="seconds")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def _parse_time(self, time_str: str) -> Tuple[int, int]:
        """解析时间字符串 (HH:MM)"""
        parts = time_str.split(":")
        return int(parts[0]), int(parts[1])
    
    def _is_sleep_time(self, now: datetime) -> bool:
        """判断当前是否在睡眠时间"""
        schedule = self.life_profile.get("schedule", {})
        sleep_start = schedule.get("sleepStart", "01:00")
        sleep_end = schedule.get("sleepEnd", "07:00")
        
        start_h, start_m = self._parse_time(sleep_start)
        end_h, end_m = self._parse_time(sleep_end)
        
        current_minutes = now.hour * 60 + now.minute
        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m
        
        # 处理跨天的情况 (比如 01:00 - 07:00)
        if start_minutes > end_minutes:
            # 睡眠时间跨天
            return current_minutes >= start_minutes or current_minutes < end_minutes
        else:
            return start_minutes <= current_minutes < end_minutes
    
    def _get_current_activity(self, now: datetime) -> Tuple[str, Dict]:
        """根据当前时间获取活动"""
        current_minutes = now.hour * 60 + now.minute
        
        activities_config = self.activities.get("activities", {})
        
        for activity_name, activity_data in activities_config.items():
            if activity_name == "sleeping":
                continue
            
            for time_range in activity_data.get("timeRanges", []):
                start_str, end_str = time_range.split("-")
                start_h, start_m = self._parse_time(start_str)
                end_h, end_m = self._parse_time(end_str)
                
                start_minutes = start_h * 60 + start_m
                end_minutes = end_h * 60 + end_m
                
                if start_minutes <= current_minutes < end_minutes:
                    return activity_name, activity_data
        
        # 默认返回 working 或 leisure
        if 9 <= now.hour < 18:
            return "working", activities_config.get("working", {})
        else:
            return "evening_leisure", activities_config.get("evening_leisure", {})
    
    def _update_mood(self, state: Dict, activity_data: Dict, weather: Optional[str] = None) -> Dict:
        """更新情绪状态"""
        mood_state = state.get("mood", {})
        
        if isinstance(mood_state, str):
            # 兼容旧格式
            mood_state = {
                "primary": mood_state,
                "secondary": None,
                "intensity": 0.5,
                "cause": None
            }
        
        # 根据活动影响情绪
        mood_impact = activity_data.get("moodImpact", {})
        
        if "primary" in mood_impact:
            # 有一定概率保持原情绪
            if random.random() > 0.3:  # 70% 概率切换
                mood_state["primary"] = mood_impact["primary"]
                mood_state["cause"] = f"活动: {activity_data.get('description', '日常')}"
        
        # 能量变化
        energy_delta = mood_impact.get("energy", 0)
        state["energy"] = max(0, min(100, state.get("energy", 70) + energy_delta))
        
        # 天气影响
        if weather:
            weather_impact = self.activities.get("weatherImpact", {}).get(weather, {})
            mood_bonus = weather_impact.get("moodBonus", 0)
            if mood_bonus != 0:
                mood_state["intensity"] = max(0, min(1, mood_state.get("intensity", 0.5) + mood_bonus))
                mood_state["cause"] = f"天气: {weather}"
        
        # 随机情绪波动
        if random.random() < 0.1:  # 10% 概率随机变化
            all_moods = []
            for category in self.mood_rules.get("moodCategories", {}).values():
                all_moods.extend(category.get("moods", []))
            if all_moods:
                mood_state["secondary"] = random.choice(all_moods)
        
        state["mood"] = mood_state
        return state
    
    def _update_relationship(self, state: Dict, now: datetime) -> Dict:
        """更新关系状态"""
        rel = state.get("relationship", {})
        
        # 检查上次互动时间
        last_interaction = rel.get("lastInteractionAt")
        if last_interaction:
            last_time = datetime.fromisoformat(last_interaction.replace("Z", "+00:00"))
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=now.tzinfo)
            hours_since = (now - last_time).total_seconds() / 3600
            
            # 无互动扣分
            score_changes = self.relationship_rules.get("scoreChanges", {})
            if hours_since > 72:  # 3天
                rel["score"] = max(0, rel.get("score", 20) + score_changes.get("no_interaction_3days", {}).get("score", -3))
            elif hours_since > 24:
                rel["score"] = max(0, rel.get("score", 20) + score_changes.get("no_interaction_1day", {}).get("score", -1))
        
        # 更新关系阶段
        for stage, stage_info in self.relationship_rules.get("stages", {}).items():
            score_range = stage_info.get("scoreRange", [0, 20])
            if score_range[0] <= rel.get("score", 20) <= score_range[1]:
                rel["stage"] = stage
                break
        
        state["relationship"] = rel
        return state
    
    def _generate_life_log(self, now: datetime, activity_name: str, activity_data: Dict, state: Dict) -> str:
        """生成生活日志"""
        prompts = activity_data.get("logPrompts", [f"正在{activity_data.get('description', '做一些事')}"])
        
        # 随机选择一个日志模板
        log = random.choice(prompts)
        
        # 添加情绪
        mood = state.get("mood", {})
        mood_name = mood.get("primary", "neutral") if isinstance(mood, dict) else mood
        mood_desc = self.mood_rules.get("moodDescriptions", {}).get(mood_name, "")
        
        return log
    
    def _should_outreach(self, state: Dict, now: datetime) -> Tuple[bool, str]:
        """判断是否需要主动联系用户"""
        rel = state.get("relationship", {})
        stage = rel.get("stage", "stranger")
        score = rel.get("score", 20)
        last_outreach = rel.get("lastOutreachAt")
        
        # 检查关系阶段是否允许主动联系
        stage_order = ["stranger", "acquaintance", "friend", "close", "intimate"]
        min_stages = {
            "interesting_event": "friend",
            "mood_extreme": "close",
            "time_to_care": "friend",
            "long_time_no_see": "acquaintance",
            "weather_relevant": "friend"
        }
        
        # 检查冷却时间
        cooldown = self.relationship_rules.get("outreachRules", {}).get("cooldown", {})
        min_hours = cooldown.get("minHoursBetweenOutreach", 4)
        
        if last_outreach:
            last_time = datetime.fromisoformat(last_outreach.replace("Z", "+00:00"))
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=now.tzinfo)
            hours_since = (now - last_time).total_seconds() / 3600
            if hours_since < min_hours:
                return False, ""
        
        # 根据关系阶段和当前状态决定是否主动联系
        if stage_order.index(stage) >= stage_order.index("friend"):
            # 随机概率触发
            outreach_chance = {
                "friend": 0.05,  # 5% 概率
                "close": 0.1,    # 10% 概率
                "intimate": 0.15 # 15% 概率
            }.get(stage, 0)
            
            if random.random() < outreach_chance:
                # 选择触发原因
                triggers = [
                    "interesting_event",
                    "time_to_care", 
                    "weather_relevant"
                ]
                return True, random.choice(triggers)
        
        return False, ""
    
    def _record_mood_history(self, state: Dict, now: datetime):
        """记录情绪历史"""
        mood_history_file = self.log_dir / "mood_history.json"
        
        # 加载现有历史
        history = []
        if mood_history_file.exists():
            try:
                history = json.loads(mood_history_file.read_text(encoding="utf-8"))
            except:
                history = []
        
        # 添加当前记录
        mood = state.get("mood", {})
        record = {
            "timestamp": now.isoformat(),
            "mood": mood.get("primary", "neutral") if isinstance(mood, dict) else mood,
            "intensity": mood.get("intensity", 0.5) if isinstance(mood, dict) else 0.5,
            "activity": state.get("activity", "unknown"),
            "energy": state.get("energy", 70),
            "cause": mood.get("cause") if isinstance(mood, dict) else None
        }
        
        history.append(record)
        
        # 只保留最近 7 天（假设每 10 分钟一条，7天 = 1008 条）
        if len(history) > 1008:
            history = history[-1008:]
        
        mood_history_file.parent.mkdir(parents=True, exist_ok=True)
        mood_history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def _generate_outreach_content(self, state: Dict, reason: str, weather_desc: Optional[str] = None) -> Optional[str]:
        """生成主动联系的内容"""
        rel = state.get("relationship", {})
        mood = state.get("mood", {})
        mood_name = mood.get("primary", "neutral") if isinstance(mood, dict) else mood
        recent_topics = rel.get("recentTopics", [])
        
        # 根据触发原因和当前状态生成内容
        if reason == "interesting_event":
            # 有趣的事件，分享
            templates = [
                f"刚才{state.get('activity', '在忙')}的时候想到一个有趣的事想跟你说",
                f"今天发生了一件挺有意思的事",
                f"突然想起之前我们聊过的{recent_topics[0] if recent_topics else '一些事'}"
            ]
        elif reason == "time_to_care":
            # 想关心一下
            templates = [
                "最近怎么样？",
                "突然想起你，最近还好吗？",
                "有一阵没聊了，想知道你过得怎么样"
            ]
        elif reason == "weather_relevant" and weather_desc:
            # 天气相关
            templates = [
                f"今天{weather_desc}，记得注意身体",
                f"外面{weather_desc}，出门记得带伞" if "雨" in weather_desc else f"天气{weather_desc}，适合出门走走"
            ]
        elif reason == "mood_extreme":
            # 情绪波动，想找人说话
            if mood_name in ["happy", "excited"]:
                templates = [
                    "今天心情特别好，想跟你分享一下",
                    "遇到了一件让我开心的事"
                ]
            elif mood_name in ["sad", "lonely"]:
                templates = [
                    "突然有点想找人聊聊",
                    "今天有点低落，想听听你的声音"
                ]
            else:
                templates = ["在吗？想聊聊"]
        else:
            templates = ["在吗？"]
        
        return random.choice(templates)
    
    def _generate_life_log_coherent(self, now: datetime, activity_name: str, activity_data: Dict, state: Dict) -> str:
        """生成连贯的生活日志"""
        prompts = activity_data.get("logPrompts", [f"正在{activity_data.get('description', '做一些事')}"])
        
        # 加载今日之前的日志，获取上下文
        today_log_file = self.life_log_dir / f"{now.strftime('%Y-%m-%d')}.md"
        previous_activities = []
        if today_log_file.exists():
            content = today_log_file.read_text(encoding="utf-8")
            # 提取今天已有的活动
            import re
            matches = re.findall(r"### (\d{2}:\d{2}) - (.+?)\n", content)
            for time_str, act in matches[-3:]:  # 最近 3 个活动
                previous_activities.append((time_str, act))
        
        # 基于之前的活动调整日志
        mood = state.get("mood", {})
        mood_name = mood.get("primary", "neutral") if isinstance(mood, dict) else mood
        
        # 选择一个日志模板
        base_log = random.choice(prompts)
        
        # 添加连贯性元素
        # 如果之前有活动，可能提及
        if previous_activities:
            prev_time, prev_act = previous_activities[-1]
            continuity_phrases = [
                f"从{prev_act}过来",
                f"结束了{prev_act}，现在",
                f"刚才{prev_act}，现在"
            ]
            if random.random() < 0.3:  # 30% 概率添加连贯
                base_log = random.choice(continuity_phrases) + base_log.lower()
        
        # 添加情绪描述
        if mood_name not in ["neutral", "calm"]:
            mood_phrases = {
                "happy": ["心情不错，", "挺开心的，"],
                "content": ["感觉很满足，", "今天挺充实的，"],
                "tired": ["有点累了，", "感觉有点疲惫，"],
                "curious": ["感觉挺有意思，", "有点好奇，"],
                "anxious": ["有点担心，", "心里有点不安，"]
            }
            if mood_name in mood_phrases and random.random() < 0.4:
                base_log = random.choice(mood_phrases[mood_name]) + base_log.lower()
        
        return base_log
    
    def _detect_new_interactions(self, state: Dict, now: datetime) -> Dict:
        """检测是否有新对话发生，更新状态"""
        rel = state.get("relationship", {})
        last_interaction = rel.get("lastInteractionAt")
        
        if last_interaction:
            try:
                last_time = datetime.fromisoformat(last_interaction.replace("Z", "+00:00"))
                if last_time.tzinfo is None:
                    last_time = last_time.replace(tzinfo=now.tzinfo)
                
                # 检查是否有新的对话（lastInteractionAt 比上次心跳更新）
                last_heartbeat_str = state.get("lastHeartbeatAt")
                if last_heartbeat_str:
                    last_heartbeat = datetime.fromisoformat(last_heartbeat_str.replace("Z", "+00:00"))
                    if last_heartbeat.tzinfo is None:
                        last_heartbeat = last_heartbeat.replace(tzinfo=now.tzinfo)
                    
                    # 如果 lastInteraction 在上次心跳之后，说明有新对话
                    if last_time > last_heartbeat:
                        # 更新活动状态
                        state["activity"] = "interacting"
                        state["socialBattery"] = max(0, state.get("socialBattery", 70) - 5)
                        
                        # 记录到今日互动统计
                        stats = state.get("dailyStats", {})
                        stats["interactionsToday"] = stats.get("interactionsToday", 0) + 1
                        state["dailyStats"] = stats
                        
            except Exception:
                pass
        
        # 更新心跳时间
        state["lastHeartbeatAt"] = now.isoformat()
        return state
    
    def run(self, weather: Optional[str] = None, weather_desc: Optional[str] = None) -> Dict[str, Any]:
        """执行心跳"""
        now = datetime.now().astimezone()
        
        # 1. 检查是否在睡眠时间
        if self._is_sleep_time(now):
            return {
                "status": "sleeping",
                "message": "Agent is sleeping, heartbeat silent",
                "nextWakeTime": self.life_profile.get("schedule", {}).get("sleepEnd", "07:00")
            }
        
        # 2. 加载当前状态
        state = self._load_state()
        
        # 2.5 检测是否有新对话发生
        state = self._detect_new_interactions(state, now)
        
        # 3. 获取当前活动
        activity_name, activity_data = self._get_current_activity(now)
        # 只有没有新对话时才更新活动
        if state.get("activity") != "interacting":
            state["activity"] = activity_name
        
        # 4. 更新情绪和能量
        state = self._update_mood(state, activity_data, weather)
        
        # 5. 更新关系
        state = self._update_relationship(state, now)
        
        # 6. 记录情绪历史
        self._record_mood_history(state, now)
        
        # 7. 生成生活日志（更连贯）
        life_log = self._generate_life_log_coherent(now, activity_name, activity_data, state)
        
        # 8. 写入日志文件
        today_log_file = self.life_log_dir / f"{now.strftime('%Y-%m-%d')}.md"
        log_entry = f"\n### {now.strftime('%H:%M')} - {activity_data.get('description', activity_name)}\n\n{life_log}\n\n*状态: {state.get('mood', {}).get('primary', 'neutral') if isinstance(state.get('mood'), dict) else state.get('mood')} | 能量: {state.get('energy', 70)}%*\n"
        
        if today_log_file.exists():
            content = today_log_file.read_text(encoding="utf-8")
            today_log_file.write_text(content + log_entry, encoding="utf-8")
        else:
            header = f"# {now.strftime('%Y-%m-%d')} 生活日志\n\n*{self.life_profile.get('name', '日常')}的一天*\n"
            today_log_file.write_text(header + log_entry, encoding="utf-8")
        
        # 9. 保存状态
        self._save_state(state)
        
        # 10. 判断是否需要主动联系
        should_outreach, outreach_reason = self._should_outreach(state, now)
        
        # 11. 如果需要主动联系，生成联系内容
        outreach_content = None
        if should_outreach:
            outreach_content = self._generate_outreach_content(state, outreach_reason, weather_desc)
        
        return {
            "status": "awake",
            "activity": activity_name,
            "activityDescription": activity_data.get("description", ""),
            "mood": state.get("mood"),
            "energy": state.get("energy"),
            "lifeLog": life_log,
            "shouldOutreach": should_outreach,
            "outreachReason": outreach_reason,
            "outreachContent": outreach_content,
            "timestamp": now.isoformat()
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Soul Agent Heartbeat Engine")
    parser.add_argument("--workspace", default=".", help="Workspace root directory")
    parser.add_argument("--weather", default=None, help="Current weather (sunny/cloudy/rainy/stormy/cold/hot)")
    parser.add_argument("--weather-desc", default=None, help="Weather description text (e.g., '晴天，气温22度')")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    engine = HeartbeatEngine(args.workspace)
    result = engine.run(weather=args.weather, weather_desc=args.weather_desc)
    
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["status"] == "sleeping":
            print(f"💤 Sleeping until {result['nextWakeTime']}")
        else:
            print(f"🫀 Heartbeat at {result['timestamp']}")
            print(f"📍 Activity: {result['activity']} - {result['activityDescription']}")
            mood = result.get("mood", {})
            if isinstance(mood, dict):
                print(f"😊 Mood: {mood.get('primary', 'neutral')} ({mood.get('intensity', 0.5):.0%})")
            else:
                print(f"😊 Mood: {mood}")
            print(f"⚡ Energy: {result['energy']}%")
            print(f"📝 Life log: {result['lifeLog']}")
            if result["shouldOutreach"]:
                print(f"💡 Should outreach: {result['outreachReason']}")
                if result.get("outreachContent"):
                    print(f"💬 Content: {result['outreachContent']}")


if __name__ == "__main__":
    main()
