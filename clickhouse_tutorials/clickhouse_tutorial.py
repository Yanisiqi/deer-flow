"""
ClickHouse 入门教程 — 循序渐进掌握基本功能
=============================================

用法:
  python -i clickhouse_tutorial.py     # 进入交互模式，然后逐个调用章节函数
  或
  from clickhouse_tutorial import *    # 在现有 REPL 中导入

示例:
  >>> chapter_01()
  >>> chapter_02()

每章独立，可任意顺序执行，但建议从 chapter_00 开始。
请将代码中的 <列名>、<条件> 替换为 entity_share_data 的实际列名。
"""

from clickhouse_driver import Client

CLICKHOUSE = {
    'host': '10.208.57.5',
    'port': 59000,
    'user': 'default',
    'password': '',
    'database': 'goin_new',
    'secure': False,
}

client = Client(**CLICKHOUSE)

# ────────────────────────────────────────────────────────────
# 辅助函数：只显示有实际值的列
# ────────────────────────────────────────────────────────────

def inspect_rows(rows, columns=None, max_width=80):
    """
    打印查询结果，每行只显示有实际值的列。

    rows : client.execute() 返回的行列表
    columns : 列名列表（不传则用 col_0, col_1...）
    max_width : 每个值截断长度
    """
    if not rows:
        print("(空结果)")
        return

    if columns is None:
        columns = [f'col_{i}' for i in range(len(rows[0]))]

    for row_idx, row in enumerate(rows):
        print(f"\n--- 行 {row_idx + 1} ---")
        has_any = False
        for i, val in enumerate(row):
            if i >= len(columns):
                break
            if val is None:
                continue
            if isinstance(val, (list, tuple)) and len(val) == 0:
                continue
            if isinstance(val, str) and val == '':
                continue
            if isinstance(val, (int, float)) and val == 0:
                continue
            val_str = str(val)
            if len(val_str) > max_width:
                val_str = val_str[:max_width] + '...'
            print(f"  {columns[i]:45s} = {val_str}")
            has_any = True
        if not has_any:
            print("  (所有列均为空/默认值)")


# ════════════════════════════════════════════════════════════
# 第〇章：连接测试
# ════════════════════════════════════════════════════════════
def chapter_00():
    """连接测试 — 验证能正常访问 ClickHouse"""
    print(client.execute('SELECT 1'))
    print(client.execute('SELECT version()'))

    # 查看 entity_share_data 有哪些列
    columns = client.execute("""
        SELECT name, type, comment
        FROM system.columns
        WHERE database = 'goin_new' AND table = 'entity_share_data'
        ORDER BY position
    """)
    print(f"\nentity_share_data 列信息 ({len(columns)} 列):")
    for name, typ, comment in columns:
        print(f"  {name:30s} {typ:30s} {comment or ''}")

    # 打印所有表名及其结构
    print("\n\ngoin_new 库所有表结构:")
    tables = client.execute("""
        SELECT name, engine, total_rows
        FROM system.tables
        WHERE database = 'goin_new'
        ORDER BY total_rows DESC
    """)
    for tbl_name, engine, total_rows in tables:
        cols = client.execute("""
            SELECT name, type
            FROM system.columns
            WHERE database = 'goin_new' AND table = %(table)s
            ORDER BY position
        """, {'table': tbl_name})
        row_str = f"{total_rows or 'N/A':>12,}" if total_rows and total_rows > 0 else f"{'N/A':>12}"
        print(f"\n  📋 {tbl_name:45s} 引擎: {engine:25s} 行数: {row_str}")
        for col_name, col_type in cols:
            print(f"      {col_name:40s} {col_type}")


