# DeerFlow 工具与技能加载机制

## 概述

DeerFlow 的工具（Tools）和技能（Skills）是 Agent 能力的两个核心来源。它们的加载机制完全不同，但在 Lead Agent 的构建过程中汇合。

- **工具**: 可执行的 Python 函数/类（`BaseTool` 实例），通过动态反射导入，Agent 可以直接调用
- **技能**: 带 YAML frontmatter 的 Markdown 文件（`SKILL.md`），描述工作流和指令，Agent 通过 `read_file` 渐进式加载

---

## 一、默认加载的工具

### 1.1 配置工具（来自 `config.yaml`）

**当前配置** (`config.yaml`) 中启用了 5 个工具组:

```
tool_groups: web, knowledge, file:read, file:write, bash
```

这 5 个组下的 **12 个工具**默认全部加载:

| 工具名 | 所属组 | 实现模块 | 用途 |
|--------|--------|----------|------|
| `web_search` | web | `deerflow.community.ddg_search.tools:web_search_tool` | DuckDuckGo 网页搜索 (max_results: 5) |
| `web_fetch` | web | `deerflow.community.jina_ai.tools:web_fetch_tool` | Jina AI Reader 网页获取 (timeout: 10) |
| `image_search` | web | `deerflow.community.image_search.tools:image_search_tool` | DuckDuckGo 图片搜索 (max_results: 5) |
| `ls` | file:read | `deerflow.sandbox.tools:ls_tool` | 列出目录内容 |
| `read_file` | file:read | `deerflow.sandbox.tools:read_file_tool` | 读取文件 |
| `glob` | file:read | `deerflow.sandbox.tools:glob_tool` | 文件模式匹配 (max_results: 200) |
| `grep` | file:read | `deerflow.sandbox.tools:grep_tool` | 文件内容搜索 (max_results: 100) |
| `write_file` | file:write | `deerflow.sandbox.tools:write_file_tool` | 写入文件 |
| `str_replace` | file:write | `deerflow.sandbox.tools:str_replace_tool` | 字符串替换 |
| `bash` | bash | `deerflow.sandbox.tools:bash_tool` | 执行 bash 命令 |
| `get_table_schema` | knowledge | `deerflow.tools.database.tools:get_table_schema_tool` | 获取数据库表结构 |
| `execute_sql` | knowledge | `deerflow.tools.database.tools:execute_sql_tool` | 执行 SQL 查询 |

### 1.2 内置工具（硬编码，按条件加载）

文件: `backend/packages/harness/deerflow/tools/tools.py`

**始终加载**（`BUILTIN_TOOLS` 常量）:

| 工具名 | 来源文件 | 用途 |
|--------|----------|------|
| `present_file_tool` | `tools/builtins/present_file_tool.py` | 向用户展示输出文件 |
| `ask_clarification_tool` | `tools/builtins/clarification_tool.py` | 请求用户澄清（由中间件拦截） |

**按条件加载**:

| 工具名 | 加载条件 | 用途 |
|--------|----------|------|
| `view_image_tool` | 模型配置 `.supports_vision: true` | 读取图片为 base64 |
| `task_tool` | `subagent_enabled=True`（运行时参数） | 委托任务给子 Agent |
| `skill_manage_tool` | `config.skill_evolution.enabled: true` | 管理自定义技能（增删改） |
| `tool_search` | `config.tool_search.enabled: true` 且有 MCP 工具 | 搜索并激活延迟加载的 MCP 工具 |
| `setup_agent` | bootstrap 模式（`is_bootstrap=True`） | 引导创建自定义 Agent |
| `update_agent` | 自定义 Agent 模式（`agent_name` 已设置） | 允许 Agent 自我更新 |
| `invoke_acp_agent` | `config.yaml` 中存在 `acp_agents` | 调用外部 ACP 兼容 Agent |

### 1.3 MCP 工具（来自 `extensions_config.json`）

**当前配置**: 3 个 MCP 服务器全部为 `enabled: false`，**默认不加载任何 MCP 工具**。

