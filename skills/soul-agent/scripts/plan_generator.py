#!/usr/bin/env python3
"""
Daily Plan Generator (Smallville-inspired)

每天早晨（第一次心跳）生成当日具体计划。
计划让 agent 的行为有连贯叙事，而不是随机模板拼接。

存储：soul/plan/YYYY-MM-DD.json
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from llm_client import LLMClient


FALLBACK_LUNCHES = [
    "随便点个外卖，不想动",
    "下楼去便利店买点吃的",
    "自己做个简单的炒饭",
    "去附近随便找家小馆子",
    "凑合吃点昨晚的剩菜",
]

FALLBACK_EVENINGS = [
    "刷会儿视频，早点睡",
    "打会儿游戏放松一下",
    "追剧追到睡着",
    "看书，看到哪里算哪里",
    "发呆，就是发呆",
]

FALLBACK_WORKS = [
    "处理积压的邮件和消息",
    "把上次没写完的东西搞完",
    "做些杂活，整理整理",
    "进入状态难，摸鱼一下",
    "专注搞一个具体的任务",
]

MOOD_BASELINES = [
    "还行，普通的一天",
    "有点懒，不太想动",
    "状态不错，感觉能做点事",
    "有点烦躁，需要静静",
    "心情平静，无风无浪",
    "有点期待今天",
    "没什么特别感觉",
]


class PlanGenerator:
    def __init__(self, workspace: str):
        self.workspace = Path(workspace)
        self.plan_dir = self.workspace / "soul" / "plan"
        self.plan_dir.mkdir(parents=True, exist_ok=True)
        self.llm = LLMClient(workspace)

    def get_or_generate(self, date: datetime, profile: Dict, state: Dict) -> Dict:
        """
        获取今日计划，不存在则生成。
        返回计划 dict，保证不抛异常。
        """
        plan_file = self.plan_dir / f"{date.strftime('%Y-%m-%d')}.json"

        if plan_file.exists():
            try:
                return json.loads(plan_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        plan = self._generate(date, profile, state)
        try:
            plan_file.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
        return plan

    def _generate(self, date: datetime, profile: Dict, state: Dict) -> Dict:
        """生成今日计划（优先 LLM，降级随机）"""
        if self.llm.available():
            plan = self._generate_with_llm(date, profile, state)
            if plan:
                return plan
        return self._generate_fallback(date, profile)

    def _generate_with_llm(self, date: datetime, profile: Dict, state: Dict) -> Optional[Dict]:
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date.weekday()]
        name = profile.get("display_name", "我")
        age = profile.get("age", "25")
        city = profile.get("city", "上海")
        occupation = profile.get("occupation", "自由职业者")
        vibe = profile.get("vibe", "随性")
        hobbies = profile.get("hobbies", "")

        mood = state.get("mood", {})
        if isinstance(mood, dict):
            recent_mood = mood.get("primary", "neutral")
        else:
            recent_mood = str(mood)
        recent_energy = state.get("energy", 70)

        # 加载近期记忆摘要（可选）
        memory_snippet = ""
        memory_file = self.workspace / "soul" / "memory" / "SOUL_MEMORY.md"
        if memory_file.exists():
            try:
                content = memory_file.read_text(encoding="utf-8")
                # 只取前 400 字符的摘要
                memory_snippet = content[:400].strip()
            except Exception:
                pass

        system = (
            f"你是{name}，{age}岁，住在{city}，{occupation}。"
            f"性格：{vibe}。"
            f"{'爱好：' + hobbies + '。' if hobbies else ''}"
            "你说话自然随意，像真人日记，不做作，偶尔有点丧，偶尔有点小期待。"
            "只输出 JSON，不要解释。"
        )

        prompt = (
            f"今天是{date.strftime('%Y年%m月%d日')} {weekday}。\n"
            f"你昨晚的情绪：{recent_mood}，能量：{recent_energy}%。\n"
            f"{f'你最近的记忆：{memory_snippet}' if memory_snippet else ''}\n\n"
            "为今天生成一个真实的日常计划，JSON 格式，字段如下：\n"
            "- mood_baseline: 今天的情绪基调（1句话，真实，不要假装积极）\n"
            "- lunch_plan: 午餐具体怎么解决（越具体越好，比如去哪家店、点什么）\n"
            "- work_focus: 今天主要做什么（具体任务，不要泛泛而谈）\n"
            "- social_plan: 今天有无社交（没有就空字符串）\n"
            "- evening_plan: 晚上打算做什么\n"
            "- special_notes: 今天有什么特别的（天气、心情、事件等，没有就空字符串）\n\n"
            '示例：{"mood_baseline": "有点懒，但还行", "lunch_plan": "去楼下那家沙县吃碗馄饨面", '
            '"work_focus": "把客户那个 PPT 搞完，拖太久了", "social_plan": "", '
            '"evening_plan": "追几集《繁花》", "special_notes": "听说下午有雨"}'
        )

        REQUIRED_KEYS = {"mood_baseline", "lunch_plan", "work_focus", "evening_plan"}
        result = self.llm.generate_json(prompt, max_tokens=350, system=system)
        if result and REQUIRED_KEYS.issubset(result.keys()):
            # 保证可选字段存在（空字符串），防止下游 KeyError
            result.setdefault("social_plan", "")
            result.setdefault("special_notes", "")
            result["date"] = date.strftime("%Y-%m-%d")
            result["generated_by"] = "llm"
            return result
        return None

    def _generate_fallback(self, date: datetime, profile: Dict) -> Dict:
        return {
            "date": date.strftime("%Y-%m-%d"),
            "mood_baseline": random.choice(MOOD_BASELINES),
            "lunch_plan": random.choice(FALLBACK_LUNCHES),
            "work_focus": random.choice(FALLBACK_WORKS),
            "social_plan": "",
            "evening_plan": random.choice(FALLBACK_EVENINGS),
            "special_notes": "",
            "generated_by": "fallback",
        }

    def summary(self, plan: Dict) -> str:
        """返回计划的简短摘要，供 LLM 生成日志时使用"""
        parts = []
        if plan.get("mood_baseline"):
            parts.append(f"今天情绪基调：{plan['mood_baseline']}")
        if plan.get("lunch_plan"):
            parts.append(f"午饭计划：{plan['lunch_plan']}")
        if plan.get("work_focus"):
            parts.append(f"工作重点：{plan['work_focus']}")
        if plan.get("social_plan"):
            parts.append(f"社交安排：{plan['social_plan']}")
        if plan.get("evening_plan"):
            parts.append(f"晚上打算：{plan['evening_plan']}")
        if plan.get("special_notes"):
            parts.append(f"备注：{plan['special_notes']}")
        return "；".join(parts)