# ════════════════════════════════════════════════════════════
# 第一章：基础查询 — SELECT FROM WHERE
# ════════════════════════════════════════════════════════════
def chapter_01():
    """基础查询：SELECT / WHERE / LIMIT / DISTINCT / ORDER BY"""
    # 总行数
    cnt = client.execute("SELECT count() FROM entity_share_data")[0][0]
    print(f"总行数: {cnt}")

    # 预览前 5 行
    print("\n前 5 行:")
    for row in client.execute("SELECT * FROM entity_share_data LIMIT 5"):
        print(row)

    # 去重
    print("去重查询:")
    rows = client.execute('''
        SELECT DISTINCT type FROM entity_share_data
        LIMIT 20
    ''')
    for row in rows:
        print(row)

    # 条件查询 — 用 inspect_rows 只看有值的列
    print("\n条件查询 (human 实体，仅显示有值的列):")
    # 先拿到列名
    col_names = [r[0] for r in client.execute("""
        SELECT name FROM system.columns
        WHERE database = 'goin_new' AND table = 'entity_share_data'
        ORDER BY position
    """)]
    # print(f"column_names: {col_names}")
    rows = client.execute('''
        SELECT * FROM entity_share_data
        WHERE type = 'administrative'
        LIMIT 3
    ''')
    inspect_rows(rows, columns=col_names)

    # 指定人名查询
    print("\n指定人名查询:")
    rows = client.execute('''
        SELECT * FROM entity_share_data
        WHERE name like '%唐纳德·特朗普%'
        AND type = 'human'
''')
    inspect_rows(rows, columns=col_names)

    # 带时间戳转换的查询（Int64 → 年月日）
    print("\n指定人名查询 (时间戳已转换):")
    rows = client.execute('''
        SELECT
            name,
            type,
            sex_or_gender,
            age,
            fromUnixTimestamp(date_of_birth) AS date_of_birth,
            fromUnixTimestamp(date_of_death) AS date_of_death,
            position_experience.position,
            arrayMap(x -> fromUnixTimestamp(x), position_experience.pos_start_time) AS pos_start,
            arrayMap(x -> fromUnixTimestamp(x), position_experience.pos_end_time) AS pos_end,
            occupation,
            country_of_citizenship,
            residence
        FROM entity_share_data
        WHERE name LIKE '%唐纳德·特朗普%'
          AND type = 'human'
    ''')
    for row in rows:
        for col, val in zip(
            ['name','type','sex_or_gender','age','date_of_birth','date_of_death',
             'position','pos_start','pos_end','occupation','country','residence'], row):
            print(f"  {col:20s} = {val}")
        print()
    

    # 排序
    # print("排序查询:")
    # rows = client.execute('''
    #     SELECT name, type, age, date_of_birth FROM entity_share_data
    #       WHERE age > 0
    #     ORDER BY age DESC
    #     LIMIT 10
    # ''')
    # for row in rows:
    #     print(row)

# ════════════════════════════════════════════════════════════
# 第二章：聚合查询 — GROUP BY
# ════════════════════════════════════════════════════════════
def chapter_02():
    """聚合查询：GROUP BY / count / avg / sum / min / max / HAVING"""
    print("按 <列名> 分组计数（请替换 <列名>）:")
    rows = client.execute('''
        SELECT type, count() AS cnt
        FROM entity_share_data
        GROUP BY type
        ORDER BY cnt DESC
        LIMIT 20
    ''')
    for row in rows:
        print(row)

    print("\n多种聚合 — 按实体类型统计:")
    rows = client.execute('''
        SELECT
            type,
            count()                AS cnt,
            count(DISTINCT industry) AS unique_industries
        FROM entity_share_data
        GROUP BY type
        ORDER BY cnt DESC
        LIMIT 10
    ''')
    for row in rows:
        print(row)

    print("\nHAVING 过滤 — 只显示超过 100 条的实体类型:")
    rows = client.execute('''
        SELECT
            type,
            count() AS cnt
        FROM entity_share_data
        GROUP BY type
        HAVING cnt > 100
        ORDER BY cnt DESC
    ''')
    for row in rows:
        print(row)


