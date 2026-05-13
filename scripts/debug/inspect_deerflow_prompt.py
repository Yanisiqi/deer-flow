"""
DeerFlow 诊断工具 —— 检查当前配置下模型实际看到的提示词内容。

用法（在 backend/ 目录下运行）:
    PYTHONPATH=. uv run python ../scripts/debug/inspect_deerflow_prompt.py

输出:
    1. 工具列表 + 模型看到的功能调用 schema
    2. 技能列表 + 注入系统提示的 XML 块
    3. 完整系统提示词
"""

import json
import sys

# ============================================================
# 路径修正：允许从 backend/ 或项目根目录运行
# ============================================================
from pathlib import Path

# 假设脚本在 deer-flow/scripts/debug/ 下
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent
_BACKEND_DIR = _PROJECT_ROOT / "backend"

if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# ============================================================
# 辅助函数
# ============================================================

_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_GREEN = "\033[92m"
_MAGENTA = "\033[95m"
_RED = "\033[91m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def _header(text: str, color=_CYAN):
    """Print a section header."""
    width = 72
    print(f"\n{_BOLD}{color}{'=' * width}{_RESET}")
    print(f"{_BOLD}{color}  {text}{_RESET}")
    print(f"{_BOLD}{color}{'=' * width}{_RESET}\n")


def _subheader(text: str):
    print(f"\n{_BOLD}{_GREEN}--- {text} ---{_RESET}\n")


# ============================================================
# 1. 工具诊断
# ============================================================


def inspect_tools():
    """打印所有配置工具 + 内置工具的 schema 信息。"""
    _header("1. 工具列表 (Tools)", _YELLOW)

    from deerflow.config import get_app_config
    from deerflow.tools import get_available_tools
    from deerflow.tools.tools import BUILTIN_TOOLS

    config = get_app_config()

    # -- 1a. 显示 config.yaml 中定义的原始工具配置
    _subheader("1a. config.yaml → 原始工具配置")
    print(f"{_BOLD}{'name':<22} {'group':<14} {'use'}{_RESET}")
    print("-" * 100)
    for t in config.tools:
        print(f"{t.name:<22} {t.group:<14} {t.use}")
    print(f"\n总计: {len(config.tools)} 个配置工具")

    # -- 1b. 显示加载后的完整工具列表（含 schema）
    _subheader("1b. 全部加载的工具（含模型看到的功能调用 schema）")
    tools = get_available_tools(app_config=config)

    # 收集工具分组信息
    config_tool_names = {t.name: t.group for t in config.tools}
    builtin_names = {t.name for t in BUILTIN_TOOLS}

    for i, tool in enumerate(tools, 1):
        group = config_tool_names.get(tool.name, "(built-in)")
        source_flag = f"{_GREEN}[config]{_RESET}" if tool.name in config_tool_names else f"{_MAGENTA}[builtin]{_RESET}"

        print(f"\n{_BOLD}工具 #{i}: {tool.name}{_RESET}  {source_flag}  组: {group}")
        print(f"  description: {tool.description[:200]}{'…' if len(tool.description) > 200 else ''}")

        # args 已经是 JSON Schema 格式
        print(f"  参数 schema:")
        print(f"    {json.dumps(tool.args, indent=4, ensure_ascii=False)}")

    print(f"\n{_BOLD}工具总计: {len(tools)}{_RESET}")

    # -- 1c. 以模型收到的方式显示（OpenAI function-calling 格式）
    _subheader("1c. 功能调用格式（模型实际看到的 bind_tools schema）")
    for i, tool in enumerate(tools, 1):
        openai_schema = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.args,
            },
        }
        print(f"\n{_BOLD}工具 #{i}: {tool.name}{_RESET}")
        print(f"  {json.dumps(openai_schema, indent=2, ensure_ascii=False)}")

    return tools


# ============================================================
# 2. 技能诊断
# ============================================================


def inspect_skills():
    """打印所有技能信息 + 注入系统提示的 XML 片段。"""
    _header("2. 技能列表 (Skills)", _GREEN)

    from deerflow.config import get_app_config
    from deerflow.config.extensions_config import ExtensionsConfig
    from deerflow.skills.storage import get_or_new_skill_storage

    config = get_app_config()
    storage = get_or_new_skill_storage()

    # -- 2a. 加载所有技能
    _subheader("2a. 全部技能（含元信息）")
    all_skills = storage.load_skills(enabled_only=False)
    enabled_skills = storage.load_skills(enabled_only=True)

    ext_cfg = ExtensionsConfig.from_file()

    print(f"{_BOLD}{'name':<32} {'category':<10} {'enabled':<8} {'allowed-tools'}{_RESET}")
    print("-" * 110)
    for s in all_skills:
        enabled_flag = ext_cfg.is_skill_enabled(s.name, s.category)
        enabled_str = f"{_GREEN}✅{_RESET}" if enabled_flag else f"{_RED}❌{_RESET}"
        at = ", ".join(s.allowed_tools) if s.allowed_tools else "(全部)"
        print(f"{s.name:<32} {s.category:<10} {enabled_str:<8} {at}")

    print(f"\n全部: {len(all_skills)}  已启用: {len(enabled_skills)}")

    # -- 2b. 显示注入系统提示的 XML 块
    _subheader("2b. 注入系统提示的 <skill_system> XML 块")
    try:
        from deerflow.agents.lead_agent.prompt import get_skills_prompt_section

        section = get_skills_prompt_section(app_config=config)
        print(section if section else "(无技能注入)")
    except Exception as e:
        print(f"(无法渲染技能提示: {e})")

    return all_skills, enabled_skills


