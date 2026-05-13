# 基于 ClickHouse 本地知识库的智能问答功能 — 技术方案

---

## 一、背景与目标

### 1.1 背景

DeerFlow 是字节跳动开源的超级智能体框架，具备工具调用、技能系统、多智能体编排等能力。当前平台已接入 Web 搜索、文件操作等通用工具，但缺少对内部知识库的查询能力。

团队维护了一个 ClickHouse 数据库（`goin_new` 库），其中 `entity_share_data` 表存储了约 1067 万条实体数据，涵盖人物、组织、事件、武器等多种类型，是团队积累的高价值结构化知识资产。目前这些数据只能通过 SQL 客户端直接查询，使用门槛高，无法被 AI 智能体直接利用。

### 1.2 目标

在 DeerFlow 框架中开发一套基于 ClickHouse 本地知识库的问答功能，实现以下能力：

1. **自然语言问知识**：用户可以用中文自然语言提问（如"特朗普什么时候出生的？"），AI 自动转化为 SQL 查询
2. **安全的只读查询**：所有查询限制为只读操作，从代码和提示词两个层面杜绝数据篡改
3. **智能的查询策略**：AI 遵循"先了解结构 → 粗查询 → 精细查询"的思路，逐步逼近正确答案
4. **可扩展的架构**：后续可方便地扩展到更多数据表

---

## 二、总体架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    用户提问                              │
│  "特朗普的出生日期是什么？"                               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  DeerFlow 智能体 (Lead Agent)                            │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │  技能系统 (Skill System)                          │    │
│  │  entity-knowledge SKILL.md                        │    │
│  │  • 何时触发: 人物类问题                          │    │
│  │  • 如何使用工具: 先查结构→粗查→细查               │    │
│  │  • 安全约束: 只读查询                             │    │
│  └──────────────────────────────────────────────────┘    │
│                          │                                │
│  ┌──────────────────────────────────────────────────┐    │
│  │  工具层 (Tools)                                   │    │
│  │  ┌─────────────────┐  ┌──────────────────────┐   │    │
│  │  │ get_table_schema │  │ execute_sql          │   │    │
│  │  │ 获取表结构       │  │ 执行 SELECT 查询      │   │    │
│  │  │                  │  │ • 代码级只读校验       │   │    │
│  │  │                  │  │ • 自动过滤空值列       │   │    │
│  │  └─────────────────┘  └──────────────────────┘   │    │
│  └──────────────────────────────────────────────────┘    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  ClickHouse 数据库                                       │
│  goin_new.entity_share_data (~1067万条)                    │
└─────────────────────────────────────────────────────────┘
```

### 2.2 交互流程

```
Step 1: 用户提问 "特朗普的出生日期是什么？"
         ↓
Step 2: 技能系统匹配 → entity-knowledge 技能被激活
         ↓
Step 3: 智能体调用 get_table_schema("entity_share_data")
        获取表结构（列名、类型、注释）
         ↓
Step 4: 智能体分析表结构，定位相关列
        (name, type, date_of_birth, date_of_death 等)
         ↓
Step 5: 智能体调用 execute_sql("SELECT ... WHERE name LIKE '%特朗普%' AND type = 'human'")
         ↓
Step 6: 获取结果，格式化后回复用户
```

---

## 三、工具设计

### 3.1 工具一：`get_table_schema`

获取指定表的列结构信息。

| 属性 | 值 |
|---|---|
| **名称** | `get_table_schema` |
| **参数** | `table_name: str`（默认 `entity_share_data`） |
| **功能** | 查询 `system.columns` 获取列名、类型、注释 |
| **返回** | 格式化的列信息表格 |
| **底层查询** | `SELECT name, type, comment FROM system.columns WHERE database = 'goin_new' AND table = %(table)s ORDER BY position` |

**输出示例**：
```
表: entity_share_data (共 346 列)
  mongo_id                 String
  name                     String               实体名称
  type                     String               实体类型(human/organization/...)
  sex_or_gender            String               性别
  age                      Int64                年龄
  date_of_birth            Int64                出生日期(Unix时间戳)
  date_of_death            Int64                死亡日期(Unix时间戳)
  occupation               String               职业
  country_of_citizenship   String               国籍
  ...