# ════════════════════════════════════════════════════════════
# 第三章：日期与时间处理
# ════════════════════════════════════════════════════════════
def chapter_03():
    """日期时间函数：按天/周/月聚合、dateDiff、formatDateTime"""
    print("使用 create_time(DateTime) 和 date_of_birth(Int64) 做演示\n")

    print("1) 按天统计 — 每天创建了多少实体:")
    rows = client.execute('''
        SELECT toDate(create_time) AS day, count() AS cnt
        FROM entity_share_data
        GROUP BY day
        ORDER BY day DESC
        LIMIT 10
    ''')
    for row in rows:
        print(f"  {row[0]}  {row[1]:>8,} 条")
    print("  ...")

    print("\n2) 按周 / 月统计:")
    rows = client.execute('''
        SELECT
            toStartOfMonth(create_time) AS month,
            count() AS cnt
        FROM entity_share_data
        GROUP BY month
        ORDER BY month DESC
        LIMIT 10
    ''')
    for row in rows:
        print(f"  {row[0]}  {row[1]:>10,} 条")

    print("\n3) 时间区间筛选 — 统计 2024 年每月创建量:")
    rows = client.execute('''
        SELECT
            toStartOfMonth(create_time) AS month,
            count() AS cnt
        FROM entity_share_data
        WHERE create_time >= '2024-01-01'
          AND create_time < '2025-01-01'
        GROUP BY month
        ORDER BY month
    ''')
    for row in rows:
        print(f"  {row[0]}  {row[1]:>8,} 条")

    print("\n4) 时间戳转换 (Int64 → 日期) — 人物出生日期:")
    rows = client.execute('''
        SELECT
            name,
            fromUnixTimestamp(date_of_birth) AS birth_date,
            dateDiff('year', fromUnixTimestamp(date_of_birth), now()) AS age_now
        FROM entity_share_data
        WHERE type = 'human' AND date_of_birth > 0
        ORDER BY date_of_birth DESC
        LIMIT 10
    ''')
    for row in rows:
        print(f"  {row[0]:20s}  出生: {row[1]}  年龄: {row[2]}")


# ════════════════════════════════════════════════════════════
# 第四章：条件与过滤进阶
# ════════════════════════════════════════════════════════════
def chapter_04():
    """进阶过滤：IN / LIKE / multiSearchAny / countIf / CASE"""
    print("1) IN 子句 — 查指定类型的实体:")
    rows = client.execute('''
        SELECT type, count() AS cnt
        FROM entity_share_data
        WHERE type IN ('human', 'organization', 'weapon')
        GROUP BY type
        ORDER BY cnt DESC
    ''')
    for row in rows:
        print(f"  {row[0]:20s}  {row[1]:>8,}")

    print("\n2) LIKE 模糊匹配 — 搜索名称含'华为'的实体:")
    rows = client.execute('''
        SELECT name, type, industry
        FROM entity_share_data
        WHERE name LIKE '%华为%'
        LIMIT 10
    ''')
    for row in rows:
        print(f"  {row[0]:20s}  {row[1]:15s}  {row[2] or '-'}")

    print("\n3) multiSearchAny — 同时搜多个关键词:")
    rows = client.execute('''
        SELECT name, type
        FROM entity_share_data
        WHERE multiSearchAny(name, ['特朗普', '拜登', '奥巴马'])
          AND type = 'human'
        LIMIT 10
    ''')
    for row in rows:
        print(f"  {row[0]:20s}  {row[1]}")

    print("\n4) countIf — 条件计数:")
    rows = client.execute('''
        SELECT
            count() AS total_entities,
            countIf(type = 'human') AS humans,
            countIf(type = 'organization') AS organizations,
            countIf(age > 0) AS has_age
        FROM entity_share_data
    ''')
    for row in rows:
        print(f"  总实体: {row[0]:>10,}")
        print(f"  人物:   {row[1]:>10,}")
        print(f"  组织:   {row[2]:>10,}")
        print(f"  有年龄: {row[3]:>10,}")

    print("\n5) 多条件组合 — 搜索中国组织类实体:")
    rows = client.execute('''
        SELECT name, type, industry
        FROM entity_share_data
        WHERE (name LIKE '%中国%' OR name LIKE '%China%')
          AND type = 'organization'
          AND industry > ''
        LIMIT 10
    ''')
    for row in rows:
        print(f"  {row[0]:25s}  {row[1]:15s}  {row[2]}")