# ============================================================
# 3. 系统提示词诊断
# ============================================================


def inspect_system_prompt():
    """打印完整组装后的系统提示词。"""
    _header("3. 完整系统提示词 (System Prompt)", _MAGENTA)

    from deerflow.config import get_app_config
    from deerflow.agents.lead_agent.prompt import apply_prompt_template

    config = get_app_config()

    _subheader("3a. 默认 Lead Agent 系统提示")
    prompt = apply_prompt_template(
        subagent_enabled=False,
        available_skills=None,
        app_config=config,
    )
    # 截取过长输出，但是保留核心部分
    if len(prompt) > 5000:
        print(prompt[:5000])
        print(f"\n{_YELLOW}... (提示词过长，已截断前 5000 字符，完整长度: {len(prompt)} 字符){_RESET}")
    else:
        print(prompt)

    # -- 启用了 subagent 时
    _subheader("3b. 带子 Agent 支持的 Lead Agent 系统提示 (subagent_enabled=True)")
    prompt_with_sub = apply_prompt_template(
        subagent_enabled=True,
        available_skills=None,
        app_config=config,
    )
    if len(prompt_with_sub) > 5000:
        print(prompt_with_sub[:5000])
        print(f"\n{_YELLOW}... (截断，完整长度: {len(prompt_with_sub)} 字符){_RESET}")
    else:
        print(prompt_with_sub)

    # -- 自定义 Agent
    _subheader("3c. 自定义 Agent 系统提示 (agent_name='test-agent')")
    prompt_custom = apply_prompt_template(
        subagent_enabled=False,
        agent_name="test-agent",
        available_skills=None,
        app_config=config,
    )
    if len(prompt_custom) > 5000:
        print(prompt_custom[:5000])
        print(f"\n{_YELLOW}... (截断，完整长度: {len(prompt_custom)} 字符){_RESET}")
    else:
        print(prompt_custom)

    # -- 提示词各部分占比分析
    _subheader("3d. 提示词各部分字符数统计")

    # 分析各部分
    from deerflow.agents.lead_agent.prompt import (
        get_skills_prompt_section,
        get_deferred_tools_prompt_section,
        get_agent_soul,
    )

    full = prompt
    total = len(full)

    skills_section = get_skills_prompt_section(app_config=config)
    deferred_section = get_deferred_tools_prompt_section(app_config=config)
    soul = get_agent_soul(None)

    parts = {
        "total": total,
        "skills_section": len(skills_section),
        "deferred_tools_section": len(deferred_section),
        "soul": len(soul),
    }

    print(f"  {'部分':<30} {'字符数':<10} {'占比':<8}")
    print(f"  {'-' * 50}")
    for name, count in parts.items():
        pct = count / total * 100 if total > 0 else 0
        label = f"  {name}"
        print(f"{label:<30} {count:<10} {pct:<8.1f}%")

    return prompt


# ============================================================
# 4. 配置总览
# ============================================================


def inspect_config_summary():
    """打印配置总览。"""
    _header("0. 当前配置概览", _CYAN)

    from deerflow.config import get_app_config
    from deerflow.config.extensions_config import ExtensionsConfig

    config = get_app_config()
    ext_cfg = ExtensionsConfig.from_file()

    model_name = config.models[0].name if config.models else "(无)"
    print(f"  模型: {_BOLD}{model_name}{_RESET}")
    print(f"  工具组: {', '.join(g.name for g in config.tool_groups)}")
    print(f"  工具数 (config): {len(config.tools)}")
    print(f"  Tool Search: {'✅ 启用' if config.tool_search.enabled else '❌ 禁用'}")
    print(f"  Skill Evolution: {'✅ 启用' if getattr(config.skill_evolution, 'enabled', False) else '❌ 禁用'}")

    enabled_mcp = ext_cfg.get_enabled_mcp_servers()
    print(f"  MCP 服务器: 共 {len(ext_cfg.mcp_servers)} 个, {len(enabled_mcp)} 个启用")
    for name, srv in ext_cfg.mcp_servers.items():
        status = f"{_GREEN}✅ 启用{_RESET}" if srv.enabled else f"{_RED}❌ 禁用{_RESET}"
        print(f"    - {name}: {status}")

    print(f"  Sandbox: {config.sandbox.use}")
    print(f"  Subagent: {'✅ 启用' if getattr(config.subagents, 'enabled', False) else '❌ 禁用（默认）'}")

    # 硬件信息
    print(f"  记忆系统: {'✅ 启用' if config.memory.enabled else '❌ 禁用'}")
    print(f"  标题自动生成: {'✅ 启用' if config.title.enabled else '❌ 禁用'}")
    print(f"  摘要: {'✅ 启用' if config.summarization.enabled else '❌ 禁用'}")


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    inspect_config_summary()
    inspect_tools()
    inspect_skills()
    inspect_system_prompt()

    print(f"\n{_BOLD}{_GREEN}✅ 诊断完成{_RESET}")
    print(f"{_YELLOW}提示: 要查看每个技能目录下的 SKILL.md 完整内容，运行:{_RESET}")
    print(f"  {_CYAN}ls skills/public/<skill-name>/SKILL.md{_RESET}")
    print(f"{_YELLOW}提示: 要查看动态注入内容（记忆、日期、上传文件），需运行实际对话。{_RESET}")
