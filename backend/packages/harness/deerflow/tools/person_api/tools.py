"""
Person API Tools — 人物信息查询

5 个工具，通过后端 REST API 查询人物各类信息。

后端基础 URL 从 config.yaml 的 ``person_api.base_url`` 读取。
"""

import logging
from datetime import UTC, datetime

import httpx
from langchain.tools import tool

from deerflow.config import get_app_config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def _get_base_url() -> str:
    """Get person API base URL from config.yaml person_api section."""
    config = get_app_config()
    api_cfg = getattr(config, "person_api", None) or {}
    return api_cfg.get("base_url", "http://10.60.1.101:5013/goin_new")


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _get(path: str, **params) -> dict:
    """GET request, filters out empty/None params."""
    params = {k: v for k, v in params.items() if v not in (None, "", "")}
    base_url = _get_base_url()
    with httpx.Client(base_url=base_url, timeout=30) as client:
        resp = client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()


def _post(path: str, **body) -> dict:
    """POST request, filters out empty/None params.

    Note: the social-media APIs expect a ``type`` field ("facebook"/"twitter").
    Python reserved-word collision is handled by the caller — *body* is passed
    as keyword-args so it will be passed through without issue.
    """
    body = {k: v for k, v in body.items() if v not in (None, "", "")}
    base_url = _get_base_url()
    with httpx.Client(base_url=base_url, timeout=30) as client:
        resp = client.post(path, json=body)
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _trunc(val, max_width: int = 200) -> str:
    """Truncate text to *max_width* chars.  0 / None = no limit."""
    if val is None:
        return ""
    s = str(val)
    if max_width and len(s) > max_width:
        return s[:max_width] + "..."
    return s


