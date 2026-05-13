from clickhouse_driver import Client

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


CLICKHOUSE = {
    'host': '10.208.57.5',
    'port': 59000,
    'user': 'default',
    'password': '',
    'database': 'goin_new',
    'secure': False,
}

client = Client(**CLICKHOUSE)

if __name__ == "__main__":

    # 查询表结构
    table_name = 'entity_share_data'
    # columns = client.execute(f"""
    #     SELECT name, type, comment
    #     FROM system.columns
    #     WHERE database = 'goin_new' AND table = %(table_name)s
    #     ORDER BY position
    # """, {'table_name': table_name})
    # print(f"\ntable 信息 ({len(columns)} 列):")
    # for name, typ, comment in columns:
    #     print(f"  {name:30s} {typ:30s} {comment or ''}")

    # 总行数
    rows = client.execute('''
select count() from relation_share_data
''')
    for row in rows:
        print(row)

    # 查询所有 type
#     rows = client.execute('''
# select distinct type from entity_share_data
# ''')
    
#     rows = client.execute('''
# select type, count() as cnt
# from entity_share_data
# group by type
# order by cnt desc
# ''')
#     for row in rows:
#         print(row)
    
    # 模糊人名查询
#     print("\n模糊人名查询:")
#     rows, columns = client.execute('''
#         SELECT * FROM entity_share_data
#         WHERE name like '%特朗普%'
#         AND type = 'human'
# ''',
#     with_column_types=True
#                           )
#     col_names = [c[0] for c in columns]
#     col_types = [c[1] for c in columns]

    # 打印所有信息
    # for row in rows:    
    #     for name, c_type, val in zip(col_names, col_types, row):
    #         print(f"{name} {c_type}: {val}")
    
    # 只打印有实际值的信息
    # inspect_rows(rows, col_names)