| 服务器 | 类型 | 用途 | 状态 |
|--------|------|------|------|
| `filesystem` | stdio (npx) | 文件系统访问 | ❌ 禁用 |
| `github` | stdio (npx) | GitHub 仓库操作 | ❌ 禁用 |
| `postgres` | stdio (npx) | PostgreSQL 数据库访问 | ❌ 禁用 |

### 1.4 默认加载的工具总结

**当前配置下，默认总共加载 14 个工具**:

```
web_search, web_fetch, image_search,        # web 组
ls, read_file, glob, grep,                   # file:read 组
write_file, str_replace,                     # file:write 组
bash,                                        # bash 组
get_table_schema, execute_sql,               # knowledge 组
present_file_tool, ask_clarification_tool    # 内置工具
```

注意：`config.yaml` 中 `tool_groups` 只定义了组名，Agent 实际加载哪些组由调用方（`get_available_tools(groups=...)`）决定。如果不指定 `groups` 参数，**所有组的工具全部加载**。

---

## 二、默认加载的技能

### 2.1 技能目录结构

```
skills/
├── public/       # 22 个内置只读技能（git 管理）
└── custom/       # 用户自定义技能（当前为空）
```

### 2.2 全部 22 个内置技能

| 技能名称 | 描述 |
|----------|------|
| `academic-paper-review` | 学术论文审阅、分析、批评和总结 |
| `bootstrap` | 首次部署 & 初始化引导 |
| `chart-visualization` | 数据可视化，支持 26 种图表 |
| `claude-to-deerflow` | 通过 HTTP API 与 DeerFlow 交互或委派任务 |
| `code-documentation` | 代码文档生成（README、API 文档、架构文档等） |
| `consulting-analysis` | 专业咨询级研究报告（市场分析、竞品分析等） |
| `data-analysis` | Excel/CSV 数据分析、统计、透视表 |
| `deep-research` | 多角度系统性网络研究 |
| `entity-knowledge` | 实体知识库构建 / 维护 |
| `find-skills` | 发现和安装技能 |
| `frontend-design` | 高质量前端界面设计开发 |
| `github-deep-research` | GitHub 仓库多轮深度研究 |
| `image-generation` | 图片生成 |
| `newsletter-generation` | 新闻稿/邮件摘要生成 |
| `podcast-generation` | 文本转双人对话播客 |
| `ppt-generation` | PPT 生成 |
| `skill-creator` | 创建、修改、评估技能 |
| `surprise-me` | 动态组合已启用技能创造惊喜体验 |
| `systematic-literature-review` | 系统文献综述/跨论文综合 |
| `vercel-deploy-claimable` | Vercel 应用部署 |
| `video-generation` | 视频生成 |
| `web-design-guidelines` | UI 代码设计规范审计 |

### 2.3 启用状态

在 `extensions_config.json` 中配置：

```json
{
  "skills": {
    "image-generation": { "enabled": true }
  }
}
```

规则：
- `extensions_config.json` 中显式列出的技能，按配置的 `enabled` 值决定
- **未在配置中列出的技能，默认启用**
- 所以当前 22 个技能中，`image-generation` 置为 `enabled: true`，其余 21 个技能未显式配置 → 全部默认启用

### 2.4 默认启用的技能总结

**当前配置下，所有 22 个技能默认全部启用**（因为只有 `image-generation` 被显式标记为启用，其余未配置的默认即为启用状态）。

---

## 三、工具加载机制详解

### 3.1 入口函数

```
get_available_tools(groups, include_mcp, model_name, subagent_enabled, app_config)
    → list[BaseTool]
```

**文件路径**: `backend/packages/harness/deerflow/tools/tools.py`（第 36 行）

### 3.2 加载流程

```
开始
  │
  ├─ 1. 从 config.yaml 读取 tools 列表
  │     └─ 按 groups 过滤（如果指定）
  │
  ├─ 2. resolve_variable(cfg.use, BaseTool)
  │     └─ importlib.import_module() + getattr()
  │     └─ 示例: "deerflow.community.ddg_search.tools:web_search_tool"
  │              → import deerflow.community.ddg_search.tools
  │              → getattr(module, "web_search_tool")
  │
  ├─ 3. 添加内置工具（BUILTIN_TOOLS + 按条件）
  │
  ├─ 4. 添加 MCP 工具（如果有启用且 include_mcp=True）
  │
  ├─ 5. 添加 ACP 工具（如果有配置）
  │
  └─ 6. 按 name 去重（配置 > 内置 > MCP > ACP）
      └─ 返回 unique_tools
```

