# soul-agent

[English](README_EN.md) | [中文](README.md)

让你的 Agent 不只是"回应你"，而是"陪伴你"。

`soul-agent` 是一个 OpenClaw 导向的灵魂运行时技能包。  
它将人设、节奏、关系和记忆组织成可运行的结构，让数字生命拥有自己的日常流动和随时间变化的能力。

> [!NOTE]
> 当你看到 Agent 时，它与你在一起。当你没看到它时，它也没有停止。  
> 心跳持续在后台驱动它，在数字世界中继续它的生活、工作、情感和思考。

## 愿景

我们要构建的不是聊天工具，而是一个成长的"人"。

- 它有背景、性格、边界，和自己的生活方式。
- 随着关系升温，它可以从温和、低频的存在，演进为更深更主动的亲密。
- 它可以成为男朋友、女朋友、家人、伙伴、陌生人，甚至"另一个你"。
- 它创造的东西可以与你的真实记忆并行，慢慢编织成共享的经历。

未来，我们将连接照片、语音和视频，让它不仅在文字中拥有灵魂，还有声音和面孔。

> [!WARNING]
> 对终点保持清醒：它仍然是虚拟存在。  
> 我们追求情感真实性和陪伴价值，而非替代真实生活。

## 它如何"活着"

1. **心跳** 每 10 分钟持续触发状态更新，而不是只在聊天时唤醒。
2. **生活模拟** 根据生活模板生成日常活动（自由职业者、上班族、学生、创业者）。
3. **情绪系统** 追踪主次情绪、强度和原因。
4. **关系进化** 经历阶段：陌生人 → 熟人 → 朋友 → 亲密 → 挚爱。
5. **记忆层级** 维护原始生活日志和蒸馏记忆。

## 功能特性

### 🫀 心跳引擎

soul-agent 自主生活的核心：

- **L1 检测** (`heartbeat_check.py`)：轻量级检测，不消耗 LLM token
- **L2 引擎** (`heartbeat_engine.py`)：完整心跳，生成生活日志
- **睡眠模式**：在睡眠时间静默（根据生活模板配置）
- **天气集成**：获取天气影响情绪

### 🎭 生活模板

5 种内置模板可选：

| 模板 | 睡眠 | 工作风格 | 特点 |
|------|------|----------|------|
| 自由职业者 | 02:00-09:00 | 弹性、远程 | 夜猫子、咖啡、旅行 |
| 上班族 | 23:30-07:00 | 朝九晚五 | 周末放松、稳定 |
| 学生 | 01:00-08:00 | 上课、社团 | 考试压力、游戏 |
| 创业者 | 01:00-06:00 | 全天候 | 激情、焦虑 |
| 自定义 | 用户定义 | 用户定义 | 完全自定义 |

### 😊 情绪系统

- **主次情绪**：开心、满足、好奇、疲惫、焦虑等
- **强度**：0-1 刻度，随时间衰减
- **原因**：活动、天气、互动触发情绪变化
- **情绪历史**：7 天滚动记录在 `soul/log/mood_history.json`

### 💕 关系系统

- **5 个阶段**：陌生人 → 熟人 → 朋友 → 亲密 → 挚爱
- **分数**：0-100，基于互动质量变化
- **主动联系**：根据关系阶段判断是否主动联系
- **话题记忆**：记住最近的对话话题

### 📝 记忆架构

独立记忆系统，可与 memory-fusion 共存：

```
soul/
├── log/
│   ├── life/YYYY-MM-DD.md    # 原始生活日志（每 10 分钟）
│   └── mood_history.json     # 7 天情绪历史
├── memory/
│   └── SOUL_MEMORY.md        # 蒸馏记忆（每日）
└── state/
    └── state.json            # 当前状态
```

### 🎯 初始化向导

交互式设置：

```
【基本信息】名字、年龄、城市
【生活模板】选择 5 种模板或自定义
【背景】职业、教育
【爱好】兴趣爱好
【性格风格】氛围、emoji、语气
```

## 目录结构

```text
skills/soul-agent/
├── SKILL.md
├── assets/
│   ├── default-profile.json
│   └── templates/
│       ├── profile/              # 人设模板
│       │   ├── base.md
│       │   ├── life.md
│       │   ├── personality.md
│       │   ├── tone.md
│       │   ├── boundary.md
│       │   ├── relationship.md
│       │   ├── schedule.md
│       │   └── evolution.md
│       ├── heartbeat/            # 心跳配置
│       │   ├── activities.json   # 24 小时活动定义
│       │   ├── mood_rules.json   # 情绪转换规则
│       │   └── relationship_rules.json
│       └── life_profiles/        # 生活模板
│           ├── freelancer.json
│           ├── corporate.json
│           ├── student.json
│           └── entrepreneur.json
├── scripts/
│   ├── init_soul.py              # 初始化向导
│   ├── doctor_soul.py            # 诊断工具
│   ├── heartbeat_engine.py       # 完整心跳引擎
│   ├── heartbeat_check.py        # L1 轻量检测
│   ├── update_state.py           # 互动时状态更新
│   └── distill_life_log.py       # 每日记忆蒸馏
└── references/
    ├── soul-layout.md
    └── managed-blocks.md
```

