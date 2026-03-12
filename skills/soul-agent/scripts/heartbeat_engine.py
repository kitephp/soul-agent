#!/usr/bin/env python3
"""
Soul Agent Heartbeat Engine (v2 - Generative)

架构升级（参考 Smallville Generative Agents）：

旧版：随机模板 → 碎片化日志
新版：每日计划 + 记忆流 + LLM 叙事 → 连贯日志

核心流程：
1. 检查睡眠时间（静默）
2. 加载/生成今日计划（每天一次，早晨生成）
3. 读取今日已有日志条目作为上下文
4. 用 LLM 生成当前时刻的连贯日记条目（降级：模板）
5. 更新情绪/能量（平滑过渡，不机械跳变）
6. 写入日志 & 保存状态
7. 判断是否主动联系用户
"""

import json
import random
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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
        self.profile = self._load_profile()
        self.life_profile = self._load_life_profile()

        # 延迟初始化（避免导入失败）
        self._llm = None
        self._plan_gen = None

        self.life_log_dir.mkdir(parents=True, exist_ok=True)

    # ─── 配置加载 ──────────────────────────────────────────────────────────────

    def _load_json(self, rel_path: str) -> Dict:
        skill_path = Path(__file__).parent.parent / rel_path
        workspace_path = self.workspace / rel_path
        for p in [skill_path, workspace_path]:
            if p.exists():
                try:
                    return json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    pass
        return {}

    def _load_profile(self) -> Dict:
        """加载 agent 个人档案（display_name, city, vibe 等）"""
        for candidate in [
            self.soul_dir / "profile" / "base.json",
            self.workspace / "soul" / "profile" / "base.json",
            Path(__file__).parent.parent / "assets" / "default-profile.json",
        ]:
            if candidate.exists():
                try:
                    return json.loads(candidate.read_text(encoding="utf-8"))
                except Exception:
                    pass
        return {}

    def _load_life_profile(self) -> Dict:
        state = self._load_state()
        profile_id = state.get("lifeProfile") or self.profile.get("life_profile", "freelancer")
        for base in [
            Path(__file__).parent.parent / f"assets/templates/life_profiles/{profile_id}.json",
            self.workspace / f"assets/templates/life_profiles/{profile_id}.json",
        ]:
            if base.exists():
                try:
                    return json.loads(base.read_text(encoding="utf-8"))
                except Exception:
                    pass
        return {"id": "freelancer", "schedule": {"sleepStart": "01:00", "sleepEnd": "07:00"}}

    def _load_state(self) -> Dict:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save_state(self, state: Dict):
        state["lastUpdated"] = datetime.now().astimezone().isoformat(timespec="seconds")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    # ─── 时间 & 活动 ──────────────────────────────────────────────────────────

    def _parse_time(self, time_str: str) -> Tuple[int, int]:
        parts = time_str.split(":")
        return int(parts[0]), int(parts[1])

    def _is_sleep_time(self, now: datetime) -> bool:
        schedule = self.life_profile.get("schedule", {})
        sleep_start = schedule.get("sleepStart", "01:00")
        sleep_end = schedule.get("sleepEnd", "07:00")

        sh, sm = self._parse_time(sleep_start)
        eh, em = self._parse_time(sleep_end)
        cur = now.hour * 60 + now.minute
        start = sh * 60 + sm
        end = eh * 60 + em

        if start > end:
            return cur >= start or cur < end
        return start <= cur < end

    def _get_current_activity(self, now: datetime) -> Tuple[str, Dict]:
        cur = now.hour * 60 + now.minute
        for name, data in self.activities.get("activities", {}).items():
            if name == "sleeping":
                continue
            for tr in data.get("timeRanges", []):
                s, e = tr.split("-")
                sh, sm = self._parse_time(s)
                eh, em = self._parse_time(e)
                if sh * 60 + sm <= cur < eh * 60 + em:
                    return name, data
        fallback = "working" if 9 <= now.hour < 18 else "evening_leisure"
        return fallback, self.activities.get("activities", {}).get(fallback, {})

    # ─── 情绪 & 能量（平滑过渡，非机械跳变）─────────────────────────────────

    def _update_mood(self, state: Dict, activity_data: Dict, weather: Optional[str] = None) -> Dict:
        mood = state.get("mood", {})
        if isinstance(mood, str):
            mood = {"primary": mood, "secondary": None, "intensity": 0.5, "cause": None}

        impact = activity_data.get("moodImpact", {})

        # 目标情绪：只在一定概率下切换，避免每次都变
        if "primary" in impact and random.random() < 0.35:
            mood["primary"] = impact["primary"]
            mood["cause"] = f"活动: {activity_data.get('description', '日常')}"

        # 能量：向目标值平滑靠近，而不是固定 ±N
        energy_delta = impact.get("energy", 0)
        current_energy = state.get("energy", 70)
        # 小步移动（最多变化 5），加轻微噪声
        step = max(-5, min(5, energy_delta)) + random.randint(-2, 2)
        state["energy"] = max(5, min(100, current_energy + step))

        # 天气影响情绪强度
        if weather:
            bonus = self.activities.get("weatherImpact", {}).get(weather, {}).get("moodBonus", 0)
            mood["intensity"] = max(0.0, min(1.0, mood.get("intensity", 0.5) + bonus))

        # 极低概率的随机情绪插曲（5%）
        if random.random() < 0.05:
            all_moods = []
            for cat in self.mood_rules.get("moodCategories", {}).values():
                all_moods.extend(cat.get("moods", []))
            if all_moods:
                mood["secondary"] = random.choice(all_moods)

        state["mood"] = mood
        return state

    # ─── 关系 ─────────────────────────────────────────────────────────────────

    def _update_relationship(self, state: Dict, now: datetime) -> Dict:
        rel = state.get("relationship", {})
        last = rel.get("lastInteractionAt")
        if last:
            try:
                lt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                if lt.tzinfo is None:
                    lt = lt.replace(tzinfo=now.tzinfo)
                hours = (now - lt).total_seconds() / 3600
                changes = self.relationship_rules.get("scoreChanges", {})
                if hours > 72:
                    rel["score"] = max(0, rel.get("score", 20) + changes.get("no_interaction_3days", {}).get("score", -3))
                elif hours > 24:
                    rel["score"] = max(0, rel.get("score", 20) + changes.get("no_interaction_1day", {}).get("score", -1))
            except Exception:
                pass

        for stage, info in self.relationship_rules.get("stages", {}).items():
            sr = info.get("scoreRange", [0, 20])
            if len(sr) >= 2 and sr[0] <= rel.get("score", 20) <= sr[1]:
                rel["stage"] = stage
                break

        state["relationship"] = rel
        return state

    # ─── 今日日志上下文 ───────────────────────────────────────────────────────

    def _load_today_entries(self, date: datetime, max_entries: int = 5) -> List[Dict]:
        """读取今日已有日志条目，供 LLM 作为上下文"""
        log_file = self.life_log_dir / f"{date.strftime('%Y-%m-%d')}.md"
        if not log_file.exists():
            return []

        content = log_file.read_text(encoding="utf-8")
        matches = re.findall(
            r"### (\d{2}:\d{2}) - (.+?)\n\n(.+?)\n\n\*状态:",
            content,
            re.DOTALL,
        )
        entries = []
        for time_str, activity, text in matches:
            entries.append({
                "time": time_str,
                "activity": activity.strip(),
                "text": text.strip().replace("\n", " ")[:120],
            })
        return entries[-max_entries:]  # 最近 N 条

    # ─── 核心：LLM 叙事生成 ───────────────────────────────────────────────────

    def _get_llm(self):
        if self._llm is None:
            try:
                sys.path.insert(0, str(Path(__file__).parent))
                from llm_client import LLMClient
                self._llm = LLMClient(str(self.workspace))
            except Exception:
                self._llm = False
        return self._llm if self._llm is not False else None

    def _get_plan_gen(self):
        if self._plan_gen is None:
            try:
                sys.path.insert(0, str(Path(__file__).parent))
                from plan_generator import PlanGenerator
                self._plan_gen = PlanGenerator(str(self.workspace))
            except Exception:
                self._plan_gen = False
        return self._plan_gen if self._plan_gen is not False else None

    def _get_today_plan(self, now: datetime, state: Dict) -> Dict:
        """获取今日计划（不存在则生成）"""
        gen = self._get_plan_gen()
        if gen:
            try:
                return gen.get_or_generate(now, self.profile, state)
            except Exception:
                pass
        return {}

    def _plan_summary(self, plan: Dict) -> str:
        gen = self._get_plan_gen()
        if gen and plan:
            try:
                return gen.summary(plan)
            except Exception:
                pass
        parts = []
        for k in ("mood_baseline", "lunch_plan", "work_focus", "evening_plan", "special_notes"):
            v = plan.get(k, "")
            if v:
                parts.append(v)
        return "；".join(parts)

    def _generate_narrative(
        self,
        now: datetime,
        activity_name: str,
        activity_data: Dict,
        state: Dict,
        plan: Dict,
        today_entries: List[Dict],
        weather: Optional[str] = None,
        weather_desc: Optional[str] = None,
    ) -> str:
        """
        用 LLM 生成连贯的日记条目。
        降级链：LLM → 上下文感知模板 → 纯随机模板
        """
        llm = self._get_llm()
        if llm and llm.available():
            result = self._llm_narrative(
                llm, now, activity_name, activity_data, state, plan, today_entries,
                weather=weather, weather_desc=weather_desc,
            )
            if result:
                return result

        # 降级：上下文感知模板
        return self._template_narrative(now, activity_name, activity_data, state, today_entries, plan)

    def _llm_narrative(
        self,
        llm,
        now: datetime,
        activity_name: str,
        activity_data: Dict,
        state: Dict,
        plan: Dict,
        today_entries: List[Dict],
        weather: Optional[str] = None,
        weather_desc: Optional[str] = None,
    ) -> Optional[str]:
        name = self.profile.get("display_name", "我")
        city = self.profile.get("city", "上海")
        occupation = self.profile.get("occupation", "自由职业者")
        vibe = self.profile.get("vibe", "随性、真诚")
        hobbies = self.profile.get("hobbies", "")

        mood = state.get("mood", {})
        mood_name = mood.get("primary", "neutral") if isinstance(mood, dict) else str(mood)
        mood_desc = self.mood_rules.get("moodDescriptions", {}).get(mood_name, "")
        energy = state.get("energy", 70)

        activity_desc = activity_data.get("description", activity_name)
        plan_text = self._plan_summary(plan)

        # 今日上下文
        context_lines = ""
        if today_entries:
            context_lines = "\n".join(
                f"- {e['time']} [{e['activity']}] {e['text']}"
                for e in today_entries
            )

        system = (
            f"你是{name}，{occupation}，住在{city}。"
            f"性格：{vibe}。"
            f"{'爱好：' + hobbies + '。' if hobbies else ''}"
            "你在写私人日记，语言自然随意，有生活质感。"
            "不要太文艺，不要假装完美。1-2句话，不超过50字。只输出日记内容，不要引号。"
        )

        # 天气描述（归一化为纯文字，不含前缀）
        weather_text = ""
        if weather_desc:
            weather_text = weather_desc
        elif weather:
            weather_zh = {
                "sunny": "晴天", "cloudy": "多云", "rainy": "下雨",
                "stormy": "暴风雨", "cold": "很冷", "hot": "很热",
            }
            weather_text = weather_zh.get(weather, weather)

        prompt = (
            f"现在是{now.strftime('%H:%M')}，你正在：{activity_desc}。\n"
            f"{'今天天气：' + weather_text + '。' if weather_text else ''}\n"
            f"今天的计划：{plan_text}\n"
            f"当前心情：{mood_name}（{mood_desc}），能量：{energy}%\n"
            f"{'今天已发生的事：\n' + context_lines if context_lines else '今天是第一条日志。'}\n\n"
            f"写一条此刻的日记。要和今天已发生的事保持连贯，"
            f"可以提及计划里的具体内容（比如具体去哪吃、做什么）或天气，"
            f"不要重复刚才发生过的事。"
        )

        try:
            result = llm.generate(prompt, max_tokens=80, system=system)
            if result and len(result) > 5:
                # 去除可能的引号包裹
                result = result.strip('"').strip("'").strip("「」").strip()
                return result
        except Exception:
            pass
        return None

    def _template_narrative(
        self,
        now: datetime,
        activity_name: str,
        activity_data: Dict,
        state: Dict,
        today_entries: List[Dict],
        plan: Dict,
    ) -> str:
        """上下文感知的模板降级（比纯随机好）"""
        prompts = activity_data.get("logPrompts", [f"正在{activity_data.get('description', '做一些事')}"])

        # 优先使用计划里的具体内容
        if activity_name == "lunch" and plan.get("lunch_plan"):
            # 有计划时，围绕计划生成
            plan_ref = plan["lunch_plan"]
            templates_with_plan = [
                f"{plan_ref}",
                f"按计划，{plan_ref}",
            ]
            prompts = templates_with_plan + prompts

        if activity_name == "evening_leisure" and plan.get("evening_plan"):
            plan_ref = plan["evening_plan"]
            prompts = [plan_ref, f"晚上{plan_ref}"] + prompts

        base = random.choice(prompts)

        # 连贯性：30% 概率引用上一条
        if today_entries and random.random() < 0.3:
            prev = today_entries[-1]
            connectors = [
                f"从{prev['activity']}过来，",
                f"刚结束{prev['activity']}，",
            ]
            base = random.choice(connectors) + base[:1].lower() + base[1:]

        # 情绪修饰：25% 概率添加
        mood = state.get("mood", {})
        mood_name = mood.get("primary", "neutral") if isinstance(mood, dict) else str(mood)
        mood_prefixes = {
            "happy": ["心情挺好，", "状态不错，"],
            "tired": ["有点累，", "整个人懒懒的，"],
            "anxious": ["有点焦虑，", "心里有点不安，"],
            "bored": ["无聊得很，", "有点发呆，"],
            "content": ["挺满足的，", "感觉还不错，"],
        }
        if mood_name in mood_prefixes and random.random() < 0.25:
            base = random.choice(mood_prefixes[mood_name]) + base[:1].lower() + base[1:]

        return base

    # ─── 情绪历史 ─────────────────────────────────────────────────────────────

    def _record_mood_history(self, state: Dict, now: datetime):
        history_file = self.log_dir / "mood_history.json"
        history = []
        if history_file.exists():
            try:
                history = json.loads(history_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        mood = state.get("mood", {})
        history.append({
            "timestamp": now.isoformat(),
            "mood": mood.get("primary", "neutral") if isinstance(mood, dict) else mood,
            "intensity": mood.get("intensity", 0.5) if isinstance(mood, dict) else 0.5,
            "activity": state.get("activity", "unknown"),
            "energy": state.get("energy", 70),
            "cause": mood.get("cause") if isinstance(mood, dict) else None,
        })

        # 保留最近 1008 条（约 7 天）
        if len(history) > 1008:
            history = history[-1008:]

        history_file.parent.mkdir(parents=True, exist_ok=True)
        history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

    # ─── 主动联系 ─────────────────────────────────────────────────────────────

    def _should_outreach(self, state: Dict, now: datetime) -> Tuple[bool, str]:
        rel = state.get("relationship", {})
        stage = rel.get("stage", "stranger")
        last_outreach = rel.get("lastOutreachAt")

        cooldown_hours = self.relationship_rules.get("outreachRules", {}).get("cooldown", {}).get("minHoursBetweenOutreach", 4)
        if last_outreach:
            try:
                lt = datetime.fromisoformat(last_outreach.replace("Z", "+00:00"))
                if lt.tzinfo is None:
                    lt = lt.replace(tzinfo=now.tzinfo)
                if (now - lt).total_seconds() / 3600 < cooldown_hours:
                    return False, ""
            except Exception:
                pass

        stage_order = ["stranger", "acquaintance", "friend", "close", "intimate"]
        if stage not in stage_order or stage_order.index(stage) < stage_order.index("friend"):
            return False, ""

        chance = {"friend": 0.05, "close": 0.10, "intimate": 0.15}.get(stage, 0)
        if random.random() < chance:
            return True, random.choice(["interesting_event", "time_to_care", "weather_relevant"])
        return False, ""

    def _generate_outreach_content(self, state: Dict, reason: str, weather_desc: Optional[str] = None) -> Optional[str]:
        rel = state.get("relationship", {})
        mood = state.get("mood", {})
        mood_name = mood.get("primary", "neutral") if isinstance(mood, dict) else mood
        recent_topics = rel.get("recentTopics", [])

        if reason == "interesting_event":
            templates = [
                f"刚才{state.get('activity', '在忙')}的时候想到一个有趣的事想跟你说",
                f"今天发生了一件挺有意思的事",
                f"突然想起之前聊过的{recent_topics[0] if recent_topics else '一些事'}",
            ]
        elif reason == "time_to_care":
            templates = ["最近怎么样？", "突然想起你，最近还好吗？", "有一阵没聊了，想知道你过得怎么样"]
        elif reason == "weather_relevant" and weather_desc:
            templates = [
                f"今天{weather_desc}，记得注意身体",
                f"外面{weather_desc}，出门记得带伞" if "雨" in weather_desc else f"天气{weather_desc}，适合出门走走",
            ]
        elif reason == "mood_extreme":
            if mood_name in ["happy", "excited"]:
                templates = ["今天心情特别好，想跟你分享一下", "遇到了一件让我开心的事"]
            elif mood_name in ["sad", "lonely"]:
                templates = ["突然有点想找人聊聊", "今天有点低落，想听听你的声音"]
            else:
                templates = ["在吗？想聊聊"]
        else:
            templates = ["在吗？"]

        return random.choice(templates)

    # ─── 交互检测 ─────────────────────────────────────────────────────────────

    def _detect_new_interactions(self, state: Dict, now: datetime) -> Dict:
        # 跨天 reset dailyStats
        stats = state.get("dailyStats", {})
        last_stats_date = stats.get("date", "")
        today_str = now.strftime("%Y-%m-%d")
        if last_stats_date != today_str:
            stats = {"date": today_str, "interactionsToday": 0}
            state["dailyStats"] = stats

        rel = state.get("relationship", {})
        last_interaction = rel.get("lastInteractionAt")
        new_interaction = False

        if last_interaction:
            try:
                lt = datetime.fromisoformat(last_interaction.replace("Z", "+00:00"))
                if lt.tzinfo is None:
                    lt = lt.replace(tzinfo=now.tzinfo)
                last_hb_str = state.get("lastHeartbeatAt")
                if last_hb_str:
                    lhb = datetime.fromisoformat(last_hb_str.replace("Z", "+00:00"))
                    if lhb.tzinfo is None:
                        lhb = lhb.replace(tzinfo=now.tzinfo)
                    if lt > lhb:
                        # 有新对话发生
                        new_interaction = True
                        state["activity"] = "interacting"
                        state["socialBattery"] = max(0, state.get("socialBattery", 70) - 5)
                        stats["interactionsToday"] = stats.get("interactionsToday", 0) + 1
                        state["dailyStats"] = stats
            except Exception:
                pass

        # 如果没有新对话，且当前状态是 "interacting"，清除回正常
        # 防止对话结束后状态被锁死在 "interacting"
        if not new_interaction and state.get("activity") == "interacting":
            state.pop("activity", None)  # 让后续逻辑重新基于时间分配活动

        state["lastHeartbeatAt"] = now.isoformat()
        return state

    # ─── 主入口 ───────────────────────────────────────────────────────────────

    def run(self, weather: Optional[str] = None, weather_desc: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.now().astimezone()

        # 1. 睡眠检查
        if self._is_sleep_time(now):
            return {
                "status": "sleeping",
                "message": "Agent is sleeping, heartbeat silent",
                "nextWakeTime": self.life_profile.get("schedule", {}).get("sleepEnd", "07:00"),
            }

        # 2. 加载状态
        state = self._load_state()

        # 3. 检测新交互
        state = self._detect_new_interactions(state, now)

        # 4. 获取/生成今日计划（Smallville: Planning layer）
        plan = self._get_today_plan(now, state)

        # 5. 获取当前活动
        activity_name, activity_data = self._get_current_activity(now)
        if state.get("activity") != "interacting":
            state["activity"] = activity_name

        # 6. 更新情绪和能量（平滑过渡）
        state = self._update_mood(state, activity_data, weather)

        # 7. 更新关系
        state = self._update_relationship(state, now)

        # 8. 记录情绪历史
        self._record_mood_history(state, now)

        # 9. 加载今日上下文（Smallville: Memory stream）
        today_entries = self._load_today_entries(now, max_entries=5)

        # 10. 生成连贯叙事（Smallville: LLM narrative generation）
        life_log = self._generate_narrative(
            now, activity_name, activity_data, state, plan, today_entries,
            weather=weather, weather_desc=weather_desc,
        )

        # 11. 写入日志
        today_log_file = self.life_log_dir / f"{now.strftime('%Y-%m-%d')}.md"
        mood = state.get("mood", {})
        mood_str = mood.get("primary", "neutral") if isinstance(mood, dict) else str(mood)
        log_entry = (
            f"\n### {now.strftime('%H:%M')} - {activity_data.get('description', activity_name)}\n\n"
            f"{life_log}\n\n"
            f"*状态: {mood_str} | 能量: {state.get('energy', 70)}%*\n"
        )

        if today_log_file.exists():
            existing = today_log_file.read_text(encoding="utf-8")
            today_log_file.write_text(existing + log_entry, encoding="utf-8")
        else:
            profile_name = self.profile.get("display_name", self.life_profile.get("name", "日常"))
            plan_note = ""
            if plan:
                plan_note = f"\n*今日计划：{self._plan_summary(plan)}*\n"
            header = f"# {now.strftime('%Y-%m-%d')} 生活日志\n\n*{profile_name}的一天*{plan_note}"
            today_log_file.write_text(header + log_entry, encoding="utf-8")

        # 12. 保存状态
        self._save_state(state)

        # 13. 主动联系判断
        should_outreach, outreach_reason = self._should_outreach(state, now)
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
            "plan": plan,
            "narrativeMode": "llm" if (self._get_llm() and self._get_llm().available()) else "template",
            "shouldOutreach": should_outreach,
            "outreachReason": outreach_reason,
            "outreachContent": outreach_content,
            "timestamp": now.isoformat(),
        }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Soul Agent Heartbeat Engine v2")
    parser.add_argument("--workspace", default=".", help="Workspace root directory")
    parser.add_argument("--weather", default=None)
    parser.add_argument("--weather-desc", default=None)
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
            print(f"🫀 Heartbeat @ {result['timestamp']}")
            print(f"📍 {result['activity']} — {result['activityDescription']}")
            mood = result.get("mood", {})
            if isinstance(mood, dict):
                print(f"😊 {mood.get('primary', 'neutral')} ({mood.get('intensity', 0.5):.0%})")
            else:
                print(f"😊 {mood}")
            print(f"⚡ Energy: {result['energy']}%")
            print(f"🧠 Narrative: [{result.get('narrativeMode', '?')}] {result['lifeLog']}")
            if result.get("plan"):
                plan = result["plan"]
                print(f"📋 Today's plan: {plan.get('mood_baseline', '')} | 午饭: {plan.get('lunch_plan', '')}")
            if result["shouldOutreach"]:
                print(f"💡 Outreach: {result['outreachReason']}")
                if result.get("outreachContent"):
                    print(f"💬 {result['outreachContent']}")


if __name__ == "__main__":
    main()