### 3.3 关键代码路径

| 步骤 | 函数/文件 | 作用 |
|------|-----------|------|
| 配置加载 | `config.tools` → `ToolConfig` 列表 | 读取 YAML 配置 |
| 反射导入 | `reflection/resolvers.py:resolve_variable()` | 动态导入模块 |
| 工具组装 | `tools/tools.py:get_available_tools()` | 合并所有来源 |
| 去重 | `tools/tools.py` 第 163-174 行 | 按 name 去重 |
| MCP 加载 | `mcp/tools.py:get_mcp_tools()` | 加载 MCP 服务器工具 |
| MCP 缓存 | `mcp/cache.py:get_cached_mcp_tools()` | 带 mtime 失效的缓存 |

### 3.4 反射加载详解: `resolve_variable()`

```python
# deerflow/reflection/resolvers.py
def resolve_variable(variable_path: str, expected_type: type | None = None):
    # "deerflow.sandbox.tools:bash_tool"
    #  → module_path = "deerflow.sandbox.tools"
    #  → variable_name = "bash_tool"
    module = importlib.import_module(module_path)
    obj = getattr(module, variable_name)
    if expected_type:
        isinstance(obj, expected_type)  # 验证
    return obj
```

---

## 四、技能加载机制详解

### 4.1 入口函数

```
SkillStorage.load_skills(enabled_only=False) → list[Skill]
```

**文件路径**: `backend/packages/harness/deerflow/skills/storage/skill_storage.py`（第 212 行）

### 4.2 加载流程

```
开始
  │
  ├─ 1. _iter_skill_files()
  │     └─ 递归遍历 skills/public/ 和 skills/custom/
  │     └─ 找到所有 SKILL.md（跳过 . 开头目录）
  │
  ├─ 2. parse_skill_file(path)
  │     └─ 解析 YAML frontmatter
  │     └─ 返回 Skill(name, description, allowed-tools, ...)
  │
  ├─ 3. 按 name 去重（custom 覆盖 public）
  │
  ├─ 4. 从 extensions_config.json 合并启用状态
  │
  ├─ 5. 按 enabled_only 过滤（可选）
  │
  └─ 6. 按 name 字母序排序
      └─ 返回 skills[]
```

### 4.3 SKILL.md 解析

```yaml
---
name: deep-research
description: 多角度系统性网络研究
allowed-tools:
  - web_search
  - web_fetch
  - read_file
  - write_file
---
# Deep Research Skill
...
```

YAML frontmatter 必需字段: `name`、`description`
可选字段: `license`、`allowed-tools`

文件路径: `backend/packages/harness/deerflow/skills/parser.py:parse_skill_file()`

### 4.4 关键代码路径

| 步骤 | 函数/文件 | 作用 |
|------|-----------|------|
| 迭代发现 | `skill_storage.py:_iter_skill_files()` | 递归扫描目录 |
| frontmatter 解析 | `parser.py:parse_skill_file()` | 解析 YAML frontmatter |
| 配置合并 | `skill_storage.py` 第 231 行 | 读 `extensions_config.json` |
| 安全扫描 | `security_scanner.py:scan_skill_content()` | LLM 调节审查 |
| ZIP 安装 | `installer.py` | .skill 存档安全解压 |
| 存储抽象 | `storage/skill_storage.py` | ABC 定义存储操作 |
| 本地实现 | `storage/local_skill_storage.py` | 本地文件系统实现 |

---

## 五、工具与技能在 Lead Agent 中的汇合

### 5.1 Agent 工厂

文件: `backend/packages/harness/deerflow/agents/lead_agent/agent.py:_make_lead_agent()`（第 350 行）