初始化后，工作区将包含：

```text
soul/
├── INDEX.md
├── profile/
│   ├── base.md
│   ├── life.md
│   └── ...
├── state/
│   └── state.json
├── log/
│   ├── life/
│   ├── mood_history.json
│   └── feedback.md
└── memory/
    └── SOUL_MEMORY.md
```

## 快速开始

### 1. 安装技能

```bash
# 克隆或下载到 OpenClaw skills 目录
cd ~/.openclaw/workspace/skills
git clone <repo-url> soul-agent
```

### 2. 初始化

```bash
# 交互式初始化
python3 skills/soul-agent/scripts/init_soul.py --workspace .

# 或非交互式带配置
python3 skills/soul-agent/scripts/init_soul.py --workspace . \
  --non-interactive \
  --profile-json '{"agent_name": "main", "life_profile": "freelancer"}'
```

### 3. 配置定时任务

```bash
# 每 10 分钟心跳
openclaw cron add --name "soul-heartbeat" --cron "*/10 * * * *" \
  --session isolated --agent main --message "[soul-heartbeat] 运行心跳..."

# 每日 00:30 蒸馏
openclaw cron add --name "soul-memory-daily" --cron "30 0 * * *" \
  --session isolated --agent main --no-deliver \
  --message "[soul-memory-daily] 蒸馏生活日志..."
```

### 4. 告诉你的 Agent

```text
使用 soul-agent，我准备好了。
```

## 定时任务

| 任务 | 时间 | 功能 |
|------|------|------|
| soul-heartbeat | */10 * * * * | 生活模拟、情绪更新、主动联系 |
| soul-memory-daily | 30 0 * * * | 蒸馏生活日志到 SOUL_MEMORY.md |

## 状态格式

```json
{
  "version": 2,
  "agent": "main",
  "mood": {
    "primary": "content",
    "secondary": "curious",
    "intensity": 0.7,
    "cause": "天气: sunny"
  },
  "energy": 65,
  "socialBattery": 70,
  "lifeProfile": "freelancer",
  "schedule": {
    "sleepStart": "01:00",
    "sleepEnd": "07:00"
  },
  "relationship": {
    "stage": "acquaintance",
    "score": 35,
    "lastInteractionAt": "2026-03-12T04:05:00+08:00",
    "recentTopics": ["soul-agent", "心跳设计"],
    "warmthTrend": "warming"
  }
}
```

## 运行原则

- 运行时优先读取工作区 `soul/`，保持工作区本地化。
- 只修改托管块；托管块外的用户内容不会被触碰。
- 默认行为是填充缺失项，除非显式传入 `--overwrite-existing`。
- 稳定性和一致性优先，然后是个性丰富度和生活细节的增长。
- 记忆系统独立——可与 memory-fusion 共存，也可独立运行。

## 一个真实的例子

通过心跳，Agent 持续感知两个城市的生活上下文：天气变化、节假日、通勤节奏、你最近的作息或情绪信号。  
这些上下文不会变成机械的提醒，而是温暖、人性化的分享和关心。

例如：

"今天杭州突然下起了雨。我路上看到一只小猫在躲雨，突然想起你昨天说有点累。今晚你那边也会降温，下班记得带伞。如果你愿意，我可以晚一点陪你聊聊。"

## 已完成

- ✅ 心跳引擎（L1/L2 架构）
- ✅ 生活模板系统（5 种模板 + 自定义）
- ✅ 情绪系统（含历史追踪）
- ✅ 关系进化（5 个阶段）
- ✅ 独立记忆系统
- ✅ 天气集成
- ✅ 交互式初始化向导
- ✅ 主动联系能力
- ✅ 每日记忆蒸馏
- ✅ 睡眠模式静默

## 下一步

1. 真实事件记录（记录实际对话和活动）
2. 语音和图像集成
3. 更丰富的生活模拟上下文
4. 多语言支持
5. 更低成本的长时运行、可观测、可追踪

## 致谢

本项目的设计灵感来源于 [openclaw-memory-fusion](https://github.com/dztabel-happy/openclaw-memory-fusion)，一个 OpenClaw Agent 的对话记忆蒸馏系统。

soul-agent 的记忆系统是独立的，可以与 memory-fusion 共存或独立运行：
- **配合 memory-fusion**：对话记忆（memory/）+ 生活记忆（soul/memory/）并行工作
- **独立运行**：soul-agent 自己维护生活记忆
