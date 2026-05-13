# SQL 入门教程 — 面向新手

> 基于 ClickHouse + `entity_share_data` 表（约 1100 万行，346 列）
> 目标：理解 SQL 的**思维方式**，而非死记语法

---

## 零、SQL 是什么

SQL 不是编程语言，是**描述问题**的语言——你说"我想要什么"，数据库自己决定"怎么找"。

对比：
```python
# Python：你告诉电脑每一步怎么做
count = 0
for row in data:
    if row['type'] == 'human':
        count += 1
```

```sql
-- SQL：你只描述要什么
SELECT count() FROM entity_share_data WHERE type = 'human';
```

---

## 一、SELECT — 从表里取东西

这是 SQL 最核心的动作。理解它最好类比**超市购物**：

```
你站在货架前（FROM entity_share_data）
↓
你挑想要的商品（SELECT name, type, age）
↓
如果有条件就筛选（WHERE type = 'human')
```

```sql
-- 查某列
SELECT name FROM entity_share_data;

-- 查多列，用逗号分隔
SELECT name, type, age FROM entity_share_data;

-- 查全部列（用 *，但不推荐在大表用）
SELECT * FROM entity_share_data;
```

**新手最容易忽略的点：** SQL 执行的顺序不是从左到右写的。你写 `SELECT name FROM table WHERE type='human'`，但数据库实际是先找表（FROM），再过滤（WHERE），最后取出你选的列（SELECT）。

---

## 二、WHERE — 加条件过滤

WHERE 后面的条件只有两种结果：**这行留下**或**这行丢掉**。

```sql
-- 等于
WHERE type = 'human'

-- 不等于
WHERE type != 'human'

-- 模糊匹配（% 是通配符，匹配任意字符）
WHERE name LIKE '%特朗普%'   -- 名字里包含"特朗普"三个字
WHERE name LIKE '特朗普%'    -- 以"特朗普"开头
WHERE name LIKE '%特朗普'    -- 以"特朗普"结尾
```

**直觉理解：** 把表想象成 Excel 表格，WHERE 就是在点"筛选"按钮，不满足条件的行被隐藏。

**多条件组合：**

```sql
-- AND：两个条件都要满足
WHERE type = 'human' AND age > 50

-- OR：满足一个就行
WHERE type = 'human' OR type = 'organization'

-- AND 和 OR 混用，括号控制优先级
WHERE (type = 'human' OR type = 'organization')
  AND age > 0
```

---

## 三、LIMIT 和 ORDER BY — 控制输出

```sql
-- LIMIT：只看前几条（相当于 Excel 里"前 N 项"）
SELECT name FROM entity_share_data LIMIT 5;

-- ORDER BY：排序（ASC 升序，DESC 降序）
SELECT name, age FROM entity_share_data
WHERE type = 'human' AND age > 0
ORDER BY age DESC;   -- 从大到小

-- 组合：取年龄最大的 10 个人
SELECT name, age FROM entity_share_data
WHERE type = 'human' AND age > 0
ORDER BY age DESC
LIMIT 10;
```

**执行顺序在这里就能看出来了：** WHERE 先过滤，ORDER BY 再排序，LIMIT 最后截断。不是按写的顺序执行的。

---

## 四、DISTINCT — 去重

```sql
-- 看 type 列一共有几种值
SELECT DISTINCT type FROM entity_share_data;
```

**直觉理解：** 把某列复制出来，删除重复项。相当于 Excel 的"删除重复值"。

不加 DISTINCT：
```
human
human
human
organization
human
weapon
```
加 DISTINCT：
```
human
organization
weapon
```

---

## 五、GROUP BY — 分组统计

这是 SQL 最难理解但也最强大的功能。

**一句话直觉：把相同的行堆在一起，压成一行。**

看 `type` 列：
```
type
human
human
organization
human    → 压成三组 →  human (3条)
weapon               organization (1条)
                     weapon (1条)
```