```python
def _make_lead_agent(config: RunnableConfig):
    # 1. 创建模型
    model = create_chat_model(name=model_name, ...)

    # 2. 加载工具
    tools = get_available_tools(groups=..., subagent_enabled=..., ...)

    # 3. 按技能策略过滤工具
    skills = _load_enabled_skills_for_tool_policy(...)
    tools = filter_tools_by_skill_allowed_tools(tools, skills)

    # 4. 构建系统提示（含技能列表）
    system_prompt = apply_prompt_template(available_skills=..., ...)

    # 5. 编译 Agent
    return create_agent(
        model=model,
        tools=tools,
        middleware=_build_middlewares(...),
        system_prompt=system_prompt,
        state_schema=ThreadState,
    )
```

### 5.2 技能-工具过滤

文件: `backend/packages/harness/deerflow/skills/tool_policy.py:filter_tools_by_skill_allowed_tools()`

- 如果所有技能都**没有**声明 `allowed-tools` → 返回全部工具（默认行为）
- 如果有技能声明了 `allowed-tools` → 仅保留这些集合的并集
- 声明了 `allowed-tools` 但技能未启用 → 不参与过滤

### 5.3 系统提示中的技能注入

文件: `backend/packages/harness/deerflow/agents/lead_agent/prompt.py:get_skills_prompt_section()`（第 626 行）

```xml
<skill_system>
You have access to skills that provide optimized workflows...
**Progressive Loading Pattern:** ...
<available_skills>
    <skill>
        <name>deep-research</name>
        <description>多角度系统性网络研究</description>
        <location>/mnt/skills/public/deep-research/SKILL.md</location>
    </skill>
    ...
</available_skills>
</skill_system>
```

Agent 看到技能列表和路径后，在需要时才通过 `read_file` 读取具体 `SKILL.md`，实现**渐进式加载**。

### 5.4 完整数据流

```
config.yaml (tools: [...])
       │
       ▼
resolve_variable("module.path:var_name")
       │  importlib + getattr
       ▼
BaseTool 实例 (12个)
       │                                        extensions_config.json
       │                                        (MCP servers: 全部禁用)
       ▼                                        (skills: 22个启用)
get_available_tools()
       │  + BUILTIN_TOOLS (2个)
       │  + 按条件加载 (0个，因条件不满足)
       │  + MCP (0个，因全部禁用)
       │  + ACP (0个，因未配置)
       │  = 14 个工具
       ▼
filter_tools_by_skill_allowed_tools()
       │  所有技能未声明 allowed-tools → 全部保留
       ▼
create_agent(tools=14个工具,
             system_prompt=<available_skills: 22个技能>)
```

### 5.5 相关中间件

| 中间件 | 文件 | 作用 |
|--------|------|------|
| `DeferredToolFilterMiddleware` | `agents/middlewares/` | 延迟工具 schema 隐藏（`tool_search.enabled` 时） |
| `ClarificationMiddleware` | `agents/middlewares/` | 拦截 `ask_clarification` 工具调用 |
| `SandboxAuditMiddleware` | `agents/middlewares/` | bash 命令安全审计 |
| `SubagentLimitMiddleware` | `agents/middlewares/` | 子 Agent 并发限制 |
| `LoopDetectionMiddleware` | `agents/middlewares/` | 工具调用循环检测 |

---

## 六、总结

| 维度 | 工具 (Tools) | 技能 (Skills) |
|------|-------------|---------------|
| **本质** | 可执行 Python 函数 (`BaseTool`) | Markdown 指令文件 (`SKILL.md`) |
| **配置来源** | `config.yaml` → `tools[]` | `skills/public/*/SKILL.md` + `extensions_config.json` |
| **加载方式** | `resolve_variable()` 动态反射导入 | 递归扫描目录 + frontmatter 解析 |
| **Agent 调用方式** | 直接作为工具函数调用 | 通过 `read_file` 渐进式读取 |
| **注册机制** | 无中央注册表，靠模块路径引用 | `SkillStorage.load_skills()` 统一收集 |
| **默认数量** | 14 个 (当前配置) | 22 个 (全部启用) |

### 如何验证

1. **查看当前工具列表**: 读取 `config.yaml` 的 `tools:` 部分
2. **查看当前技能列表**: 浏览 `skills/public/` 目录
3. **查看启用状态**: 检查 `extensions_config.json` 的 `skills` 键
4. **API 查看**: 启动应用后访问 `/api/skills` 和 MCP 相关 API