```

**设计说明**：结果以纯文本表格形式返回，便于 LLM 解析列名和对应类型。特别标注 Int64 时间戳列，引导模型使用 `fromUnixTimestamp()` 转换。

### 3.2 工具二：`execute_sql`

执行只读 SQL 查询并返回格式化的结果。

| 属性 | 值 |
|---|---|
| **名称** | `execute_sql` |
| **参数** | `sql: str`（SQL 查询语句）, `compact: bool`（默认 `true`） |
| **功能** | 执行 SELECT 查询，返回格式化结果 |
| **返回** | 格式化的行记录 |

**安全约束（代码层）**：
- SQL 语句必须以 `SELECT`、`WITH`、`DESCRIBE`、`EXPLAIN` 开头
- 明确拒绝 `INSERT`、`UPDATE`、`DELETE`、`DROP`、`ALTER`、`CREATE`、`TRUNCATE`、`OPTIMIZE` 等语句
- 校验失败时返回错误信息，不执行任何操作

**展示优化（compact 模式）**：
当 `compact=True` 时，对查询结果做以下过滤，只显示有实际值的列：
- 跳过 `NULL` 值
- 跳过空字符串 `''`
- 跳过空数组 `[]`
- 跳过数值 `0`
- 跳过空元组

此模式对大宽表尤其重要——大多数行的绝大多数列为空，只显示有值的列能大幅提升可读性。

**查询安全设置**（Client 级别）：
```python
settings={
    'max_execution_time': 30,          # 最长执行 30 秒
    'max_result_bytes': 100_000_000,   # 最多返回 100MB
    'max_rows_to_read': 1_000_000_000, # 最多读取 10 亿行
}
```

### 3.3 ClickHouse 连接管理

- **驱动**: `clickhouse-driver`（`from clickhouse_driver import Client`）
- **连接参数**: 通过 `config.yaml` 的 `clickhouse` 段配置
- **生命周期**: 模块级单例，工具首次调用时建立连接，连接断开时自动重连
- **配置示例**:
  ```yaml
  clickhouse:
    host: 10.208.57.5
    port: 59000
    user: default
    password: ''
    database: goin_new
    secure: false
  ```

---

## 四、技能设计

### 4.1 SKILL.md 配置

技能是 DeerFlow 中引导 AI 行为的关键机制。本功能创建 `entity-knowledge` 技能，通过 `SKILL.md` 文件定义。

**Frontmatter**：
```yaml
name: entity-knowledge
description: >
  Use this skill when the user asks about people, such as
  queries about a person's background, age, occupation,
  or other personal information.
allowed-tools:
  - get_table_schema
  - execute_sql
```

### 4.2 技能指令要点

SKILL.md 正文中向 AI 模型提供的指引：

1. **触发条件**
   - 用户询问人物信息（如"特朗普是谁？""拜登的年龄"）

2. **工作流程**
   ```
   ① 不确定表结构 → 先调用 get_table_schema
   ② 写 SQL 查询   → 从简单条件开始，逐步精确
   ③ 结果过多       → 调整 LIMIT 或使用更精确的 WHERE
   ④ 结果过少       → 放宽条件重试
   ```

3. **SQL 编写规范**
   - 只使用 `SELECT` 语句，绝不修改数据
   - 时间戳列（`date_of_birth`、`date_of_death` 等 Int64 类型）使用 `fromUnixTimestamp()` 转换
   - 尽量只查询需要的列，避免 `SELECT *`

4. **仅限 `entity_share_data` 表**
   - 所有查询限定在该表范围内

### 4.3 安全约束总览

| 层面 | 措施 |
|---|---|
| **代码层** | `execute_sql` 拒绝非 SELECT 语句 |
| **提示词层** | SKILL.md 明确要求只生成 SELECT 查询 |
| **工具层** | 技能只开放 2 个工具，不暴露 bash 等危险工具 |
| **连接层** | ClickHouse Client 配置执行超时和读取上限 |

---

## 五、配置变更

### 5.1 `config.yaml` 新增内容

```yaml
# --- ClickHouse 本地知识库 ---
clickhouse:
  host: 10.208.57.5
  port: 59000
  user: default
  password: ''
  database: goin_new
  secure: false