# ════════════════════════════════════════════════════════════
# 第五章：多表 JOIN
# ════════════════════════════════════════════════════════════
def chapter_05():
    """JOIN 操作与替代方案"""
    print("⚠️ relation_share_data 有 3.4 亿行，直接 JOIN 会卡住。")
    print("推荐用「分两步查」代替一次 JOIN：\n")

    print("1) 分两步查 — 先查实体 ID，再查关系:")
    # 第一步：查 mongo_id
    entities = client.execute("""
        SELECT mongo_id, name FROM entity_share_data
        WHERE name = '唐纳德·特朗普' AND type = 'human'
    """)
    if entities:
        mongo_id, name = entities[0]
        # 第二步：直接用 mongo_id 查关系表
        rows = client.execute("""
            SELECT type, Tail_id, Tail_name, Tail_title, Tail_type
            FROM goin_new.relation_share_data
            WHERE Head_id = %(id)s
            LIMIT 20
        """, {'id': mongo_id})
        print(f"  实体: {name} (mongo_id: {mongo_id})")
        for rel_type, tail_id, tail_name, tail_title, tail_type in rows:
            display = tail_title or tail_name or '(无标题)'
            print(f"    --[{rel_type}]-->  {display}  ({tail_type})")
        print(f"  共查到 {len(rows)} 条关系")
        print(f"  共查到 {len(rows)} 条关系")

    print("""
    为什么分两步快？
      一次 JOIN → ClickHouse 需要全量加载右表（3.4 亿行）构建哈希表
      分两步查  → 第一次走主键索引定位实体，第二次按 Head_id 过滤
                   Head_id 有主键排序，数据量小得多
    """)

    # 以下 JOIN 语法示例保留作参考，但实际不执行（避免卡死）
    print("2) JOIN 语法参考（仅展示，不执行）:")
    print("""    -- 小表 JOIN 小表时可用
    SELECT e.name, r.type, r.Tail_id
    FROM entity_share_data AS e
    LEFT JOIN goin_new.relation_share_data AS r
        ON e.mongo_id = r.Head_id
    WHERE e.name = '唐纳德·特朗普' AND e.type = 'human'
    LIMIT 20

    -- GLOBAL JOIN：右表数据广播到所有节点，减少网络传输
    SELECT e.name, r.type, r.Tail_id
    FROM entity_share_data AS e
    GLOBAL LEFT JOIN goin_new.relation_share_data AS r
        ON e.mongo_id = r.Head_id
    WHERE e.name = '唐纳德·特朗普' AND e.type = 'human'
    LIMIT 10
    """)

    print("3) Dictionary 替代 JOIN（生产环境推荐）:")
    print("""    -- DBA 执行一次（需要权限）：
    CREATE DICTIONARY goin_new.entity_dict
    (
        mongo_id String,
        name String,
        type String
    )
    PRIMARY KEY mongo_id
    SOURCE(CLICKHOUSE(TABLE 'entity_share_data'))
    LIFETIME(MIN 300 MAX 600)
    LAYOUT(HASHED())

    -- 应用层用 dictGet 代替 JOIN（极快）：
    SELECT
        Head_id AS entity_id,
        dictGet('goin_new.entity_dict', 'name', Head_id) AS entity_name,
        type AS relation_type
    FROM goin_new.relation_share_data
    LIMIT 10
    """)

    print("""对比：
    ┌──────────────┬──────────────────────────────────┬──────────────────────┐
    │              │  JOIN                            │  Dictionary          │
    ├──────────────┼──────────────────────────────────┼──────────────────────┤
    │ 速度         │  每次查询都要做 JOIN             │  预加载到内存，接近  │
    │              │                                   │  零开销              │
    │ 适用场景     │  右表小、临时关联                │  右表大、频繁关联    │
    │ 配置         │  SQL 里直接写 ON                 │  需 DBA 提前建字典   │
    │ 实时性       │  实时                            │  有缓存延迟          │
    └──────────────┴──────────────────────────────────┴──────────────────────┘
    """)


# ════════════════════════════════════════════════════════════
# 第六章：子查询与 CTE
# ════════════════════════════════════════════════════════════
def chapter_06():
    """子查询 与 WITH (CTE)"""
    print("1) 子查询:")
    print("""示例:
    rows = client.execute('''
        SELECT <列>, count() AS cnt
        FROM (
            SELECT * FROM entity_share_data WHERE <条件>
        )
        GROUP BY <列>
    ''')
    """)

    print("\n2) WITH CTE:")
    print("""示例:
    rows = client.execute('''
        WITH filtered AS (
            SELECT * FROM entity_share_data WHERE <条件>
        )
        SELECT <列>, count() AS cnt
        FROM filtered
        GROUP BY <列>
    ''')
    """)

    print("\n3) WHERE IN 子查询:")
    print("""示例:
    rows = client.execute('''
        SELECT *
        FROM entity_share_data
        WHERE <列> IN (
            SELECT <列> FROM entity_share_data
            GROUP BY <列>
            HAVING count() > 10
        )
        LIMIT 100
    ''')
    """)


