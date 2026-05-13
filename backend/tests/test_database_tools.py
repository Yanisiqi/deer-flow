"""Tests for the ClickHouse database tools (formatting + read-only validation).

These tests cover the pure-function helpers that do not require a live
ClickHouse connection:

  - ``_validate_read_only`` — SQL security validation
  - ``_format_schema``     — column metadata table formatting
  - ``_format_rows``       — compact row formatting with truncation

The tool functions (``get_table_schema_tool``, ``execute_sql_tool``) have
integration tests at the bottom of this file that require a live ClickHouse
server.  They are skipped by default; run explicitly with:

    pytest tests/test_database_tools.py::test_schema_output -v -s --no-header
    pytest tests/test_database_tools.py::test_query_output   -v -s --no-header
"""

from __future__ import annotations

from pathlib import Path

import pytest

from deerflow.tools.database.tools import (
    _format_rows,
    _format_schema,
    _validate_read_only,
)

# ===========================================================================
# _validate_read_only
# ===========================================================================


class TestValidateReadOnly:
    """SQL read-only validation."""

    def test_allows_select(self):
        assert _validate_read_only("SELECT 1") is None

    def test_allows_with(self):
        assert _validate_read_only("WITH x AS (SELECT 1) SELECT * FROM x") is None

    def test_allows_describe(self):
        assert _validate_read_only("DESCRIBE TABLE entity_share_data") is None

    def test_allows_explain(self):
        assert _validate_read_only("EXPLAIN PLAN SELECT 1") is None

    def test_rejects_drop(self):
        err = _validate_read_only("DROP TABLE entity_share_data")
        assert err is not None
        assert "DROP" in err

    def test_rejects_insert(self):
        err = _validate_read_only("INSERT INTO t VALUES (1)")
        assert err is not None
        assert "INSERT" in err

    def test_rejects_delete(self):
        err = _validate_read_only("DELETE FROM t WHERE 1=1")
        assert err is not None
        assert "DELETE" in err

    def test_rejects_alter(self):
        err = _validate_read_only("ALTER TABLE t ADD COLUMN x Int64")
        assert err is not None

    def test_rejects_create(self):
        err = _validate_read_only("CREATE TABLE t (x Int64)")
        assert err is not None

    def test_rejects_truncate(self):
        assert _validate_read_only("TRUNCATE TABLE t") is not None

    def test_rejects_update(self):
        assert _validate_read_only("UPDATE t SET x=1") is not None

    def test_rejects_optimize(self):
        assert _validate_read_only("OPTIMIZE TABLE t") is not None

    def test_rejects_rename(self):
        assert _validate_read_only("RENAME TABLE a TO b") is not None

    def test_rejects_attach(self):
        assert _validate_read_only("ATTACH TABLE t") is not None

    def test_rejects_detach(self):
        assert _validate_read_only("DETACH TABLE t") is not None

    def test_rejects_system(self):
        assert _validate_read_only("SYSTEM DROP DNS CACHE") is not None

    def test_rejects_kill(self):
        assert _validate_read_only("KILL QUERY WHERE 1") is not None

    def test_rejects_set(self):
        assert _validate_read_only("SET max_threads = 1") is not None

    # --- Boundary: keywords inside string values (should be ALLOWED) ---

    def test_drop_in_string_value(self):
        """'DROP' inside a string literal is not a real DROP statement."""
        sql = "SELECT name FROM t WHERE name = 'drop table test'"
        assert _validate_read_only(sql) is None

    def test_insert_in_string_value(self):
        sql = "SELECT * FROM t WHERE type = 'insert into test'"
        assert _validate_read_only(sql) is None

    def test_delete_in_like(self):
        sql = "SELECT * FROM t WHERE name LIKE '%DELETE%'"
        assert _validate_read_only(sql) is None

    # --- Boundary: semicolon-injected multi-statement ---

    def test_semicolon_drop(self):
        sql = "SELECT 1; DROP TABLE entity_share_data"
        assert _validate_read_only(sql) is not None

    def test_semicolon_delete(self):
        sql = "SELECT 1; DELETE FROM entity_share_data WHERE 1=1"
        assert _validate_read_only(sql) is not None

    # --- Boundary: keyword as column name (should be ALLOWED) ---

    def test_drop_as_column_name_mysql_quoting(self):
        sql = 'SELECT * FROM t WHERE "drop" = 1'
        assert _validate_read_only(sql) is None

    def test_drop_as_column_name_backtick(self):
        sql = "SELECT `drop` FROM t"
        assert _validate_read_only(sql) is None

    # --- Boundary: word-boundary differentiation ---

    def test_dropped_in_value(self):
        """DROPPED contains DROP but \\b boundary prevents false positive."""
        sql = "SELECT * FROM t WHERE name = 'DROPPED'"
        assert _validate_read_only(sql) is None

    def test_created_in_value(self):
        sql = "SELECT * FROM t WHERE name = 'CREATED'"
        assert _validate_read_only(sql) is None

    # --- Edge cases ---

    def test_empty_string(self):
        err = _validate_read_only("")
        assert err is not None
        assert "Empty" in err

    def test_whitespace_only(self):
        err = _validate_read_only("   ")
        assert err is not None

    def test_unknown_statement(self):
        err = _validate_read_only("FOOBAR 1")
        assert err is not None
        assert "SELECT" in err

    def test_case_insensitivity(self):
        assert _validate_read_only("select * from t") is None
        assert _validate_read_only("SELECT * FROM t") is None
        assert _validate_read_only("  select 1  ") is None
        assert _validate_read_only("drop table t") is not None
        assert _validate_read_only("DROP TABLE t") is not None