# --- 工具组新增 ---
tool_groups:
  - name: knowledge

# --- 工具注册新增 ---
tools:
  - name: get_table_schema
    group: knowledge
    use: deerflow.tools.database.tools:get_table_schema_tool
  - name: execute_sql
    group: knowledge
    use: deerflow.tools.database.tools:execute_sql_tool
```

### 5.2 新增文件清单

```
backend/packages/harness/deerflow/tools/database/
  __init__.py          # 空文件
  tools.py             # get_table_schema_tool + execute_sql_tool

skills/public/entity-knowledge/
  SKILL.md             # 技能定义（触发条件 + 使用指引）
```

---

## 六、风险与注意事项（按优先级排列）

### 6.1 DDL/DML 误操作（最高优先级）

| 风险 | 说明 |
|---|---|
| 模型生成 DDL/DML 语句 | AI 可能输出 `DROP TABLE`、`ALTER TABLE`、`INSERT`、`DELETE` 等破坏性语句 |

**建议**：
1. **代码层**：`execute_sql` 工具执行前校验 SQL 前缀，只允许 SELECT/WITH/DESCRIBE/EXPLAIN
2. **数据库层**：在 ClickHouse 中创建**只读用户**（`readonly=1`），AI 工具使用该用户连接，而非 `default` 超级用户。这样即使代码层校验失效，数据库层面仍有防护
3. **连接层**：配置 `max_execution_time` 等安全上限，避免资源耗尽

### 6.2 SQL 注入

| 风险 | 说明 |
|---|---|
| 恶意输入篡改 SQL | 模型生成的 SQL 或用户输入可能包含恶意内容，改变查询语义 |

**建议**：
1. 使用参数化查询（`%(name)s`），避免拼接 SQL 字符串
2. 代码层二次校验，确认语句属于只读操作
3. 限制数据库用户权限，让注入语句即使执行也无法生效

### 6.3 数据泄露

| 风险 | 说明 |
|---|---|
| 越权查询 | 模型可能查询到不应公开的数据，或用户通过 Prompt 注入诱导查询 |

**建议**：
1. 技能限定只激活在 `entity_share_data` 表范围内
2. ClickHouse 层面可通过行级权限（`SQL_ROW_POLICY`）做进一步约束
3. 后续可增加查询审计日志，记录所有 AI 发起的查询

### 6.4 性能风险

| 风险 | 说明 | 缓解措施 |
|---|---|---|
| 全表扫描 | 无 WHERE 条件的查询会扫描全部 1067 万行 | 设置 `max_execution_time: 30s` 和 `max_rows_to_read: 1B` |
| 大结果集 | 查询返回过多数据 | 设置 `max_result_bytes: 100MB`；引导模型使用 LIMIT |
| JOIN 操作 | `relation_share_data` 3.4 亿行，JOIN 会导致超时 | 技能指引中明确建议分两步查询代替 JOIN |

### 6.5 后续规划

1. **扩展到更多表**：在技能配置中增加更多表的描述
2. **表关系理解**：将 `relation_share_data` 的关系数据纳入问答范围
3. **查询缓存**：对高频查询做结果缓存，减少 ClickHouse 压力
4. **查询审计**：记录所有查询日志，便于排查和优化

---
