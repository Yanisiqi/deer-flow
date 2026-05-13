# goin_new 数据库表清单

> 生成日期: 2026-05-13  
> ClickHouse 版本: 22.6.1.1  
> 数据库: `goin_new`

---

## 总览

| 序号 | 表名 | 引擎 | 行数 | 类别 |
|---|---|---|---|---|
| 1 | `relation_share_data` | ReplacingMergeTree | 3.48 亿 | 关系 |
| 2 | `document_share_data_old` | ReplacingMergeTree | 6393 万 | 文档(旧) |
| 3 | `document_share_data` | ReplacingMergeTree | 6389 万 | 文档 |
| 4 | `document_share_data_lookup` | Join | 6323 万 | 文档辅助 |
| 5 | `event_share_data` | ReplacingMergeTree | 3623 万 | 事件 |
| 6 | `entity_share_data` | ReplacingMergeTree | 1068 万 | 实体 |
| 7 | `event_geo_share_data` | MergeTree | 965 万 | 事件地理位置 |
| 8 | `activity_summary` | MergeTree | 191 | 活动摘要 |
| 9 | `statements_summary` | MergeTree | 190 | 言论摘要 |
| 10 | `entity_summary` | MergeTree | 132 | 实体摘要 |
| 11 | `social_media_summary` | MergeTree | 113 | 社交媒体摘要 |
| 12 | `event_summary` | MergeTree | 91 | 事件摘要 |
| 13 | `news_summary` | MergeTree | 63 | 新闻摘要 |
| 14 | `cognitive_*_summary`（10 张） | MergeTree | 15~42 | 认知分析 |
| 15 | `social_media_discussion_summary` | MergeTree | 21 | 社交媒体讨论 |
| 16 | `mv_sync_document_share_data_lookup` | MaterializedView | - | 物化视图 |
| 17 | `person_event_share_data` | View | - | 人物-事件视图 |
| 18 | `person_statements_share_data` | View | - | 人物-言论视图 |

---

## 各表详细说明

### 1. `entity_share_data` — 实体数据（核心表）

- **行数**: 10,677,339
- **引擎**: ReplacingMergeTree
- **列数**: 346
- **内容**: 实体主表，存储各类实体的属性信息，包括人物、组织、武器、地点等
- **典型字段**: `mongo_id`, `name`, `type`, `sex_or_gender`, `age`, `date_of_birth`, `date_of_death`, `occupation`, `country_of_citizenship`, `residence`, `industry` 等
- **复杂的复合字段**:
  - `population` / `gdp` — 人口/GDP（数组嵌套结构）
  - `position_experience` — 任职经历（时间、机构、职位）
  - `education_experience` — 教育经历
  - `medias` / `notes` — 媒体/笔记
  - `runway` / `altitude` — 机场/武器技术参数
- `type` 列区分实体类型: `human`, `organization`, `weapon`, `administrative`, `facility` 等

### 2. `relation_share_data` — 关系数据

- **行数**: 347,572,165（最大的表）
- **引擎**: ReplacingMergeTree
- **内容**: 实体之间的关系，每行一条关系记录
- **典型字段**: `Head_id`, `Head_name`, `Head_type`, `Tail_id`, `Tail_name`, `Tail_type`, `Tail_title`, `type`（关系类型）
- **用途**: 从"头实体"指向"尾实体"，如"特朗普 → 总统 → 美国"（人 → 职位 → 国家）
- **注意**: 3.4 亿行，直接 JOIN 风险大，建议分两步查询

### 3. `document_share_data` — 文档数据

- **行数**: 63,890,583
- **引擎**: ReplacingMergeTree
- **内容**: 知识库文档，可能是网页或文章的正文
- **关联**: `document_share_data_lookup`（Join 引擎）用于加速查询
- **`document_share_data_old`**: 旧版文档数据（6393 万行）

### 4. `event_share_data` — 事件数据

- **行数**: 36,229,387
- **引擎**: ReplacingMergeTree
- **内容**: 事件记录，如政治事件、冲突事件等

### 5. `event_geo_share_data` — 事件地理位置

- **行数**: 9,648,685
- **引擎**: MergeTree
- **内容**: 事件关联的地理位置信息

---

## Summary 表（分析结果）

这些表行数较少，存储 AI 分析后的结构化摘要：

| 表名 | 行数 | 内容 |
|---|---|---|
| `activity_summary` | 191 | 活动摘要 |
| `statements_summary` | 190 | 人物言论/表态摘要 |
| `entity_summary` | 132 | 实体分析摘要 |
| `social_media_summary` | 113 | 社交媒体分析摘要 |
| `event_summary` | 91 | 事件分析摘要 |
| `news_summary` | 63 | 新闻分析摘要 |
| `social_media_discussion_summary` | 21 | 社交媒体讨论摘要 |
| `cognitive_summary` | 5 | 认知分析总摘要 |
| `cognitive_AttitudeToChina_summary` | 42 | 对华态度认知分析 |
| `cognitive_Personality_summary` | 30 | 人格分析 |
| `cognitive_Influence_summary` | 30 | 影响力分析 |
| `cognitive_PolicyView_summary` | 29 | 政策观点分析 |
| `cognitive_PoliticalPosition_summary` | 29 | 政治立场分析 |
| `cognitive_Risk_summary` | 29 | 风险分析 |
| `cognitive_GuidingPrinciples_summary` | 18 | 指导原则分析 |
| `cognitive_Character_summary` | 16 | 性格分析 |
| `cognitive_PublicImage_summary` | 15 | 公众形象分析 |
| `cognitive_DecisionMakingMechanism_summary` | 15 | 决策机制分析 |
| `cognitive_BehaviorPattern_summary` | 15 | 行为模式分析 |

---

## 视图

| 视图名 | 说明 |
|---|---|
| `person_event_share_data` | 人物-事件关系视图 |
| `person_statements_share_data` | 人物-言论关系视图 |

---

## 表关系简图

```
                    ┌──────────────────┐
                    │  entity_share_data│  ← 实体（1068万行）
                    │  (person/org/etc) │
                    └────────┬─────────┘
                             │ mongo_id = Head_id
                             ▼
┌───────────────────────────────────────────────┐
│            relation_share_data                │  ← 关系（3.48亿行）
│  Head_id → [relation] → Tail_id               │
│  特朗普 --总统--> 美国                          │
└───────────────────────────────────────────────┘

┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ document_     │   │  event_       │   │  event_geo_   │
│ share_data    │   │  share_data   │   │  share_data   │
│ (6390万行)    │   │ (3623万行)    │   │ (965万行)     │
└───────────────┘   └───────────────┘   └───────────────┘
```

## 说明

- 所有表都在 `goin_new` 数据库中
- 大多数主表使用 **ReplacingMergeTree** 引擎，支持按主键去重
- Summary 表使用 **MergeTree** 引擎，存储 AI 分析产生的结构化摘要
- 两张 **View** 和一张 **MaterializedView** 用于查询加速和数据整合
