"""
ClickHouse Read-Only User Creator & Tester

1. Creates a dedicated read-only user for DeerFlow knowledge-base agent
2. Creates a disposable test table (admin) for safe destructive-operation tests
3. Verifies read-only user CAN read from real data
4. Verifies read-only user CANNOT write — tested against the disposable table
5. Cleans up the test table

Usage:
    cd backend
    .venv/Scripts/python.exe ../scripts/create_clickhouse_readonly_user.py

Environment variables (optional):
    CH_HOST, CH_PORT, CH_ADMIN_USER, CH_ADMIN_PASSWORD
    CH_RO_USER, CH_RO_PASSWORD, CH_DATABASE
"""

import os
import sys

from clickhouse_driver import Client
from clickhouse_driver.errors import ServerException

# ---------------------------------------------------------------------------
# Config — read from env or use defaults
# ---------------------------------------------------------------------------
ADMIN_USER = os.getenv("CH_ADMIN_USER", "default")
ADMIN_PASSWORD = os.getenv("CH_ADMIN_PASSWORD", "")
RO_USER = os.getenv("CH_RO_USER", "deerflow_ro")
RO_PASSWORD = os.getenv("CH_RO_PASSWORD", "deerflow_ro_2026")
HOST = os.getenv("CH_HOST", "10.208.57.5")
PORT = int(os.getenv("CH_PORT", "59000"))
DATABASE = os.getenv("CH_DATABASE", "goin_new")

TEST_TABLE = "_test_perm_check"
ok = True


def _admin_client():
    return Client(
        host=HOST,
        port=PORT,
        user=ADMIN_USER,
        password=ADMIN_PASSWORD,
        database=DATABASE,
        secure=False,
    )


def _ro_client():
    return Client(
        host=HOST,
        port=PORT,
        user=RO_USER,
        password=RO_PASSWORD,
        database=DATABASE,
        secure=False,
    )


def step(label: str):
    print(f"\n{'=' * 60}")
    print(f">>> {label}")
    print(f"{'=' * 60}")


def check(label: str, success: bool, detail: str = ""):
    global ok
    status = "✅" if success else "❌"
    print(f"  {status} {label}")
    if detail:
        print(f"     {detail}")
    if not success:
        ok = False


# ===========================================================================
# 1. Create test table (admin)
# ===========================================================================
step("Step 0 — 创建测试表 (admin)")
admin = _admin_client()
admin.execute(f"DROP TABLE IF EXISTS {DATABASE}.{TEST_TABLE}")
admin.execute(
    f"CREATE TABLE {DATABASE}.{TEST_TABLE} (id UInt64, name String) "
    f"ENGINE = MergeTree() ORDER BY id"
)
check(f"测试表 {TEST_TABLE} 已创建", True)

# ===========================================================================
# 2. Create user & grant SELECT only
# ===========================================================================
step("Step 1 — 创建只读用户")
admin.execute(f"CREATE USER IF NOT EXISTS {RO_USER} IDENTIFIED BY '{RO_PASSWORD}'")
check("用户创建/已存在", True)

admin.execute(f"GRANT SELECT ON {DATABASE}.* TO {RO_USER}")
check(f"GRANT SELECT ON {DATABASE}.*", True)

admin.execute(f"GRANT SELECT ON system.columns TO {RO_USER}")
check("GRANT SELECT ON system.columns", True)

admin.disconnect()

# ===========================================================================
# 3. Test: read-only user can SELECT from real data
# ===========================================================================
step("Step 2 — 测试: SELECT 读数据（应该成功）")
ro = _ro_client()

rows = ro.execute(f"SELECT COUNT(*) FROM {DATABASE}.entity_share_data")
count = rows[0][0]
check("SELECT COUNT(*) FROM entity_share_data", True, f"当前行数: {count}")

rows = ro.execute(
    f"SELECT name FROM system.columns "
    f"WHERE database = '{DATABASE}' AND table = 'entity_share_data' LIMIT 3"
)
cols = [r[0] for r in rows]
check("SELECT FROM system.columns (DESCRIBE)", True, f"前 3 列: {cols}")

# ===========================================================================
# 4. Test: write operations against DISPOSABLE test table
#    (all must be denied — the test table is used only because
#    it's safe even if the permission check somehow fails)
# ===========================================================================
step("Step 3 — 测试: 写入操作被拒绝（对测试表操作，绝对安全）")

write_tests = [
    ("INSERT", f"INSERT INTO {DATABASE}.{TEST_TABLE} (id, name) VALUES (1, 'test')"),
    ("DELETE", f"DELETE FROM {DATABASE}.{TEST_TABLE} WHERE id = 1"),
    ("ALTER", f"ALTER TABLE {DATABASE}.{TEST_TABLE} DELETE WHERE id = 1"),
    ("DROP", f"DROP TABLE {DATABASE}.{TEST_TABLE}"),
    ("TRUNCATE", f"TRUNCATE TABLE {DATABASE}.{TEST_TABLE}"),
    ("RENAME", f"RENAME TABLE {DATABASE}.{TEST_TABLE} TO {DATABASE}.{TEST_TABLE}_bak"),
]

for label, sql in write_tests:
    try:
        ro.execute(sql)
        check(label, False, "操作成功了？！不应该！")
    except ServerException as e:
        check(label, True, f"拒绝 (符合预期): {str(e).splitlines()[0][:80]}")

ro.disconnect()

# ===========================================================================
# 5. Cleanup
# ===========================================================================
step("Step 4 — 清理测试表")
admin = _admin_client()
admin.execute(f"DROP TABLE IF EXISTS {DATABASE}.{TEST_TABLE}")
check(f"测试表 {TEST_TABLE} 已删除", True)
admin.disconnect()

# ===========================================================================
# 6. Summary
# ===========================================================================
step("结果汇总")
if ok:
    print(f"\n  所有检查通过。现在可以把 config.yaml 中的 clickhouse 段改为:\n")
    print(f"  clickhouse:")
    print(f"    host: {HOST}")
    print(f"    port: {PORT}")
    print(f"    user: {RO_USER}")
    print(f"    password: {RO_PASSWORD}")
    print(f"    database: {DATABASE}")
    print(f"    secure: false")
else:
    print(f"\n  有检查未通过，请查看上面的 ❌ 信息。")
    sys.exit(1)