def _fmt_val(key: str, val, max_width: int = 200) -> str | None:
    """Format a single key → value line.  Returns None when the value is empty."""
    if val is None:
        return None
    if isinstance(val, (list, tuple)) and len(val) == 0:
        return None
    if isinstance(val, str) and val.strip() == "":
        return None
    # int timestamps → datetime string
    if key in ("create_time", "update_time") and isinstance(val, (int, float)) and val > 10**8:
        try:
            val = datetime.fromtimestamp(val, tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
        except (OSError, ValueError):
            pass
    return f"  {key}: {_trunc(val, max_width)}"


def _fmt_compact_list(data: list, max_items: int = 10, max_width: int = 200) -> str:
    """Format a list of dicts as readable text blocks.

    Only non-empty fields are shown.  A pagination footer is NOT included here
    so the caller can append it afterwards.
    """
    if not data:
        return "(空结果)"
    lines: list[str] = [f"共 {len(data)} 条记录"]
    for i, item in enumerate(data[:max_items]):
        if not isinstance(item, dict):
            lines.append(f"\n--- [{i + 1}] ---\n  {_trunc(str(item), max_width)}")
            continue
        lines.append(f"\n--- [{i + 1}] ---")
        shown = 0
        for k, v in item.items():
            line = _fmt_val(k, v, max_width)
            if line:
                lines.append(line)
                shown += 1
        if shown == 0:
            lines.append("  (无有效数据)")
    if len(data) > max_items:
        lines.append(f"\n... 还有 {len(data) - max_items} 条记录（可通过 page/size 参数翻页）")
    return "\n".join(lines)


def _fmt_pagination(pagination: dict | None) -> str:
    """Brief pagination summary."""
    if not pagination:
        return ""
    parts = []
    if "page" in pagination:
        parts.append(f"第 {pagination['page']} 页")
    if "size" in pagination:
        parts.append(f"每页 {pagination['size']} 条")
    if "total" in pagination:
        parts.append(f"共 {pagination['total']} 条")
    return f"  ({', '.join(parts)})" if parts else ""


def _fmt_single(data: dict, max_width: int = 200) -> str:
    """Format a single dict item with attribute-like fields."""
    lines: list[str] = []
    for k, v in data.items():
        line = _fmt_val(k, v, max_width)
        if line:
            lines.append(line)
    return "\n".join(lines) if lines else "(无数据)"


def _end_time_default(end_time: str) -> str:
    """Return today's date when *end_time* is empty."""
    return end_time if end_time else datetime.now().strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Tool 1 — 搜索人物实体
# ---------------------------------------------------------------------------


@tool("search_person_entity", parse_docstring=True)
def search_person_entity_tool(
    name: str,
    page: int = 1,
    size: int = 10,
) -> str:
    """根据人物姓名搜索数据库，返回匹配的人物 ID (mongo_id/pid) 及基本信息。

    这是查询人物的**入口工具**。先调用此工具获取 entity_id，再传给其他工具查询详细信息。

    后端翻页逻辑: 按 subject_count（提及次数）降序排列，使用 SQL
    ``LIMIT size OFFSET (page-1) * size`` 翻页，不返回总条数。
    size 越大，命中间名/歧义名的候选越多；page 用于翻查更靠后的结果。

    Args:
        name: 人物姓名关键词（支持模糊匹配）。
        page: 页码，从 1 开始，默认 1。
        size: 每页返回条数，默认 10。
    """
    body = {"entity_type": "person", "key_word": name, "page": page, "size": size}
    try:
        result = _post("/entity_index/entity_list", **body)
    except Exception as e:
        logger.exception("search_person_entity failed for '%s'", name)
        return f"搜索失败: {e}"

    data = result.get("data", [])
    if not data:
        return f"未找到名为「{name}」的人物。"

    lines: list[str] = []
    for i, item in enumerate(data, 1):
        lines.append(f"--- [{i}] ---")
        lines.append(f"  名称: {item.get('name', '')}")
        lines.append(f"  entity_id: {item.get('id', '')}")
        abstract = item.get("abstract", "")
        if abstract:
            lines.append(f"  摘要: {_trunc(abstract)}")
        gender = item.get("gender", "")
        if gender:
            lines.append(f"  性别: {gender}")
        birth = item.get("birth", "")
        if birth:
            lines.append(f"  出生: {birth}")
        occupation = item.get("occupation", "")
        if occupation:
            lines.append(f"  职业: {_trunc(occupation)}")
        text = item.get("text", "")
        if text:
            lines.append(f"  描述: {_trunc(text)}")
        labels = item.get("labels", [])
        if labels:
            lines.append(f"  标签: {', '.join(labels[:5])}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 2 — 人物基本属性
# ---------------------------------------------------------------------------


@tool("get_person_profile", parse_docstring=True)
def get_person_profile_tool(entity_id: str, max_width: int = 200) -> str:
    """获取人物的基本属性信息，包括名称、性别、国籍、出生日期、职业、教育经历、政党等。

    Args:
        entity_id: 人物 ID（由 search_person_entity 返回）。
        max_width: 字段值最大显示长度，超出截断。0 为不截断。
    """
    try:
        result = _get("/persona/person_attributes", entity_id=entity_id)
    except Exception as e:
        logger.exception("get_person_profile failed for %s", entity_id)
        return f"查询失败: {e}"

    data = result.get("data", {})
    if not data:
        return "未找到该人物的基本信息。"

    lines = [f"=== {data.get('name', '')} ==="]
    abstract = data.get("abstract", "")
    if abstract:
        lines.append(f"摘要: {_trunc(abstract, max_width)}")

    detail = data.get("detail", [])
    for d in detail:
        if d.get("val") is not None:
            cn = d.get("cn", "")
            val = d.get("val", "")
            lines.append(f"  {cn}: {_trunc(val, max_width)}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 3 — 查询各类关联内容（通用分发）
# ---------------------------------------------------------------------------


@tool("query_person_content", parse_docstring=True)
def query_person_content_tool(
    entity_id: str,
    content_type: str,
    start_time: str = "1970-01-01",
    end_time: str = "",
    key_word: str = "",
    page: int = 1,
    size: int = 10,
    labels: str = "",
    sentiment: str = "",
    topic: str = "",
    media: str = "",
    social_type: str = "",
    max_width: int = 200,
) -> str:
    """查询人物的各类关联内容，包括事件、活动、言论、新闻、社交媒体等。

    可选 content_type 值：events（相关事件）、activities（主要活动，支持 labels 过滤）、
    statements（重点言论，支持 sentiment 过滤）、news（新闻报道，支持 topic/media 过滤）、
    social_discussion（社媒讨论，别人讨论该人物）、person_social（个人社媒，自己发的帖子）。

    Args:
        entity_id: 人物 ID（由 search_person_entity 返回）。
        content_type: 查询类型。events=相关事件, activities=主要活动, statements=重点言论, news=新闻报道, social_discussion=社媒讨论, person_social=个人社媒。
        start_time: 起始日期 (YYYY-MM-DD)，默认 "1970-01-01"。
        end_time: 截止日期 (YYYY-MM-DD)，默认为今天。
        key_word: 关键词过滤（匹配标题/内容）。
        page: 页码，从 1 开始。
        size: 每页条数，默认 10。
        labels: activities 专用，活动类型过滤，多个用逗号分隔，如 "politics,military"。
        sentiment: statements/news 专用，情感极性过滤：1=正面，0=中性，-1=负面。
        topic: news 专用，新闻话题过滤。
        media: news 专用，新闻来源过滤。
        social_type: social_discussion/person_social 专用，平台："facebook" 或 "twitter"。
        max_width: 字段值最大显示长度，超出截断。0 为不截断。
    """

    end_time = _end_time_default(end_time)
    fmt_kw = dict(max_width=max_width)

    # Dispatch to the correct API
    try:
        if content_type == "events":
            result = _post("/persona/person_event", entity_id=entity_id, page=page, size=size)

        elif content_type == "activities":
            label_list = [x.strip() for x in labels.split(",") if x.strip()] if labels else None
            result = _post(
                "/persona/person_activity",
                entity_id=entity_id,
                start_time=start_time,
                end_time=end_time,
                key_word=key_word,
                labels=label_list,
                page=page,
                size=size,
            )

        elif content_type == "statements":
            result = _post(
                "/persona/person_statements",
                entity_id=entity_id,
                start_time=start_time,
                end_time=end_time,
                key_word=key_word,
                sentiment=sentiment,
                page=page,
                size=size,
            )

        elif content_type == "news":
            result = _get(
                "/persona/person_news",
                entity_id=entity_id,
                start_time=start_time,
                end_time=end_time,
                key_word=key_word,
                sentiment=sentiment,
                topic=topic,
                media=media,
                page=page,
                size=size,
            )

        elif content_type == "social_discussion":
            if not social_type:
                return "查询社媒讨论需要指定 social_type (facebook/twitter)。"
            result = _get(
                "/persona/social_media_discussion",
                entity_id=entity_id,
                type=social_type,
                start_time=start_time,
                end_time=end_time,
                key_word=key_word,
                page=page,
                size=size,
            )

        elif content_type == "person_social":
            if not social_type:
                return "查询个人社媒需要指定 social_type (facebook/twitter)。"
            result = _get(
                "/persona/person_social_media",
                entity_id=entity_id,
                type=social_type,
                start_time=start_time,
                end_time=end_time,
                key_word=key_word,
                page=page,
                size=size,
            )

        else:
            return f"未知 content_type: {content_type}。可用值: events, activities, statements, news, social_discussion, person_social"

    except Exception as e:
        logger.exception("query_person_content(%s) failed for %s", content_type, entity_id)
        return f"查询失败: {e}"

    data = result.get("data", [])
    pagination = result.get("pagination") or result.get("page")

    formatted = _fmt_compact_list(data if isinstance(data, list) else [], **fmt_kw)
    if pagination:
        formatted += "\n" + _fmt_pagination(pagination)
    return formatted


# ---------------------------------------------------------------------------
# Tool 4 — 认知属性分析
# ---------------------------------------------------------------------------


@tool("get_person_cognitive_analysis", parse_docstring=True)
def get_person_cognitive_analysis_tool(
    entity_id: str,
    start_time: str = "1970-01-01",
    end_time: str = "",
    key_word: str = "",
    update: bool = False,
    max_width: int = 200,
) -> str:
    """对人物进行多维度认知分析（AI 生成），包括政治立场、性格特质、政策主张、对华态度等。
    共 6 个维度：1.政治立场 2.性格特质 3.政策主张 4.对华态度 5.影响力评估 6.风险评估。

    注意：首次调用会触发 AI 生成并缓存，后续默认读缓存。传 update=True 可强制重新生成。

    Args:
        entity_id: 人物 ID（由 search_person_entity 返回）。
        start_time: 分析数据的起始日期 (YYYY-MM-DD)。
        end_time: 分析数据的截止日期 (YYYY-MM-DD)，默认为今天。
        key_word: 关键词过滤。
        update: 是否强制重新生成（忽略缓存），默认 False。
        max_width: 字段值最大显示长度，超出截断。0 为不截断。
    """

    end_time = _end_time_default(end_time)
    try:
        result = _post(
            "/persona/cognitive_attributes",
            entity_id=entity_id,
            start_time=start_time,
            end_time=end_time,
            key_word=key_word,
            update=update,
        )
    except Exception as e:
        logger.exception("get_person_cognitive_analysis failed for %s", entity_id)
        return f"认知分析失败: {e}"

    data = result.get("data", {})
    results = data.get("results", [])
    if not results:
        return "暂无认知分析数据。"

    lines = [f"=== 认知属性分析（{len(results)} 个维度）===\n"]
    for r in results:
        title = r.get("title", "")
        lines.append(f"▶ {title}")
        items = r.get("list", [])
        for item in items:
            label = item.get("label", "")
            content = item.get("content", "")
            if label and content:
                lines.append(f"  [{label}] {_trunc(content, max_width)}")
            elif content:
                lines.append(f"  {_trunc(content, max_width)}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 5 — 文档详情
# ---------------------------------------------------------------------------


@tool("get_document_detail", parse_docstring=True)
def get_document_detail_tool(raw_id: str, max_width: int = 200) -> str:
    """根据 raw_doc_id 获取完整的文档/帖子原文内容。

    当用户对某条事件/新闻/社媒内容感兴趣、要求"展开说说"或"查看详情"时调用。

    raw_id 来自 query_person_content 返回结果中的 raw_doc_id 字段。

    Args:
        raw_id: 文档的 raw_doc_id（由 query_person_content 返回）。
        max_width: 字段值最大显示长度，超出截断。0 为不截断。
    """
    try:
        result = _get("/document/document_detial", raw_id=raw_id)
    except Exception as e:
        logger.exception("get_document_detail failed for raw_id=%s", raw_id)
        return f"查询文档详情失败: {e}"

    data = result.get("data", [])
    if not data:
        return "未找到该文档。"

    item = data[0] if isinstance(data, list) else data
    lines = []
    title = item.get("title", "")
    if title:
        lines.append(f"标题: {title}")

    content = item.get("content", "")
    if content:
        lines.append(f"\n正文:\n{_trunc(content, max_width)}")

    url = item.get("url", "")
    if url:
        lines.append(f"\n链接: {url}")

    create_time = item.get("create_time", "")
    if create_time:
        lines.append(f"时间: {create_time}")

    source = item.get("source", "")
    if source:
        lines.append(f"来源: {source}")

    # List entity mentions if any
    entity_list = item.get("entity_list", [])
    if entity_list:
        lines.append("\n提及实体:")
        if isinstance(entity_list, dict):
            for ent_type, entities in entity_list.items():
                if entities:
                    names = [e.get("name", "") for e in (entities if isinstance(entities, list) else [])]
                    lines.append(f"  {ent_type}: {', '.join(filter(None, names[:10]))}")
        elif isinstance(entity_list, list):
            for e in entity_list[:10]:
                name = e.get("name", "") if isinstance(e, dict) else str(e)
                if name:
                    lines.append(f"  - {name}")

    return "\n".join(lines) if lines else "(无内容)"


# ---------------------------------------------------------------------------
# For direct testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pid = search_person_entity_tool(name="特朗普")
    print(pid)