# ===========================================================================
# _format_schema
# ===========================================================================


class TestFormatSchema:
    """Schema formatting (column metadata table)."""

    def test_empty(self):
        assert _format_schema([]) == "(no columns found)"

    def test_single_column(self):
        rows = [("name", "String", "实体名称")]
        result = _format_schema(rows)
        assert "name" in result
        assert "String" in result
        assert "实体名称" in result
        assert "共 1 列" in result

    def test_multiple_columns(self):
        rows = [
            ("name", "String", "实体名称"),
            ("age", "Int64", "年龄"),
            ("type", "String", ""),
        ]
        result = _format_schema(rows)
        assert "共 3 列" in result
        assert "实体名称" in result
        assert "年龄" in result
        # Column without comment should not show extra spaces
        assert "String" in result

    def test_no_comment(self):
        """Column with empty comment should not show trailing blank."""
        rows = [("mongo_id", "String", "")]
        result = _format_schema(rows)
        assert "mongo_id" in result
        assert "String" in result

    def test_table_name_from_first_row(self):
        rows = [("col1", "Int64", "")]
        result = _format_schema(rows)
        assert "表:" in result


# ===========================================================================
# _format_rows
# ===========================================================================


class TestFormatRows:
    """Compact row formatting with empty/default filtering."""

    # --- Empty result ---

    def test_empty_rows(self):
        assert _format_rows([], ["a", "b"]) == "(空结果)"

    # --- NULL / empty filtering ---

    def test_skips_null(self):
        rows = [(None,)]
        result = _format_rows(rows, ["col1"])
        assert "所有列均为空/默认值" in result

    def test_skips_empty_string(self):
        rows = [("",)]
        result = _format_rows(rows, ["col1"])
        assert "所有列均为空/默认值" in result

    def test_skips_empty_array(self):
        rows = [([],)]
        result = _format_rows(rows, ["col1"])
        assert "所有列均为空/默认值" in result

    def test_keeps_zero(self):
        """0 is a valid value and must NOT be filtered."""
        rows = [(0,)]
        result = _format_rows(rows, ["age"])
        assert "age" in result
        assert "0" in result

    def test_keeps_non_empty_string(self):
        rows = [("特朗普",)]
        result = _format_rows(rows, ["name"])
        assert "特朗普" in result

    def test_keeps_non_empty_array(self):
        rows = [(["politician", "businessman"],)]
        result = _format_rows(rows, ["occupation"])
        assert "politician" in result

    def test_mixed_row(self):
        """Row with some null and some non-null columns."""
        rows = [("特朗普", None, "male", "")]
        result = _format_rows(rows, ["name", "age", "sex_or_gender", "email"])
        assert "特朗普" in result
        assert "male" in result
        assert "age" not in result  # None — skipped
        assert "email" not in result  # empty str — skipped

    # --- Truncation ---

    def test_truncates_long_value_default(self):
        long_str = "a" * 200
        rows = [(long_str,)]
        result = _format_rows(rows, ["text"], max_col_width=80)
        assert len(result) < 200  # truncation happened
        assert "..." in result

    def test_max_col_width_zero_disables_truncation(self):
        long_str = "a" * 200
        rows = [(long_str,)]
        result = _format_rows(rows, ["text"], max_col_width=0)
        assert "a" * 200 in result  # full value preserved

    def test_custom_max_col_width(self):
        long_str = "x" * 50
        rows = [(long_str,)]
        result = _format_rows(rows, ["col"], max_col_width=20)
        assert "..." in result
        assert "x" * 20 in result
        assert "x" * 50 not in result  # truncated

    # --- Multiple rows ---

    def test_multiple_rows(self):
        rows = [("Alice", 30), ("Bob", 25)]
        result = _format_rows(rows, ["name", "age"])
        assert "行 1" in result
        assert "行 2" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_row_count_displayed(self):
        rows = [("a",), ("b",), ("c",)]
        result = _format_rows(rows, ["col"])
        assert "共 3 行" in result


