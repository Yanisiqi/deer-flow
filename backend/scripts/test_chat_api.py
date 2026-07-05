"""Test DeerFlow streaming API — verify parallel tool execution.

Usage:
    cd backend
    uv run python scripts/test_chat_api.py
"""

import json
import time

import requests

BASE_URL = "http://localhost:2026/api"

# Ask the model to search for 3 topics in parallel
QUESTION = "用搜索工具同时查询以下信息：1）今天的北京天气 2）特斯拉今日股价 3）AI最新新闻。请先列出要调用的工具，然后同时调用所有工具，不要一个一个调用。"


def _ensure_auth(session: requests.Session) -> None:
    """Authenticate to Gateway. Creates admin account on first boot."""
    status = session.get(f"{BASE_URL}/v1/auth/setup-status").json()
    if status.get("needs_setup"):
        print("[auth] First boot — creating admin account...")
        resp = session.post(
            f"{BASE_URL}/v1/auth/initialize",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        resp.raise_for_status()
        print("[auth] Admin created. Logging in...")
    else:
        print("[auth] Logging in with existing account...")

    resp = session.post(
        f"{BASE_URL}/v1/auth/login/local",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    resp.raise_for_status()
    print("[auth] Authenticated.\n")


def main():
    session = requests.Session()

    # Quick probe: if auth is disabled, skip login
    probe = session.post(
        f"{BASE_URL}/runs/wait",
        json={"input": {"messages": [{"role": "user", "content": "hi"}]}},
    )
    if probe.status_code in (401, 403):
        _ensure_auth(session)
    else:
        print("[auth] Auth disabled — skipping login.\n")

    print("=" * 60)
    print("Testing parallel tool execution via streaming")
    print("=" * 60)

    body = {
        "input": {"messages": [{"role": "user", "content": QUESTION}]},
        "stream_mode": ["values", "messages"],
    }

    print(f"\nQ: {QUESTION}\n")

    resp = session.post(
        f"{BASE_URL}/runs/stream",
        json=body,
        stream=True,
        timeout=180,
        headers={"Accept": "text/event-stream"},
    )
    resp.raise_for_status()

    stream_start = time.time()
    tool_call_times: dict[str, float] = {}  # tool_call_id → timestamp
    event_type = ""
    for line in resp.iter_lines(decode_unicode=True):
        if line is None:
            continue
        if line == "":
            event_type = ""
            continue
        if line.startswith("event: "):
            event_type = line[7:]
        elif line.startswith("data: "):
            data_str = line[6:]
            if data_str == "[DONE]":
                elapsed = time.time() - stream_start
                print(f"\n\n[Stream finished in {elapsed:.1f}s]\n")
                continue
            try:
                payload = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            if event_type in ("messages-tuple", "messages"):
                if isinstance(payload, list) and len(payload) >= 1:
                    msg = payload[0] if isinstance(payload[0], dict) else {}
                    msg_type = msg.get("type", "")

                    # Tool call — record timestamp
                    if msg_type in ("AIMessageChunk", "ai") and msg.get("tool_calls"):
                        now = time.time()
                        ts = now - stream_start
                        for tc in msg["tool_calls"]:
                            if tc.get("name") and tc.get("id"):
                                tool_call_times[tc["id"]] = now
                        names = [tc.get("name", "?") for tc in msg["tool_calls"] if tc.get("name")]
                        print(f"\n[+{ts:.2f}s] >>> tool_calls: {names}")

                    # Tool result — show timing since tool_call
                    elif msg_type in ("ToolMessage", "tool"):
                        now = time.time()
                        ts = now - stream_start
                        tool_id = msg.get("tool_call_id", "")
                        start_ts = tool_call_times.get(tool_id)
                        if start_ts:
                            tool_duration = now - start_ts
                            print(f"[+{ts:.2f}s] <<< tool_result [{tool_id[:20]}...]: {tool_duration:.2f}s")
                        else:
                            print(f"[+{ts:.2f}s] <<< tool_result [{tool_id[:20]}...]")
                        content = msg.get("content", "")
                        preview = content[:200] if len(str(content)) > 200 else content
                        print(f"    {preview}")

                    # AI text
                    elif msg_type in ("AIMessageChunk", "ai"):
                        text = msg.get("content", "")
                        if text:
                            print(text, end="", flush=True)

    print("\nDone.\n")


ADMIN_EMAIL = "admin@deerflow.local"
ADMIN_PASSWORD = "deerflow2024"

if __name__ == "__main__":
    main()