然后对每组做统计：
```sql
SELECT type, count() AS cnt   -- count() 算每组有多少行
FROM entity_share_data
GROUP BY type;
```

结果：
| type | cnt |
|---|---|
| human | 3,720,754 |
| organization | 920,330 |
| weapon | 43,128 |

**核心规则（新手最容易犯错）：** 只要用了 GROUP BY，SELECT 里出现的列要么在 GROUP BY 里，要么套上聚合函数（count/sum/avg/min/max）。

```sql
-- ✅ 正确：type 在 GROUP BY 里，age 套了 avg
SELECT type, avg(age) FROM ... GROUP BY type;

-- ❌ 错误：age 既不在 GROUP BY 里，也没套聚合函数
SELECT type, age FROM ... GROUP BY type;
```

**常见聚合函数：**

| 函数 | 作用 |
|---|---|
| `count()` | 计数 |
| `count(DISTINCT 列)` | 去重后计数 |
| `avg(列)` | 平均值 |
| `sum(列)` | 总和 |
| `min(列)` | 最小值 |
| `max(列)` | 最大值 |

---

## 六、HAVING — 对分组结果再过滤

WHERE 是分组前过滤行，HAVING 是分组后过滤组：

```sql
-- WHERE 先过滤掉 type 为空的行
-- GROUP BY 按 type 分组
-- HAVING 只保留超过 100 万条的组
SELECT type, count() AS cnt
FROM entity_share_data
WHERE type > ''
GROUP BY type
HAVING cnt > 1000000
ORDER BY cnt DESC;
```

**直观区别：**
- WHERE = 查**人口**时，先筛掉未满 18 岁的
- HAVING = 分组后，只看**超过 1000 人的城市**

---

## 七、完整执行顺序（最重要的一张表）

```sql
SELECT type, count() AS cnt        -- 5. 选要显示的列
FROM entity_share_data              -- 1. 从哪张表取
WHERE type = 'human'                -- 2. 过滤行
GROUP BY type                       -- 3. 分组
HAVING cnt > 1000                   -- 4. 过滤组
ORDER BY cnt DESC                   -- 6. 排序
LIMIT 10;                           -- 7. 截断
```

**不是按写的顺序执行的！** 数据库的执行顺序是：

`FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT`

理解这个顺序是学 SQL 最重要的一个概念。比如为什么 HAVING 里不能用 SELECT 里取的别名？因为 HAVING 执行在 SELECT 之前。

---

## 八、JOIN — 合并两张表

JOIN 就是把两张表**按某个共同的列拼在一起**。

```
entity_share_data (实体表)           relation_share_data (关系表)
┌──────────┬─────────┐             ┌──────────┬──────────┐
│ mongo_id │ name    │             │ Head_id  │ type     │
├──────────┼─────────┤             ├──────────┼──────────┤
│ Q22686   │ 特朗普  │             │ Q22686   │ subject  │
│ Q12345   │ 拜登    │             │ Q22686   │ spouse   │
└──────────┴─────────┘             │ Q12345   │ subject  │
                                   └──────────┴──────────┘
```

**INNER JOIN**（默认 JOIN）：**两边都有的才保留**
```sql
SELECT e.name, r.type
FROM entity_share_data AS e
JOIN relation_share_data AS r ON e.mongo_id = r.Head_id;
```
→ 特朗普和拜登都出现（他们都在关系表里有记录）

**LEFT JOIN**：**左表全保留，右边没有就 NULL**
```sql
SELECT e.name, r.type
FROM entity_share_data AS e
LEFT JOIN relation_share_data AS r ON e.mongo_id = r.Head_id;
```
→ 左表所有实体都出现，没有关系的右边显示 NULL

**新手直觉：** JOIN = 在 Excel 里用 VLOOKUP 把两列拼在一起。LEFT JOIN = 保留所有行，找不到的就留空。

---

## 九、子查询 — 查询里面套查询

有时候你需要先查一个中间结果，再在这个结果上查。用括号包起来就行：

