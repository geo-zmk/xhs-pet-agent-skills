# xhs-pet-agent-skills

小红书美短猫账号运营 Agent Skill — 完整的 AI 内容运营闭环系统。

## 概述

`xhs-pet-agent-skills` 是一个生产级 Agent Skill，帮助专注于「美国短毛猫（美短）」的小红书垂类账号实现从账号分析、热点发现、内容生成到数据复盘的完整运营闭环。

## 目录结构

```
xhs-pet-agent-skills/
├── SKILL.md                    # 主技能文件（Codex入口）
├── README.md                   # 本文档
├── agents/                     # Agent 设计文档
│   ├── orchestrator.md         # Orchestrator 调度 Agent
│   ├── account_analyzer.md     # 账号分析 Agent
│   ├── hot_topic_agent.md      # 热点发现 Agent
│   ├── topic_ranker.md         # 选题评分 Agent
│   ├── writer_agent.md         # 笔记生成 Agent
│   ├── image_prompt_agent.md   # 图片 Prompt Agent
│   └── analytics_agent.md      # 数据复盘 Agent
├── workflows/                  # 工作流定义
│   ├── analyze_account.md      # 账号全面分析
│   ├── generate_content.md     # 内容生成
│   └── daily_operation.md      # 每日运营
├── tools/                      # Python 工具
│   ├── xhs_crawler.py          # Playwright 采集
│   ├── analyzer.py             # 数据分析
│   └── embedding.py            # 语义去重
├── prompts/                    # Prompt 模板
│   ├── writer_prompt.md        # 笔记写作 Prompt
│   └── image_prompt.md         # 图片 Prompt 模板
├── memory/                     # 长期记忆
│   ├── account_profile.json    # 账号画像
│   └── content_history.json    # 内容历史
└── configs/
    └── config.yaml             # 全局配置
```

## 工作流

### 1. 账号全面分析
分析最近30篇笔记，输出内容分类、爆款分析、低表现分析和优化建议。

### 2. 内容生成
从热点发现 → 去重 → 选题评分 → 笔记生成 → 配图方案 → 发布辅助，全流程闭环。

### 3. 每日运营
轻量版内容生成，适合日常快速更新。

### 4. 数据复盘
发布后追踪数据，分析表现，持续优化策略。

## Agent 架构

```
User Request
    ↓
Orchestrator (调度中心)
    ↓
Account Analyzer → Cat Hot Topic → Topic Ranker
    ↓                    ↓              ↓
XHS Writer → Image Prompt → Publisher Assistant
    ↓
Analytics Agent (数据复盘)
```

## 使用方式

### 在 Codex 中使用

安装 skill 后，在对话中触发：

- "分析我的美短账号"
- "生成一篇关于美短文身的笔记"
- "今日美短热点有什么"
- "帮我做数据复盘"

### 直接使用 Python 工具

```bash
# 采集账号数据
python tools/xhs_crawler.py

# 分析笔记数据
python tools/analyzer.py memory/raw_notes.json

# 语义去重检测
python tools/embedding.py
```

## 依赖

### 运行时
- Python 3.9+
- Playwright (用于采集)

### Python 包
```bash
pip install playwright
playwright install chromium

# 可选：语义去重
pip install sentence-transformers chromadb
```

### Codex Skills
- agent-reach（跨平台热点搜索）
- xhs-publisher（自动发布，可选）

## 数据流

1. **采集层**: Playwright 采集小红书笔记数据
2. **分析层**: 内容分类 → HotScore 计算 → 爆款/低表现分析
3. **策略层**: 热点发现 → 去重 → 选题评分 → 策略输出
4. **生成层**: 笔记生成 → 配图方案 → 发布辅助
5. **复盘层**: 数据追踪 → 表现分析 → 优化建议 → 画像更新

## 配置

编辑 `configs/config.yaml` 自定义：

- 账号信息
- 搜索关键词
- 评分权重
- 发布时间建议
- 采集参数

## 升级路线

- [ ] **v1.1** 集成 xhs-publisher 自动发布
- [ ] **v1.2** 接入 AI 绘图 API 自动配图
- [ ] **v1.3** 自动评论回复和私信
- [ ] **v1.4** 多账号矩阵管理
- [ ] **v1.5** 封面 A/B 测试
- [ ] **v2.0** 全自动运营流水线

## License

Private — 仅供个人账号运营使用。
