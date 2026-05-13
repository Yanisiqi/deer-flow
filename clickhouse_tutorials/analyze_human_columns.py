"""
分析 entity_share_data 中 type='human' 的所有非空字段分布。

输出内容：
  1. type='human' 的总行数
  2. 按填充率排序的列列表（有数据的列在前，完全为空的列在后）
  3. 完全为空的列名清单

运行:
  cd deer-flow && python clickhouse_tutorials/analyze_human_columns.py
"""

from clickhouse_driver import Client

CLICKHOUSE = {
    "host": "10.208.57.5",
    "port": 59000,
    "user": "default",
    "password": "",
    "database": "goin_new",
    "secure": False,
}

client = Client(**CLICKHOUSE)


def get_human_count() -> int:
    """获取 type='human' 的总行数。"""
    rows = client.execute(
        "SELECT count() FROM entity_share_data WHERE type = 'human'"
    )
    return rows[0][0]


def get_all_columns() -> list[tuple[str, str]]:
    """获取 entity_share_data 的所有列名和类型。"""
    rows = client.execute(
        """
        SELECT name, type
        FROM system.columns
        WHERE database = 'goin_new' AND table = 'entity_share_data'
        ORDER BY position
        """
    )
    return [(name, typ) for name, typ in rows]


def build_countif_condition(col: str, typ: str) -> str:
    """根据列类型构造 countIf 条件。

    注意：ClickHouse 22.6.1.1 中，部分 Array 列实际存储为空字符串 '' 而非 []，
    直接比较 != '' 会导致 "Array does not start with '['" 错误。
    """
    upper = typ.upper()

    # 数组类型：先检查！因为 Array(String) 也包含 "STRING"。
    # 使用 length() > 0 避免空字符串 '' 与 Array 类型比较引发错误。
    if "ARRAY" in upper:
        return f"countIf({col} IS NOT NULL AND length({col}) > 0)"

    # 字符串类型：非 NULL 且非空字符串
    if "STRING" in upper:
        return f"countIf({col} IS NOT NULL AND {col} != '')"

    # 数值 / 日期 / 其他：只要非 NULL 就算有数据（0 是合法值）
    return f"countIf({col} IS NOT NULL)"


def _run_batched_queries(columns: list[tuple[str, str]], total: int, batch_size: int = 50):
    """分批查询，每批 batch_size 列，避免单条 SQL 编译时内部错误。

    在 ClickHouse 22.6.1.1 中，346 个 countIf 放在一条 SQL 里会触发
    查询编译器 bug。分成多批即可绕过。
    """
    results: list[int] = [0] * len(columns)

    for batch_start in range(0, len(columns), batch_size):
        batch = columns[batch_start : batch_start + batch_size]
        parts = []
        for local_idx, (col_name, col_type) in enumerate(batch):
            cond = build_countif_condition(col_name, col_type)
            parts.append(f"    {cond} AS _r{local_idx}")

        sql = (
            "SELECT\n"
            + ",\n".join(parts)
            + "\nFROM entity_share_data\nWHERE type = 'human'"
        )

        global_idx = batch_start
        row = client.execute(sql)[0]
        for val in row:
            non_null = val if val is not None else 0
            results[global_idx] = non_null
            global_idx += 1

        print(f"  批次 {batch_start // batch_size + 1}: "
              f"列 {batch_start + 1}–{batch_start + len(batch)} "
              f"({len(batch)} 列) ✓")

    return results


def analyze():
    print("=" * 60)
    print("entity_share_data — type='human' 字段填充分析")
    print("=" * 60)

    # Step 1: count
    total = get_human_count()
    print(f"\ntype='human' 总行数: {total:,}\n")

    if total == 0:
        print("没有 type='human' 的记录，退出。")
        return

    # Step 2: 获取所有列
    columns = get_all_columns()
    print(f"总列数: {len(columns)}")
    print(f"分批执行查询（每批 50 列）...\n")

    # Step 3: 分批执行查询
    row = _run_batched_queries(columns, total, batch_size=50)

    # Step 4: 整理结果 — (列名, 填充率, 非空数)
    filled: list[tuple[str, float, int]] = []
    empty_cols: list[str] = []

    for idx, (col_name, _) in enumerate(columns):
        non_null = row[idx]
        ratio = non_null / total * 100
        if non_null > 0:
            filled.append((col_name, ratio, non_null))
        else:
            empty_cols.append(col_name)

    # 按填充率降序排列
    filled.sort(key=lambda x: -x[1])

    # Step 5: 输出
    print(f"\n--- 有数据的列（{len(filled)} 列，按填充率降序）---\n")
    print(f"  {'填充率':>8s}  {'非空数':>10s}  列名")
    print(f"  {'-'*8}  {'-'*10}  {'-'*40}")
    for col_name, ratio, non_null in filled:
        print(f"  {ratio:>7.1f}%  {non_null:>10,}  {col_name}")

    if empty_cols:
        print(f"\n--- 完全为空的列（共 {len(empty_cols)} 列）---\n")
        for col_name in empty_cols:
            print(f"  {col_name}")


if __name__ == "__main__":
    analyze()
