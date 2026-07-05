"""Entity Knowledge Base Skill — Batch Test Script (Async).

Tests the person API tools via real lead-agent conversations.
Queries cover all 5 tools: search, profile, content (6 types), cognitive, doc detail.

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
# Each entry tests different tools/content_types of the person API.

QUERIES = [
    # Tool 1 + 2: search + profile
    "介绍特朗普（Donald Trump）。",
    # Tool 1 + 3 (events): search + events
    # "特朗普最近参与了哪些重要事件？",
    # # Tool 1 + 3 (activities): search + activities
    # "特朗普在军事方面有什么活动？",
    # # Tool 1 + 3 (statements): search + statements
    # "特朗普最近说过什么重要言论？",
    # # Tool 1 + 3 (news): search + news
    # "关于特朗普最近有什么新闻报道？",
    # # Tool 1 + 3 (social_discussion): search + social media discussion
    # "别人在社交媒体上是怎么讨论特朗普的？",
    # # Tool 1 + 3 (person_social): search + person's own social media
    # "特朗普自己最近在社交媒体上发了什么？",
    # # Tool 1 + 4: search + cognitive analysis
    # "特朗普的政治立场和对华态度如何？",
    # # Multi-tool combined query
    # "全面分析一下特朗普，包括他的基本信息和政治立场。",
]

# ── Output path ────────────────────────────────────────────────────────────
RESULTS_FILE = Path(__file__).resolve().parent.parent / "entity_knowledge_results.xlsx"


async def ask_agent(question: str, thread_id: str) -> str:
    """Send a single question to the lead agent and return the final AI reply.

    Uses the same ``make_lead_agent`` factory as the Gateway frontend.
    Injects ``__pregel_runtime`` so tools can access thread_id / run_id / config.
    Uses ``MemorySaver`` (in-memory) since batch tests don't need persistence.
    """
    config = {
        "configurable": {
            "thread_id": thread_id,
            "model_name": None,  # use default from config.yaml
            "thinking_enabled": True,
            "is_plan_mode": False,
            "subagent_enabled": False,
        },
        "metadata": {
            "agent_name": "default",
        },
    }

    runtime_ctx = {
        "thread_id": thread_id,
        "run_id": str(uuid.uuid4()),
        "app_config": get_app_config(),
    }
    runtime = Runtime(context=runtime_ctx)
    config.setdefault("configurable", {})["__pregel_runtime"] = runtime

    runnable_config = RunnableConfig(**config)
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
    logger.info("Person Knowledge API — Batch Test")
    logger.info("Total queries: %d", len(QUERIES))
    logger.info("Results file: %s", RESULTS_FILE)
    logger.info("=" * 60)

    results = []
    for i, query in enumerate(QUERIES, 1):
        thread_id = f"person-test-{uuid.uuid4().hex[:8]}"
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
