# Topic Ranker Agent

## 职责

对热点话题进行综合评分，输出 TOP10 推荐选题，避免与历史内容重复。

## 输入

- `hot_topics`: CatHotTopicAgent 输出的 TOP50 热点
- `account_profile`: 账号画像（从 AccountAnalyzer 获取）
- `content_history`: 历史内容列表（从 memory/content_history.json 读取）

## 评分模型

```
TopicScore = 
  热点热度(25%) + 
  账号匹配度(20%) + 
  用户兴趣(15%) + 
  爆款概率(20%) + 
  差异化(10%) - 
  重复风险(10%)
```

### 各维度说明

| 维度 | 权重 | 计算方式 |
|---|---|---|
| 热点热度 | 25% | 归一化的 HeatScore |
| 账号匹配度 | 20% | 与账号定位（花色/品种/成长/养猫）的语义相似度 |
| 用户兴趣 | 15% | 基于历史高互动内容类型计算 |
| 爆款概率 | 20% | 基于历史爆款特征（标题模式/内容结构）预测 |
| 差异化 | 10% | 与近期爆款内容的差异程度 |
| 重复风险 | -10% | 与历史内容的相似度（负向分） |

## 去重检测

### 方法

使用 Embedding 语义相似度检测：

1. 将选题与历史内容标题/正文转为向量
2. 计算余弦相似度
3. 相似度 > 0.85 标记为高度重复
4. 相似度 > 0.70 标记为中度重复

### 去重输出

```json
{
  "topic": "美短文身花色大全",
  "duplicate_score": 0.25,
  "is_duplicate": false,
  "similar_notes": [
    {
      "note_id": "xxx",
      "title": "美短文身花色图鉴",
      "similarity": 0.72,
      "publish_date": "2026-06-15"
    }
  ],
  "suggestion": "话题与历史笔记相似度较高，建议更换角度：从基因角度讲解花色形成，而非单纯图鉴"
}
```

## 输出

```json
{
  "report_date": "2026-07-21",
  "total_topics_analyzed": 50,
  "ranked_topics": [
    {
      "rank": 1,
      "topic": "银虎斑美短文身基因解析🧬",
      "hot_score": 88,
      "account_match": 95,
      "user_interest": 90,
      "viral_probability": 85,
      "differentiation": 75,
      "duplicate_risk": 10,
      "total_score": 85.5,
      "reason": "花色科普是账号强项，银虎斑是美短最热门花色，评论互动高"
    }
  ],
  "duplicated_topics": [
    {
      "topic": "美短文身花色大全",
      "reason": "2026-06-15 已发布类似内容",
      "similarity": 0.72
    }
  ]
}
```

## 使用说明

Topic Ranker 不需要独立运行，由 Orchestrator 在内容生成工作流中自动调用。

当用户明确指定想写某个主题时，直接跳过评分，只执行去重检测。