# ════════════════════════════════════════════════════════════
# 第七章：窗口函数
# ════════════════════════════════════════════════════════════
def chapter_07():
    """窗口函数：ROW_NUMBER / RANK / 移动聚合"""
    print("1) ROW_NUMBER / RANK 排名:")
    print("""示例:
    rows = client.execute('''
        SELECT
            <列>,
            <数值列>,
            row_number() OVER (PARTITION BY <分组列> ORDER BY <数值列> DESC) AS rn,
            rank()       OVER (PARTITION BY <分组列> ORDER BY <数值列> DESC) AS rk
        FROM entity_share_data
        LIMIT 50
    ''')
    """)

    print("\n2) 每组 TOP N:")
    print("""示例:
    rows = client.execute('''
        SELECT *
        FROM (
            SELECT *,
                row_number() OVER (PARTITION BY <分组列> ORDER BY <数值列> DESC) AS rn
            FROM entity_share_data
        )
        WHERE rn <= 3
    ''')
    """)

    print("\n3) 移动聚合（7 天滚动窗口）:")
    print("""示例:
    rows = client.execute('''
        SELECT
            toDate(<时间列>) AS day,
            count() AS daily_cnt,
            sum(count()) OVER (
                ORDER BY toDate(<时间列>)
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) AS rolling_7day
        FROM entity_share_data
        GROUP BY day
        ORDER BY day
    ''')
    """)


# ════════════════════════════════════════════════════════════
# 第八章：数据写入
# ════════════════════════════════════════════════════════════
def chapter_08():
    """数据写入 — 推荐批量 INSERT"""
    print("1) 插入单行:")
    print("""示例:
    client.execute('''
        INSERT INTO entity_share_data
        VALUES (%(val1)s, %(val2)s, %(val3)s)
    ''', {'val1': 'xxx', 'val2': 123, 'val3': '2025-06-01'})
    """)

    print("\n2) 批量插入（推荐方式）:")
    print("""示例:
    import datetime
    data = [
        ('a', 1, datetime.datetime.now()),
        ('b', 2, datetime.datetime.now()),
        ('c', 3, datetime.datetime.now()),
    ]
    client.execute(
        'INSERT INTO entity_share_data (<列1>, <列2>, <时间列>) VALUES',
        data
    )
    """)

    print("💡 ClickHouse 适合批量写入（每批 > 1000 行），避免逐行 insert")


# ════════════════════════════════════════════════════════════
# 第九章：元数据与表操作
# ════════════════════════════════════════════════════════════
def chapter_09():
    """查看元数据：建表语句、分区、表大小"""
    # 建表语句
    ddl = client.execute("SHOW CREATE TABLE entity_share_data")[0][0]
    print("建表语句:")
    print(ddl)

    # 表分区信息
    print("\n分区信息:")
    rows = client.execute("""
        SELECT
            database,
            table,
            partition,
            name AS part_name,
            rows,
            formatReadableSize(bytes_on_disk) AS size,
            min_date,
            max_date
        FROM system.parts
        WHERE database = 'goin_new' AND table = 'entity_share_data' AND active = 1
        ORDER BY partition
    """)
    for row in rows:
        print(
            f"  分区={row[2]}  行数={row[4]:>12,}  大小={row[5]:>10s}"
            f"  日期=[{row[6]}, {row[7]}]"
        )

    # 所有表大小排行
    print("\ngoin_new 库表大小排行:")
    rows = client.execute("""
        SELECT
            table,
            formatReadableSize(sum(bytes_on_disk)) AS size,
            sum(rows) AS total_rows
        FROM system.parts
        WHERE database = 'goin_new' AND active = 1
        GROUP BY table
        ORDER BY sum(bytes_on_disk) DESC
    """)
    for tbl, size, rows_cnt in rows:
        print(f"  {tbl:30s}  {size:>10s}  {rows_cnt:>12,} rows")


