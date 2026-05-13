"""
Local Database Tools — ClickHouse Knowledge Base

Provides two tools for querying the entity_share_data table:
  - get_table_schema: fetch column metadata (name, type, comment)
  - execute_sql: run read-only SELECT queries with safety constraints

Connection parameters are read from config.yaml's "clickhouse" section.
"""

import logging
import re

from clickhouse_driver import Client
from clickhouse_driver.errors import NetworkError
from langchain.tools import tool

from deerflow.config import get_app_config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Read-only SQL validation
# ---------------------------------------------------------------------------

# Statements that are NEVER allowed
_DENIED_KEYWORDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "OPTIMIZE",
    "RENAME",
    "ATTACH",
    "DETACH",
    "SYSTEM",
    "KILL",
    "SET",
)

# Allowed statement-starting keywords
_ALLOWED_PREFIXES = ("SELECT", "WITH", "DESCRIBE", "EXPLAIN")


def _validate_read_only(sql: str) -> str | None:
    """Check that *sql* is a read-only query.

    Returns ``None`` when the query is allowed, or an error message string
    when it is rejected.
    """
    stripped = sql.strip()
    if not stripped:
        return "Empty SQL statement."

    # Normalise to upper case for keyword matching
    upper = stripped.upper()

    # Reject denied keywords at the start of a statement.
    for keyword in _DENIED_KEYWORDS:
        # Match keyword at the start or after a semicolon / whitespace boundary.
        pattern = rf"(?:^|;\s*){keyword}\b"
        if re.search(pattern, upper):
            return f"Only read-only queries are allowed. Statement starting with '{keyword}' was rejected."

    # Allow explicit prefixes
    for prefix in _ALLOWED_PREFIXES:
        if upper.startswith(prefix):
            return None

    return f"Query must start with one of: {', '.join(_ALLOWED_PREFIXES)}. Got: {stripped[:60]}"


# ---------------------------------------------------------------------------
# ClickHouse client — module-level singleton with auto-reconnect
# ---------------------------------------------------------------------------

_client: Client | None = None


def _get_client() -> Client:
    """Return a ClickHouse client, reconnecting on failure."""
    global _client
    try:
        if _client is not None:
            # Ping to verify the connection is alive
            _client.execute("SELECT 1")
            return _client
    except NetworkError:
        logger.warning("ClickHouse connection lost, reconnecting...")
        _client = None

    config = get_app_config()
    ch_config = getattr(config, "clickhouse", None)
    if ch_config is None:
        raise RuntimeError("Missing 'clickhouse' section in config.yaml. Please add:\n\nclickhouse:\n  host: <host>\n  port: <port>\n  user: <user>\n  password: <password>\n  database: <database>\n  secure: false\n")

    host = ch_config.get("host", "127.0.0.1")
    port = ch_config.get("port", 9000)
    user = ch_config.get("user", "default")
    password = ch_config.get("password", "")
    database = ch_config.get("database", "default")
    secure = ch_config.get("secure", False)

    _client = Client(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        secure=secure,
        settings={
            "max_execution_time": 30,
            "max_result_bytes": 100_000_000,
            "max_rows_to_read": 1_000_000_000,
        },
    )
    return _client


# ---------------------------------------------------------------------------
# Result formatting helpers
# ---------------------------------------------------------------------------


def _format_schema(rows: list[tuple]) -> str:
    """Format column metadata into a readable table."""
    if not rows:
        return "(no columns found)"

    lines = [f"表: {rows[0][0] if len(rows[0]) > 0 else '?'}  (共 {len(rows)} 列)"]
    for name, typ, comment in rows:
        comment_str = f"  {comment}" if comment else ""
        lines.append(f"  {name:30s} {typ:30s}{comment_str}")
    return "\n".join(lines)


def _format_rows(rows: list[tuple], columns: list[str], max_col_width: int = 80) -> str:
    """Format rows showing only non-default values.

    Args:
        max_col_width: Truncate column values longer than this.
                       Set to 0 to disable truncation entirely.
    """
    if not rows:
        return "(空结果)"

    output_parts: list[str] = [f"共 {len(rows)} 行\n"]
    for row_idx, row in enumerate(rows):
        output_parts.append(f"--- 行 {row_idx + 1} ---")
        has_any = False
        for i, val in enumerate(row):
            col_name = columns[i] if i < len(columns) else f"col_{i}"
            if val is None:
                continue
            if isinstance(val, (list, tuple)) and len(val) == 0:
                continue
            if isinstance(val, str) and val == "":
                continue
            val_str = str(val)
            if max_col_width and len(val_str) > max_col_width:
                val_str = val_str[:max_col_width] + "..."
            output_parts.append(f"  {col_name} = {val_str}")
            has_any = True
        if not has_any:
            output_parts.append("  (所有列均为空/默认值)")
        output_parts.append("")
    return "\n".join(output_parts)


# ---------------------------------------------------------------------------
# Tool 1: get_table_schema
# ---------------------------------------------------------------------------


@tool("get_table_schema", parse_docstring=True)
def get_table_schema_tool(
    table_name: str = "entity_share_data",
) -> str:
    """Get the column schema (name, type, comment) for a table in the goin_new database.

    Use this tool FIRST when you are unsure about the table structure.
    Always check column names and types before writing SQL queries.

    Args:
        table_name: Name of the table to inspect. Default is "entity_share_data".
    """
    try:
        client = _get_client()
        rows = client.execute(
            """
            SELECT name, type, comment
            FROM system.columns
            WHERE database = 'goin_new' AND table = %(table)s
            ORDER BY position
            """,
            {"table": table_name},
        )
        return _format_schema(rows)
    except Exception as e:
        logger.exception("Failed to get table schema for '%s'", table_name)
        return f"Error fetching schema for '{table_name}': {e}"


# ---------------------------------------------------------------------------
# Tool 2: execute_sql
# ---------------------------------------------------------------------------


@tool("execute_sql", parse_docstring=True)
def execute_sql_tool(
    sql: str,
    max_col_width: int = 80,
) -> str:
    """Execute a read-only SQL query against the entity_share_data table and return formatted results.

    Only SELECT, WITH, DESCRIBE, and EXPLAIN statements are allowed.
    INSERT, UPDATE, DELETE, DROP, and other modification statements are rejected.

    Args:
        sql: The SQL query string to execute (read-only).
        max_col_width: Maximum characters per column value before truncation.
                       Default 80. Set to 0 to disable truncation.
    """
    # --- Read-only validation (code-level enforcement) ---
    rejection = _validate_read_only(sql)
    if rejection:
        return f"[SECURITY] {rejection}"

    # --- Execute ---
    try:
        client = _get_client()
        rows, columns_with_types = client.execute(sql, with_column_types=True)
    except Exception as e:
        logger.exception("SQL execution failed")
        return f"Query error: {e}"

    column_names = [col[0] for col in columns_with_types]

    # --- Format results (compact, filters empty/default columns) ---
    return _format_rows(rows, column_names, max_col_width=max_col_width)
