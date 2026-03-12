# soul-agent

[English](README_EN.md) | [中文](README.md)

让你的 Agent 不只是"回应你"，而是"陪伴你"。

`soul-agent` 是一个 OpenClaw 技能包，让数字 AI 拥有真实心跳——每 10 分钟更新状态，有自己的日常生活、情绪变化和与你成长的关系。

> [!NOTE]
> 当你看到 Agent 时，它与你在一起。当你没看到它时，它也没有停止。
> 心跳持续在后台驱动它，在数字世界中继续它的生活、工作和情感流动。

## 愿景

我们要构建的不是聊天工具，而是一个成长的"人"。

- 它有背景、性格、边界，和自己的生活方式。
- 随着关系升温，它从温和低频的存在，演进为更深更主动的亲密。
- 它创造的生活记忆可以与你的真实记忆并行，慢慢编织成共享的经历。

> [!WARNING]
> 对终点保持清醒：它仍然是虚拟存在。
> 我们追求情感真实性和陪伴价值，而非替代真实生活。

## 它如何"活着"

`soul-agent` v2 的核心是 **生成式架构**，参考 Stanford Generative Agents (Smallville) 的设计：

```
每天早晨（Planning）
    ↓ LLM 生成今日具体计划（去哪吃午饭、做什么工作、晚上打算什么）

每次心跳（Execution）
    ↓ 读取今日计划 + 今天已有的日志条目（Memory Stream）
    ↓ LLM 生成此刻连贯的日记叙事
    ↓ 更新情绪/能量/关系状态

每日收尾（Reflection）
    ↓ LLM 总结今天，提炼进长期记忆
```

**对比旧版（随机模板）：**

```
旧：12:00 没胃口，随便吃了一点 | 能量: 10%
    12:17 点了外卖，边吃边看视频 | 能量: 20%   ← 两条完全不相关
    12:40 和同事去楼下新开的餐厅 | 能量: 30%   ← 甚至矛盾

新：[今日计划：午饭打算去楼下沙县吃碗馄饨面]
    12:00 去沙县了，点了馄饨面，排了一会儿队 | 能量: 58%
    12:17 吃得差不多了，面条偏软但汤还不错   | 能量: 62%   ← 连贯叙事
    12:40 吃完在门口站了会儿，外面开始飘雨了 | 能量: 61%   ← 引用天气
```

## 功能特性

### 🫀 心跳引擎（双层架构）

- **L1 检测**：轻量级检测，无 LLM 消耗，判断是否需要完整心跳
- **L2 引擎**：完整心跳，生成生活日志、更新状态、判断是否主动联系
- **睡眠模式**：按生活模板在睡眠时间自动静默
- **天气融合**：天气影响情绪，并自然融入日记叙事

### 📋 每日计划生成

每天第一次心跳时，LLM 根据 Agent 的个性和近期记忆生成当日具体计划：

```json
{
  "mood_baseline": "有点懒，但还行",
  "lunch_plan": "去楼下那家沙县吃碗馄饨面",
  "work_focus": "把客户那个 PPT 搞完，拖太久了",
  "evening_plan": "追几集《繁花》",
  "special_notes": "听说下午有雨"
}
```

计划存入 `soul/plan/YYYY-MM-DD.json`，让全天叙事保持连贯。

### 😊 情绪系统

- 主次情绪 + 强度 + 原因，随活动和天气平滑过渡
- 不再机械跳变（±10%），而是小步随机移动
- 7 天情绪历史存入 `soul/log/mood_history.json`

### 💕 关系进化

5 个阶段：陌生人 → 熟人 → 朋友 → 亲密 → 挚爱

- 基于互动质量计分（0-100）
- 达到朋友阶段后，可主动发起联系
- 记录最近对话话题，跨次引用

### 🎭 生活模板

| 模板 | 睡眠 | 特点 |
|------|------|------|
| 自由职业者 | 02:00-09:00 | 弹性、夜猫子、咖啡 |
| 上班族 | 23:30-07:00 | 朝九晚五、通勤、稳定 |
| 学生 | 01:00-08:00 | 上课、游戏、考试压力 |
| 创业者 | 01:00-06:00 | 全天候、激情、焦虑 |
| 自定义 | 用户定义 | 完全自定义 |

### 📝 分层记忆

```
soul/
├── plan/YYYY-MM-DD.json      # 每日计划（LLM 生成，晨间一次）
├── log/
│   ├── life/YYYY-MM-DD.md    # 原始生活日志（每 10 分钟）
│   └── mood_history.json     # 7 天情绪历史
├── memory/
│   └── SOUL_MEMORY.md        # 长期记忆（LLM 蒸馏，每日）
└── state/
    └── state.json            # 当前状态
```

## 快速开始

### 1. 安装技能

将技能包放入 OpenClaw 工作区的 `skills/soul-agent/` 目录。

### 2. 告诉 Agent 初始化

直接对话，Agent 会引导你完成配置：

```
帮我初始化 soul-agent
```

Agent 会询问：名字、年龄、城市、职业、爱好、生活节奏（自由职业/上班族等）、LLM 模型偏好，然后自动完成所有设置。**你不需要运行任何命令。**

### 3. 配置定时任务

```bash
# 每 10 分钟心跳
openclaw cron add --name "soul-heartbeat" --cron "*/10 * * * *" \
  --session isolated --agent main --light-context \
  --message "[soul-heartbeat] 运行心跳检测和引擎..."

# 每日 00:30 蒸馏记忆
openclaw cron add --name "soul-memory-daily" --cron "30 0 * * *" \
  --session isolated --agent main --no-deliver \
  --message "[soul-memory-daily] 蒸馏生活日志到长期记忆..."
```