# ════════════════════════════════════════════════════════════
# 第十章：实用技巧
# ════════════════════════════════════════════════════════════
def chapter_10():
    """采样 / HTTP备用 / 超时设置 / EXPLAIN / 避坑"""
    print("1) 采样查询（大表提速）:")
    print("""示例:
    rows = client.execute('''
        SELECT count()
        FROM entity_share_data
        SAMPLE 0.1
    ''')
    """)

    print("\n2) HTTP 协议连接（Native 不通时的备用方案）:")
    print("""示例:
    from clickhouse_driver.http import HttpClient
    http_client = HttpClient(
        host='10.208.57.5', port=58123,
        user='default', password='', database='goin_new',
    )
    """)

    print("\n3) 查询超时设置:")
    print("""示例:
    safe_client = Client(**CLICKHOUSE, settings={
        'max_execution_time': 30,
        'max_result_bytes': 100_000_000,
        'max_rows_to_read': 1_000_000_000,
    })
    """)

    print("\n4) EXPLAIN 查看执行计划:")
    print("""示例:
    rows = client.execute('''
        EXPLAIN PLAN
        SELECT count() FROM entity_share_data WHERE <某列> = 'xxx'
    ''')
    for step in rows:
        print(step[0])
    """)

    print("\n5) 避免的坑:")
    print("""  ✗ for 循环单行 insert        → ✓ 批量 1000+ 行 INSERT
  ✗ SELECT * 无脑使用          → ✓ 只选需要的列
  ✗ 频繁 ALTER TABLE           → ✓ 设计时规划好 Schema
  ✗ 大表无 WHERE 全表扫描      → ✓ 尽量带分区键过滤
""")


# ════════════════════════════════════════════════════════════
# 附录：常用系统诊断查询
# ════════════════════════════════════════════════════════════
def chapter_appendix():
    """系统诊断：当前查询、慢查询、表引擎"""
    print("1) 当前正在执行的查询:")
    print("""示例:
    client.execute('''
        SELECT query_id, query, elapsed, read_rows, memory_usage
        FROM system.processes
        WHERE database = 'goin_new'
    ''')
    """)

    print("\n2) 慢查询 TOP 20:")
    print("""示例:
    client.execute('''
        SELECT query, duration_ms, read_rows, result_rows,
               query_kind, databases, tables
        FROM system.query_log
        WHERE database = 'goin_new'
          AND type = 'QueryFinish'
          AND duration_ms > 1000
        ORDER BY duration_ms DESC
        LIMIT 20
    ''')
    """)

    print("\n3) 查看各表引擎:")
    print("""示例:
    client.execute('''
        SELECT name, engine, engine_full
        FROM system.tables
        WHERE database = 'goin_new'
    ''')
    """)


# ════════════════════════════════════════════════════════════
# 交互菜单
# ════════════════════════════════════════════════════════════
def menu():
    """启动交互菜单，选择要运行的章节"""
    chapters = [
        ("00", "连接测试", chapter_00),
        ("01", "基础查询 — SELECT / WHERE / LIMIT", chapter_01),
        ("02", "聚合查询 — GROUP BY / HAVING", chapter_02),
        ("03", "日期与时间处理", chapter_03),
        ("04", "条件与过滤进阶", chapter_04),
        ("05", "多表 JOIN", chapter_05),
        ("06", "子查询与 CTE", chapter_06),
        ("07", "窗口函数", chapter_07),
        ("08", "数据写入", chapter_08),
        ("09", "元数据与表操作", chapter_09),
        ("10", "实用技巧", chapter_10),
        ("A",  "附录：系统诊断查询", chapter_appendix),
    ]

    print("=" * 60)
    print("  ClickHouse 入门教程 — 请选择要运行的章节")
    print("=" * 60)
    for num, title, _ in chapters:
        print(f"  [{num}] {title}")
    print("  [q] 退出")
    print("=" * 60)

    while True:
        choice = input("\n请输入章节编号: ").strip()
        if choice.lower() == 'q':
            print("退出。")
            break
        for num, title, func in chapters:
            if choice == num:
                print(f"\n--- 第{num}章：{title} ---\n")
                func()
                print(f"\n--- 第{num}章结束 ---")
                break
        else:
            print("无效输入，请重新选择。")


if __name__ == '__main__':
    menu()
else:
    print("ClickHouse 教程已加载，可用以下命令运行：")
    print("  chapter_00()  连接测试")
    print("  chapter_01()  基础查询")
    print("  chapter_02()  聚合查询")
    print("  ...")
    print("  chapter_10()  实用技巧")
    print("  chapter_appendix()  附录")
    print("  menu()        交互菜单")
