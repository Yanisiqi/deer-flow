"""Entity Knowledge Base Skill — Batch Test Script (Async).

Usage:
    cd backend && uv run python scripts/test_entity_knowledge.py
"""

import asyncio
import logging
import time
import uuid
from pathlib import Path

import pandas as pd
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.runtime import Runtime

from deerflow.agents.lead_agent import make_lead_agent
from deerflow.config.app_config import get_app_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Query definitions ──────────────────────────────────────────────────────

QUERIES = [
    # Geographic entities
    "北京有哪些别名？",
    # "广东省的省会在哪里？",
    # # People
    # "介绍特朗普（Donald Trump）。",
    # # Administrative regions
    # "海淀区属于哪个市？",
    # # Organizations
    # "介绍北京大学。",
    # "介绍清华大学。",
    # # Mixed
    # "介绍马云。",
    # "上海市有多少人口？",
    # "深圳在哪个省？",
]

# ── Output path ────────────────────────────────────────────────────────────
RESULTS_FILE = Path(__file__).resolve().parent.parent / "entity_knowledge_results.xlsx"


async def ask_agent(question: str, thread_id: str) -> str:
    """Send a single question to the lead agent and return the final AI reply.

    .. note::
        **与前端 Gateway 路径的一致性说明**

        相同点：
        - 使用 ``make_lead_agent``（同样的 agent 工厂函数）
        - 使用 ``agent.astream()`` 异步执行（同样的执行方式）
        - 注入 ``__pregel_runtime``（工具所需的运行时上下文，与 worker.py 一致）
        - config 加载路径一致（``get_app_config()`` 读取 ``config.yaml``）

        不同点及原因：

        +----------------------------+---------------------------+-----------------------------------------+
        | 项目                       | 简化版                    | 与前端不同？                             |
        +----------------------------+---------------------------+-----------------------------------------+
        | checkpointer               | ``MemorySaver()``         | 是，前端用 ``config.yaml`` 中配置的      |
        |                            | （内存级，无持久化）      | checkpointer (SQLite/PostgreSQL)。       |
        |                            |                           | 本脚本为单次批量查询，不需要跨轮次       |
        |                            |                           | 恢复对话状态，内存 checkpointer 即可。   |
        +----------------------------+---------------------------+-----------------------------------------+
        | store                      | 未设置 (None)             | 是，前端注入持久化 store 用于 memory。   |
        |                            |                           | 本脚本不依赖跨线程记忆，不影响单次查询   |
        |                            |                           | 的工具调用结果。                          |
        +----------------------------+---------------------------+-----------------------------------------+
        | run_id / RunJournal        | 未设置                    | 是，前端用于事件追踪和 token 用量统计。  |
        |                            |                           | 本脚本只关心最终文本回复，不需要           |
        |                            |                           | token 统计和事件日志。                    |
        +----------------------------+---------------------------+-----------------------------------------+

        结论：对于「向 knowledge 工具发查询 → 取回复」这一场景，
        checkpointer / store / RunJournal 不参与 agent 决策和工具调用，
        因此简化版与前端结果一致。
    """
    config = {
        "configurable": {
            "thread_id": thread_id,
            "model_name": None,  # 使用 config.yaml 的默认模型
            "thinking_enabled": True,
            "is_plan_mode": False,
            "subagent_enabled": False,
        },
        "metadata": {
            "agent_name": "default",
        },
    }

    # 注入 __pregel_runtime — 与 worker.py 的 _install_runtime_context 一致
    # 使 tool 能获取 runtime 依赖（thread_id, run_id, app_config）
    runtime_ctx = {
        "thread_id": thread_id,
        "run_id": str(uuid.uuid4()),
        "app_config": get_app_config(),
    }
    runtime = Runtime(context=runtime_ctx)
    config.setdefault("configurable", {})["__pregel_runtime"] = runtime

    runnable_config = RunnableConfig(**config)

    # 创建 agent — 与前端相同的工厂函数
    agent = make_lead_agent(config=runnable_config)
    agent.checkpointer = MemorySaver()

    last_text = ""
    async for chunk in agent.astream(
        {"messages": [HumanMessage(content=question)]},
        config=runnable_config,
        stream_mode="values",
    ):
        messages = chunk.get("messages", [])
        if not messages:
            continue
        last_msg = messages[-1]
        if hasattr(last_msg, "type") and last_msg.type == "ai" and last_msg.content:
            last_text = last_msg.content if isinstance(last_msg.content, str) else str(last_msg.content)

    return last_text


async def main():
    logger.info("=" * 60)
    logger.info("Entity Knowledge Base — Batch Test")
    logger.info("Total queries: %d", len(QUERIES))
    logger.info("Results file: %s", RESULTS_FILE)
    logger.info("=" * 60)

    results = []
    for i, query in enumerate(QUERIES, 1):
        thread_id = f"entity-test-{uuid.uuid4().hex[:8]}"
        logger.info("[%d/%d] Query: %s", i, len(QUERIES), query)

        try:
            t0 = time.time()
            response = await ask_agent(query, thread_id=thread_id)
            elapsed = time.time() - t0
            logger.info("       Response (%d chars, %.1fs)", len(response), elapsed)
            results.append({"query": query, "response": response, "status": "ok"})
        except Exception as exc:
            logger.error("       Failed: %s", exc, exc_info=True)
            results.append({"query": query, "response": str(exc), "status": "error"})

    df = pd.DataFrame(results)
    df.to_excel(RESULTS_FILE, index=False, engine="openpyxl")
    logger.info("=" * 60)
    logger.info("Done. %d/%d succeeded. Saved to %s", sum(1 for r in results if r["status"] == "ok"), len(results), RESULTS_FILE)


if __name__ == "__main__":
    asyncio.run(main())