# ===========================================================================
# Integration tests (require live ClickHouse)
# ===========================================================================

_skip_live = pytest.mark.skipif(
    not Path(__file__).resolve().parents[2].joinpath("config.yaml").exists(),
    reason="No config.yaml — live ClickHouse tests require a running server",
)


@_skip_live
def test_schema_output():
    """Print the schema output for entity_share_data."""
    from deerflow.tools.database.tools import get_table_schema_tool

    result = get_table_schema_tool.invoke({"table_name": "entity_share_data"})
    print()
    print("=" * 60)
    print("get_table_schema_tool('entity_share_data') 输出")
    print("=" * 60)
    print(result)
    print("=" * 60)
    # Basic sanity checks
    assert "mongo_id" in result
    assert "name" in result
    assert "occupation" in result
    # Should show some columns (at least 10)
    assert result.count("\n") > 10


@_skip_live
def test_query_output():
    """Print the query result output (compact format)."""
    from deerflow.tools.database.tools import execute_sql_tool

    # 1) Simple query, default truncation
    result = execute_sql_tool.invoke(
        {
            "sql": "SELECT name, type, occupation FROM entity_share_data WHERE type = 'human' AND name LIKE '%Trump%' LIMIT 5",
        }
    )
    print()
    print("=" * 60)
    print("execute_sql_tool — 默认 max_col_width=80")
    print("=" * 60)
    print(result)
    print("=" * 60)
    assert "Trump" in result

    # 2) Query with max_col_width=0 (no truncation)
    result_full = execute_sql_tool.invoke(
        {
            "sql": "SELECT name, text FROM entity_share_data WHERE type = 'human' AND text != '' AND name LIKE '%Trump%' LIMIT 1",
            "max_col_width": 0,
        }
    )
    print()
    print("=" * 60)
    print("execute_sql_tool — max_col_width=0 (不截断)")
    print("=" * 60)
    print(result_full)
    print("=" * 60)
    assert "text" in result_full

    # 3) Empty result
    result_empty = execute_sql_tool.invoke(
        {
            "sql": "SELECT name FROM entity_share_data WHERE name = '这个不存在'",
        }
    )
    print()
    print("=" * 60)
    print("execute_sql_tool — 空结果")
    print("=" * 60)
    print(result_empty)
    print("=" * 60)
    assert "空结果" in result_empty