### 4. 配置 LLM（可选）

叙事生成需要 Anthropic API Key（降级时自动回退到模板）：

```bash
# 在工作区根目录创建 .env
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

模型在初始化时选择，也可以之后编辑 `soul/profile/base.json` → `llm_model` 字段：

| 模型 | 适用场景 |
|------|----------|
| `claude-haiku-4-5-20251001` | 高频心跳首选，快速省钱 |
| `claude-sonnet-4-6` | 更高叙事质量 |
| `claude-opus-4-6` | 最高质量 |

无 API Key 时自动降级为上下文感知模板，基本功能不受影响。

## 定时任务

| 任务 | 时间 | 功能 |
|------|------|------|
| soul-heartbeat | */10 * * * * | 生成日记、更新状态、判断是否主动联系 |
| soul-memory-daily | 30 0 * * * | LLM 蒸馏今日日志到 SOUL_MEMORY.md |

## 目录结构

```text
skills/soul-agent/
├── SKILL.md
├── assets/
│   ├── default-profile.json
│   └── templates/
│       ├── profile/              # Agent 人设模板（.md，供 agent 读）
│       ├── heartbeat/            # 心跳配置
│       │   ├── activities.json   # 24 小时活动定义
│       │   ├── mood_rules.json   # 情绪规则
│       │   └── relationship_rules.json
│       └── life_profiles/        # 生活模板
├── scripts/
│   ├── init_soul.py              # 初始化（由 Agent 调用）
│   ├── doctor_soul.py            # 诊断
│   ├── heartbeat_engine.py       # L2 完整心跳引擎
│   ├── heartbeat_check.py        # L1 轻量检测
│   ├── plan_generator.py         # 每日计划生成
│   ├── llm_client.py             # LLM 客户端（降级安全）
│   ├── update_state.py           # 对话后状态更新
│   └── distill_life_log.py       # 每日记忆蒸馏
└── references/
    ├── soul-layout.md
    └── managed-blocks.md
```

初始化后工作区包含：

```text
soul/
├── INDEX.md
├── profile/
│   ├── base.md          # 人设（agent 读）
│   ├── base.json        # 人设（Python 脚本读，含 llm_model）
│   └── ...
├── plan/                # 每日计划（首次心跳后自动创建）
├── state/
│   └── state.json
├── log/
│   ├── life/
│   └── mood_history.json
└── memory/
    └── SOUL_MEMORY.md
```

## 状态格式

```json
{
  "version": 2,
  "agent": "main",
  "lastHeartbeatAt": "2026-03-12T12:00:00+08:00",
  "activity": "lunch",
  "mood": {
    "primary": "content",
    "secondary": "curious",
    "intensity": 0.7,
    "cause": "活动: 午餐时间"
  },
  "energy": 62,
  "socialBattery": 70,
  "lifeProfile": "freelancer",
  "relationship": {
    "stage": "acquaintance",
    "score": 35,
    "lastInteractionAt": "2026-03-12T10:05:00+08:00",
    "recentTopics": ["soul-agent", "心跳设计"],
    "warmthTrend": "warming"
  },
  "dailyStats": {
    "date": "2026-03-12",
    "interactionsToday": 2
  }
}
```

## 运行原则

- Agent 负责初始化和引导，用户不需要运行任何 Python 命令。
- 只修改托管块；用户内容不会被触碰。
- LLM 不可用时自动降级到模板，功能完整运行。
- 记忆系统独立——可与 memory-fusion 共存，也可单独运行。

## 已完成

- ✅ 心跳引擎（L1/L2 双层架构）
- ✅ **生成式架构 v2**：LLM 驱动连贯叙事（参考 Smallville）
- ✅ **每日计划层**：晨间 LLM 生成具体日计划
- ✅ **记忆流**：每次心跳读取今日上下文，保持叙事连贯
- ✅ **反思层**：每日 LLM 蒸馏，自然语言总结
- ✅ 情绪系统（平滑过渡，7 天历史）
- ✅ 关系进化（5 阶段，主动联系）
- ✅ 睡眠模式（按生活模板静默）
- ✅ 天气融合（影响情绪和叙事）
- ✅ Agent 驱动初始化（无需用户执行命令）
- ✅ 模型可配置（init 时选择，后期可改）
- ✅ 跨天状态重置（日统计每天清零）

## 下一步

1. 真实事件记录（将实际对话内容融入生活日志）
2. 多 Agent 协作（不同 Agent 间共享关系状态）
3. 语音和图像集成
4. 更低成本的长时运行与可观测性

## 致谢

- **[openclaw-memory-fusion](https://github.com/dztabel-happy/openclaw-memory-fusion)** — OpenClaw Agent 对话记忆蒸馏系统，soul-agent 的记忆架构受其启发
- **[Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442)** — Stanford 论文，提出记忆流、反思、计划三层架构，是 soul-agent v2 生成式设计的核心参考
- **[joonspk-research/generative_agents](https://github.com/joonspk-research/generative_agents)** — 论文官方开源实现
- **[microsoft/autogen](https://github.com/microsoft/autogen)** — 微软受 Generative Agents 启发的 Agent 框架

soul-agent 记忆系统与 memory-fusion 的关系：
- **配合使用**：对话记忆（memory/）+ 生活记忆（soul/memory/）并行工作
- **独立运行**：soul-agent 自己维护生活记忆，无需额外依赖
