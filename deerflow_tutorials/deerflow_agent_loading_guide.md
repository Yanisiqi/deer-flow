# DeerFlow 智能体加载与配置指南

## 一、工具加载

### 加载入口

`backend/packages/harness/deerflow/tools/tools.py` → `get_available_tools()`

### 工具来源（4 个，按优先级）

| 来源 | 配置位置 | 加载方式 |
|------|----------|----------|
| 配置工具 | `config.yaml` → `tools[]` | `resolve_variable("module:var")` 动态反射导入 |
| 内置工具 | 硬编码 `BUILTIN_TOOLS` | 直接引用 Python 对象 |
| MCP 工具 | `extensions_config.json` → `mcpServers` | `langchain-mcp-adapters` 多服务器客户端 |
| ACP 工具 | `config.yaml` → `acp_agents` | 运行时选择性构建 |

### 默认加载的工具（当前配置，共 14 个）

**配置工具（12 个）：**

| 工具 | 组 | 来源 |
|------|----|------|
| `web_search` | web | DuckDuckGo 搜索 |
| `web_fetch` | web | Jina AI Reader |
| `image_search` | web | DuckDuckGo 图片搜索 |
| `ls` | file:read | 文件系统 |
| `read_file` | file:read | 文件系统 |
| `glob` | file:read | 文件系统 |
| `grep` | file:read | 文件系统 |
| `write_file` | file:write | 文件系统 |
| `str_replace` | file:write | 文件系统 |
| `bash` | bash | 本地执行 |
| `get_table_schema` | knowledge | 数据库 |
| `execute_sql` | knowledge | 数据库 |

**内置工具（2 个）：** `present_file_tool`, `ask_clarification_tool`

MCP/ACP/子智能体工具全部未启用。

### 工具加载的关键机制

- **反射加载**：`reflection/resolvers.py:resolve_variable()` 用 `importlib.import_module()` + `getattr()` 动态导入
- **去重**：按 `name` 去重，优先级 配置 > 内置 > MCP > ACP
- **按组过滤**：`get_available_tools(groups=...)` 指定组，不指定则加载全部

### 配置新增工具

在 `config.yaml` 的 `tools` 列表添加条目：

```yaml
tools:
  - name: my_tool
    group: my_group
    use: my_module.tools:my_tool_function
```

---

## 二、技能加载

### 加载入口

`backend/packages/harness/deerflow/skills/storage/skill_storage.py` → `SkillStorage.load_skills()`

### 目录结构

```
skills/
├── public/       # 22 个内置技能（只读，git 管理）
└── custom/       # 用户自定义技能（可读写，.gitignore）
```

### 默认启用的技能

当前配置下 **22 个技能全部启用**。规则：

- `extensions_config.json` 中显式列出的，按其 `enabled` 值
- **未列出的默认启用**（`is_skill_enabled()` 第 202 行）

### 禁用某个技能

编辑 `extensions_config.json`：

```json
{
  "skills": {
    "image-generation": { "enabled": true },
    "deep-research": { "enabled": false }
  }
}
```

### 技能与工具的不同

| | 工具 (Tool) | 技能 (Skill) |
|--|------------|-------------|
| 本质 | 可执行 `BaseTool` 实例 | `SKILL.md` Markdown 文件 |
| 调用方式 | 直接作为函数调用 | Agent 通过 `read_file` 渐进式读取 |
| 注入提示词 | 作为 `bind_tools` schema | 作为 `<available_skills>` XML 块 |

---

## 三、系统提示词生成

### 入口

`backend/packages/harness/deerflow/agents/lead_agent/prompt.py` → `apply_prompt_template()`

### 提示词构成

```
<role>                     → 角色声明（{agent_name}）
{soul}                     → 自定义 Agent 个性（SOUL.md）
<thinking_style>           → 思维风格指导
<clarification_system>     → 澄清优先原则
{skills_section}           → <available_skills> 技能 XML 列表
{deferred_tools_section}   → <available-deferred-tools> 延迟工具列表
{subagent_section}         → 子智能体编排指令（仅启用时）
<working_directory>        → 工作目录说明
<citations>                → 引用规范
<critical_reminders>       → 关键提醒
```

### 提示词大小（当前配置）

| 部分 | 字符数 | 占比 |
|------|--------|------|
| 总计 | ~22K | 100% |
| 技能部分 | ~12K | 56% |
| 记忆/日期 | 动态注入 | - |

提示词生成后是静态的，记忆和当前日期通过 `DynamicContextMiddleware` 在每个回合注入为 `<system-reminder>` HumanMessage，以最大化前缀缓存复用。

---

## 四、子智能体 (Subagent)

### 启用方式

`subagent_enabled` **不由** `config.yaml` 控制，是运行时参数：

| 方式 | 设置 |
|------|------|
| 前端 ultra 模式 | `subagent_enabled: true` |
| API 请求 | `config.configurable.subagent_enabled: true` |
| IM 频道 | 默认 `false` |

### 子智能体的作用

1. **上下文隔离**：独立 `ThreadState`、独立消息历史，中间工具调用对父不可见
2. **并行执行**：最多并发 3 个（`SubagentLimitMiddleware` 硬限制）
3. **不污染主智能体**：子智能体只返回结果文本 `"Task Succeeded. Result: {text}"`

### 子智能体的工具和技能

- **工具**：默认继承父的全部工具（禁用 `task`、`ask_clarification`、`present_files`）
- **技能**：默认继承父的全部启用技能（完整读取 `SKILL.md` 内容注入）
- 均可通过 `config.yaml` 覆盖（allowlist/denylist）

### 子智能体相关配置

```yaml
subagents:
  timeout_seconds: 900               # 默认超时 15 分钟
  agents:
    general-purpose:
      timeout_seconds: 1800          # 覆盖超时 30 分钟
      skills: ["deep-research"]      # 仅加载指定技能
  custom_agents:                     # 自定义子智能体类型
    analysis:
      description: "数据分析专家"
      system_prompt: "你的角色是数据分析专家..."
      tools: ["bash", "read_file", "write_file"]
```

### 子智能体禁用时的变化

- 系统提示词减少约 7K 字符（无 `<subagent_system>` 编排指令）
- 工具列表减少 `task` 工具
- 无 `SubagentLimitMiddleware`

---

## 五、默认配置速查

### config.yaml

| 配置项 | 当前值 | 备注 |
|--------|--------|------|
| 模型 | deepseek-chat | - |
| 工具组 | web, knowledge, file:read, file:write, bash | 5 组 |
| 工具数 | 12 | 配置工具 |
| Tool Search | disabled | 延迟工具加载 |
| Skill Evolution | disabled | 代理管理技能 |
| Subagent | 不由此文件控制 | 运行时参数 |
| 记忆 | enabled | 30 秒防抖 |
| 摘要 | enabled | 15K tokens 触发 |

### extensions_config.json

| 配置项 | 当前值 |
|--------|--------|
| MCP 服务器 | 3 个，全部禁用 |
| 技能状态 | image-generation 显式启用，其余默认启用 |

---

## 六、测试/调试工具

`scripts/debug/inspect_deerflow_prompt.py` 可以打印当前配置下模型实际看到的内容：

```bash
cd backend/
PYTHONPATH=. uv run python ../scripts/debug/inspect_deerflow_prompt.py
```

输出：工具 schema、技能 XML 块、完整系统提示词、各部分字符数统计。