```sql
-- 找出"type 数量超过 100 万的那些 type"下所有的人
SELECT name, type
FROM entity_share_data
WHERE type IN (
    SELECT type
    FROM entity_share_data
    GROUP BY type
    HAVING count() > 1000000
);
```

**执行顺序：先执行括号里的，把结果当成一个临时列表，再执行外面的。**

---

## 十、常见误区

### 1. 以为 SELECT * 没问题
```sql
-- ❌ entity_share_data 有 346 列，查出来巨量数据
SELECT * FROM entity_share_data;

-- ✅ 只取需要的 2 列
SELECT name, type FROM entity_share_data;
```

### 2. 混不清 WHERE 和 HAVING
```sql
-- WHERE 过滤原始行（分组前）
WHERE age > 0

-- HAVING 过滤分组结果（分组后）
HAVING count() > 100
```

### 3. 字符串值不用引号
```sql
WHERE name = 特朗普      -- ❌ 语法错误
WHERE name = '特朗普'     -- ✅ 正确
```

### 4. 以为 JOIN 总是快
ClickHouse 的 JOIN 在右表很大时非常慢（几亿行要全加载）。**能分两步查就分两步查。**

---

---

## 十一、SQL 语句分类：读 vs 写

不是所有 SQL 都是查数据的。按权限分为两类：

### 只读（查询类）

这些语句**不改数据**，可以安全执行：

| 关键词 | 含义 | 示例 |
|---|---|---|
| **SELECT** | 查询数据 | `SELECT * FROM entity_share_data` |
| **WITH** | CTE（公用表表达式），本质也是 SELECT | `WITH filtered AS (SELECT ...) SELECT ...` |
| **DESCRIBE** | 查看表结构 | `DESCRIBE TABLE entity_share_data` |
| **EXPLAIN** | 查看执行计划（数据库怎么执行你的查询） | `EXPLAIN PLAN SELECT ...` |

### 写操作（修改类）

这些语句**改变数据或结构**，在只读场景下要禁止：

| 关键词 | 含义 | 风险 |
|---|---|---|
| **INSERT** | 插入新数据 | 会往表里写新行 |
| **UPDATE** | 修改已有数据 | 改变现有行的值 |
| **DELETE** | 删除数据 | 删掉行 |
| **DROP** | 删除表/数据库 | 整张表消失，数据丢失 |
| **ALTER** | 修改表结构（加列、删列、改类型） | 改变表定义 |
| **CREATE** | 创建表/数据库 | 建新对象 |
| **TRUNCATE** | 清空表数据 | 全表数据一次性删除 |
| **OPTIMIZE** | 强制合并数据片段 | 后端资源消耗大 |
| **RENAME** | 重命名表 | 改表名 |
| **ATTACH** / **DETACH** | 挂载/卸载表 | 加删表但不删数据文件 |
| **SYSTEM** | 系统级操作（刷新视图、清空缓存） | 影响数据库状态 |
| **KILL** | 终止正在执行的查询 | 中断其他查询 |
| **SET** | 修改会话配置 | 改变运行环境 |

### 为什么要在意这个分类？

在 AI 智能体查询数据库的场景下，必须从**两个层面**限制只读：

1. **代码层**：工具执行 SQL 前检查关键词，拒绝写操作
2. **提示词层**：告诉模型只能生成 SELECT 语句

只靠提示词不安全——模型可能犯错或被注入攻击。只靠代码也不够——模型需要理解边界才能写出正确的 SQL。双重保障才能防止"AI 把表删了"这种事故。

---

## 总结——SQL 思维方式

写 SQL 时，问自己三个问题：

1. **要查的数据在哪？** → FROM
2. **我只要其中哪部分？** → WHERE
3. **我想要逐行看还是合并统计？** → 逐行看就 SELECT，统计就 GROUP BY

SQL 不复杂，它只是把你想做的事情用文字描述出来。每多学一个关键词，就是你多会了一种描述问题的方式。
