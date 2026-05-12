# DeerFlow

**DeerFlow** (Deep Exploration and Efficient Research Flow) is ByteDance's open-source super agent harness built with Python (FastAPI + LangGraph) + TypeScript (Next.js 16).

> **Note**: `backend/CLAUDE.md` contains a detailed architecture reference (middleware chain, config schema, development workflow). This file is a lightweight navigation index — check there for deep-dive details.

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, LangGraph 1.1+, LangChain, SQLAlchemy, SQLite/PostgreSQL, Pydantic 2, uv
- **Frontend**: Next.js 16, React 19, TypeScript 5.8, Tailwind CSS 4, TanStack Query 5, Vercel AI SDK 6, Shadcn UI, CodeMirror
- **Infra**: Docker, Nginx (port 2026), Docker Compose

## Key Directories

| Dir | Purpose |
|---|---|
| `backend/packages/harness/deerflow/` | Core agent framework (publishable `deerflow-harness` package) |
| `backend/app/` | FastAPI application layer (routes, auth, IM channels) |
| `frontend/src/` | Next.js UI |
| `skills/` | Agent skill definitions (23 public skills, each has `SKILL.md`) |
| `docker/` | Docker Compose, Nginx config, provisioner |
| `scripts/` | Devops/utility scripts |
| `docs/` | Internal docs and plans |
| `config.yaml` | Main application configuration |
| `extensions_config.json` | MCP servers + skill enable/disable |

## When users ask about...

### Agent orchestration / lead agent / middleware
- `backend/packages/harness/deerflow/agents/lead_agent/` — `make_lead_agent()`, system prompt assembly, tool loading
- `backend/packages/harness/deerflow/agents/middlewares/` — 18 middlewares (sandbox, memory, summarization, loop detection, etc.)
- `backend/packages/harness/deerflow/agents/thread_state.py` — ThreadState schema

### Sub-agents / task delegation
- `backend/packages/harness/deerflow/subagents/` — `general-purpose`, `bash` agents, executor pool (3 workers), 15-min timeout

### Memory system
- `backend/packages/harness/deerflow/agents/memory/` — LLM fact extraction, debounced updates, per-user file storage

### Sandbox / file tools
- `backend/packages/harness/deerflow/sandbox/` — `LocalSandboxProvider` (filesystem) and `AioSandboxProvider` (Docker)

### MCP integration
- `backend/packages/harness/deerflow/mcp/` — Multi-server MCP via `langchain-mcp-adapters`, stdio/SSE/HTTP, OAuth

### Tools
- `backend/packages/harness/deerflow/tools/builtins/` — built-in tools (present_files, ask_clarification, task, etc.)
- `backend/packages/harness/deerflow/community/` — web search/scraping (Tavily, Jina, Firecrawl, DuckDuckGo, Exa, Serper, etc.)

### Models / LLM config
- `backend/packages/harness/deerflow/models/` — Model factory, thinking/vision support, vLLM
- `config.yaml` — model groups and provider config

### API routes
- `backend/app/gateway/routers/` — REST routes (threads, runs, models, mcp, skills, memory, auth, etc.)
- `backend/app/gateway/auth/` — JWT auth, bcrypt, credential files

### IM channel integrations
- `backend/app/channels/` — Feiyu, Slack, Telegram, DingTalk, WeChat, WeCom, Discord

### Skills system
- `backend/packages/harness/deerflow/skills/` — Skills discovery/loading, SKILL.md parsing, .skill ZIP install
- `skills/` — skill definitions directory (`public/` and `custom/`)

### Configuration
- `config.yaml` — main app config
- `extensions_config.json` — MCP servers + skills toggles
- `config.example.yaml` — full reference with docs

### Frontend (general)
- `frontend/src/app/` — Next.js App Router pages
- `frontend/src/components/workspace/` — Chat workspace components
- `frontend/src/components/ai-elements/` — AI-specific UI (artifacts, chain-of-thought, code blocks, etc.)
- `frontend/src/core/threads/` — Thread creation, streaming hooks
- `frontend/src/core/api/` — LangGraph client, stream handlers

### Database / persistence
- `backend/packages/harness/deerflow/persistence/` — Thread metadata, runs, feedback, users, Alembic migrations

### Guardrails / security
- `backend/packages/harness/deerflow/guardrails/` — Pre-tool-call authorization providers

### Tracing / observability
- `backend/packages/harness/deerflow/tracing/` — LangSmith and Langfuse integration

### Tests
- `backend/tests/` — ~160+ Python test files
- `frontend/` — Vitest (unit) + Playwright (e2e)

### Docker / deployment
- `docker/docker-compose.yaml` — production
- `docker/docker-compose-dev.yaml` — dev with hot-reload
- `docker/nginx/nginx.conf` — reverse proxy (port 2026)
