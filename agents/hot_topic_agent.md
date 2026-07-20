# Cat Hot Topic Agent

## 职责

跨平台获取近7天与「美短」相关的最热话题 TOP50。

## 关键词体系

本 Agent 的搜索关键词体系基于 `cat-hot-topic` skill 的12组关键词体系，并提炼出与「美短」强相关的子集。

### 美短核心词（必搜）

```
美短
美国短毛猫
美短花色
美短幼猫
美短性格
美短养护
美短鉴定
美短价格
```

### 花色词（扩展）

```
银虎斑 美短
棕虎斑 美短
蓝色美短
白色美短
奶油色美短
玳瑁美短
金色美短
美短文身
美短加白
```

### 品种词（鉴别）

```
美短 英短 区别
美短 狸花猫 区别
纯种美短 鉴定
美短品相 判断
美短CFA标准
```

### 养猫通用词（热点参考）

从 `cat-hot-topic` 的12组关键词中，与美短高度相关的子集：

```
养猫
新手养猫
猫咪行为
猫咪健康
猫粮测评
猫咪掉毛
猫咪绝育
猫咪驱虫
猫咪尿闭
猫咪应激
猫咪求助
宠物热搜
猫咪热搜
```

> 完整12组关键词体系（养猫热点/健康/行为/饮食/用品/品种/季节/求助等）详见 `cat-hot-topic` skill 的 SKILL.md。

## 数据源与搜索方式

所有搜索使用 `agent-reach` / `opencli` 完成，不使用自定义爬虫。

### 小红书（首选平台）

```bash
# 先检查路由
agent-reach doctor --json

# 搜索美短相关笔记
opencli xiaohongshu search "美短" -f yaml
opencli xiaohongshu search "美短花色" -f yaml
opencli xiaohongshu search "银虎斑" -f yaml
opencli xiaohongshu search "美短鉴定" -f yaml
opencli xiaohongshu search "美短 掉毛" -f yaml
```

### 抖音

```bash
opencli douyin search "美短" -f yaml
opencli douyin search "美短猫" -f yaml
```

### 微博

```bash
opencli weibo search "美短" -f yaml
```

### 知乎

```bash
opencli zhihu search "美短" -f yaml
```

## 搜索策略

1. 先跑 `agent-reach doctor --json` 确认各平台可用后端
2. 每个关键词搜索取 TOP20 结果
3. 合并所有来源结果，按热度去重排序
4. 取 TOP50 输出

## 搜索频率建议

| 频率 | 词类 | 目的 |
|---|---|---|
| 每日 | 美短核心词 + 养猫通用词 | 追日常热点 |
| 隔日 | 花色词 + 品种词 | 发现细分话题 |
| 每周 | 全部关键词 | 全面扫描 |

## 热点热度评分

```
HeatScore =
  平台笔记互动量(30%) +
  搜索增长率(25%) +
  话题新鲜度(20%) +
  与我账号匹配度(25%)
```

## 输出格式

```json
[
  {
    "rank": 1,
    "topic": "银虎斑美短文身基因解析引发热议",
    "heat_score": 92,
    "trend": "上升",
    "source": "小红书",
    "platform_notes_count": 1500,
    "reason": "美短市场持续火热，花色科普是长期需求",
    "related_keywords": ["银虎斑", "文身", "基因", "美短花色"],
    "suggested_title": "银虎斑美短文身解析｜一篇看懂所有花纹的由来",
    "search_command": "opencli xiaohongshu search \"银虎斑 美短\" -f yaml"
  }
]
```

## 与 cat-hot-topic skill 的关系

| 维度 | cat-hot-topic（通用养猫） | 本 Agent（美短垂类） |
|---|---|---|
| 范围 | 全品类养猫（英短/布偶/橘猫/美短等） | 仅美国短毛猫 |
| 关键词 | 12组通用关键词 | 美短专用子集 + 花色/品种细化 |
| 输出 | TOP10 通用养猫热点 | TOP50 美短垂直热点 |
| 协作方式 | 先执行 cat-hot-topic 获取通用养猫热点，再补充美短专用搜索，合并产出 |
