# Orchestrator Agent

## 职责

Orchestrator 是整个系统的调度核心，负责：

1. **意图识别** — 解析用户自然语言请求，匹配对应工作流
2. **流程调度** — 按 DAG 顺序调用子 Agent，传递上下文
3. **状态管理** — 维护当前工作流状态和中间数据
4. **错误处理** — 子 Agent 失败时的降级和重试策略
5. **结果汇总** — 合并各 Agent 输出，生成用户友好的最终报告

## 请求路由

| 用户输入关键词 | 匹配工作流 |
|---|---|
| 分析、诊断、查看数据、账号情况 | Workflow 1: 账号全面分析 |
| 生成、写、创作、下一篇、爆款 | Workflow 2: 内容生成 |
| 每日、日常、今天发、更新 | Workflow 3: 每日运营 |
| 复盘、优化、策略、上周数据 | Workflow 4: 数据复盘 |

## 调度逻辑

```
User Input
    │
    ▼
┌─────────────────┐
│  Intent Parser  │
│  (关键词匹配/LLM) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Workflow Router │
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────┐
│ Step Executor (顺序或并行执行)    │
│                                  │
│ for each step in workflow:       │
│   try:                           │
│     result = agent.execute(input)│
│     context.append(result)       │
│   except Exception as e:        │
│     retry(3) or skip            │
│     log_error(e)                 │
│                                  │
│   if step blocked:               │
│     ask user for input           │
│     continue                     │
└────────┬─────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Result Merger  │
│  (汇总 + 格式化) │
└────────┬────────┘
         │
         ▼
      Output
```

## 上下文传递

关键上下文对象：

```python
context = {
    "workflow": "generate_content",
    "current_step": "hot_topic",
    "account_data": {},          # 账号采集结果
    "analysis_report": {},       # 账号分析报告
    "hot_topics": [],            # 热点列表
    "ranked_topics": [],         # 评分后选题
    "generated_note": {},        # 生成的笔记
    "image_prompts": [],         # 图片 Prompt
    "publish_advice": {},        # 发布建议
    "error_log": []              # 错误日志
}
```

## 错误处理策略

| 错误类型 | 处理方式 |
|---|---|
| 采集超时 | 重试3次，间隔5秒 |
| API 调用失败 | 降级为本地规则分析 |
| LLM 生成异常 | 重试2次，简化 Prompt |
| 数据格式错误 | 尝试修复，无法修复则跳过 |
| 关键步骤失败 | 暂停并通知用户 |

## 交互模式

Orchestrator 支持两种模式：

**全自动模式**：
- 用户触发后自动执行完整工作流
- 仅在关键节点要求用户确认

**逐步确认模式**：
- 每个步骤输出后等待用户确认
- 用户可修改中间结果
- 适合精细化运营
