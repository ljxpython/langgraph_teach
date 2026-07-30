from __future__ import annotations

import os
import sys
from asyncio import Lock
from pathlib import Path
from typing import Awaitable, Callable

from deepagents import (
    FilesystemPermission,
    GeneralPurposeSubagentProfile,
    HarnessProfile,
    create_deep_agent,
    register_harness_profile,
)
from deepagents.graph import DeepAgentState
from deepagents.backends import FilesystemBackend
from langchain.tools import ToolRuntime, tool
from langchain.agents.middleware import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
    ToolCallRequest,
    wrap_model_call,
)
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from deepagent_src.frontend_teach.sandbox_api import sandbox_backend


load_dotenv(Path(__file__).resolve().parents[1] / ".env")
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"


def get_frontend_model(*, disable_tool_streaming: bool = False) -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-5.5",
        api_key=os.getenv("CHATGPT_API_KEY"),
        base_url=os.getenv("CHATGPT_API_URL"),
        disable_streaming="tool_calling" if disable_tool_streaming else False,
    )


register_harness_profile(
    "openai:gpt-5.5",
    HarnessProfile(
        general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
    ),
)


agent = create_deep_agent(
    model=get_frontend_model(),
    tools=[],
    subagents=[],
    system_prompt=(
        "你是 Deep Agents Frontend 教学助手。"
        "本章只讲概述，不调用工具。"
        "用中文简洁解释 stream.messages、stream.subagents、stream.values "
        "分别如何被前端展示。"
    ),
)


@tool
def frontend_note(topic: str) -> str:
    """Record the frontend concept currently being inspected."""
    return f"已记录前端观察点：{topic}"


subagent_stream_agent = create_deep_agent(
    model=get_frontend_model(disable_tool_streaming=True),
    tools=[frontend_note],
    subagents=[
        {
            "name": "frontend_researcher",
            "description": (
                "解释 Deep Agents frontend stream 里的 messages、subagents、values。"
                "当用户询问 subagent streaming 时使用。"
            ),
            "model": get_frontend_model(disable_tool_streaming=True),
            "tools": [frontend_note],
            "system_prompt": (
                "你是 frontend_researcher。用中文解释 subagent streaming。"
                "先调用 frontend_note 工具记录你正在观察的前端概念。"
                "输出三点：你正在处理什么、stream.subagents 代表什么、"
                "前端为什么要用 useMessages(stream, subagent)。"
            ),
        }
    ],
    system_prompt=(
        "你是 Deep Agents subagent streaming 教学协调者。"
        "当用户询问 subagent streaming、stream.subagents 或 specialist worker 时，"
        "必须委派给 frontend_researcher。拿到结果后，用中文做简短总结。"
    ),
)


todo_agent = create_deep_agent(
    model=get_frontend_model(disable_tool_streaming=True),
    tools=[],
    subagents=[],
    system_prompt=(
        "你是 Deep Agents Todo list 教学助手。每次收到请求都必须使用 write_todos。"
        "先创建三个具体任务，第一项设为 in_progress，其余设为 pending。"
        "然后依次完成任务：每完成一项立刻调用 write_todos，将它设为 completed，"
        "并把下一项设为 in_progress。最后将三项全部设为 completed，再给出简短中文总结。"
        "每次 write_todos 都必须提交完整列表，不要并行调用。"
        "总结必须说明 React 直接读取 stream.values.todos 并响应式重渲染；"
        "禁止建议复制到本地 useState、手动轮询或维护第二份 todo 状态。"
    ),
)


sandbox_agent = create_deep_agent(
    model=get_frontend_model(disable_tool_streaming=True),
    tools=[],
    subagents=[],
    backend=sandbox_backend,
    system_prompt=(
        "你是 Deep Agents Sandbox 教学编码助手。工作区已经包含 /README.md 和 /src/app.py。"
        "收到请求后必须先 read_file 读取 /src/app.py，然后使用 edit_file 修改 greeting，"
        "再使用 write_file 创建 /CHANGELOG.md。不要调用 execute，不要访问工作区以外的路径。"
        "完成后用中文简短说明修改了哪些文件。"
    ),
)


@tool
def send_release_announcement(channel: str, message: str) -> str:
    """Send a release announcement to a team channel."""
    return f"已发送到 {channel}：{message}"


hitl_agent = create_deep_agent(
    model=get_frontend_model(disable_tool_streaming=True),
    tools=[send_release_announcement],
    subagents=[],
    interrupt_on={
        "send_release_announcement": {
            "allowed_decisions": ["approve", "edit", "reject"],
            "description": "发送团队发布通知",
        }
    },
    system_prompt=(
        "你是 Deep Agents Frontend HITL 教学助手。"
        "每次收到发送发布通知的请求时，必须调用且只调用一次 send_release_announcement。"
        "工具被拒绝后不要重试，直接说明通知没有发送；工具执行后简短确认实际发送参数。"
    ),
)


@tool
def lookup_weather(city: str) -> str:
    """Look up the teaching weather report for a city."""
    return f"{city}：晴，24°C"


@tool
def calculate_total(unit_price: float, quantity: int) -> str:
    """Calculate a purchase total from unit price and quantity."""
    return f"总价：{unit_price * quantity:.2f} 元"


SELECTABLE_TOOL_NAMES = {"lookup_weather", "calculate_total"}


class DynamicToolsState(DeepAgentState):
    enabled_tools: list[str]


def filter_selectable_tools(tools, enabled_tools: set[str]):
    return [
        item
        for item in tools
        if item.name not in SELECTABLE_TOOL_NAMES or item.name in enabled_tools
    ]


@wrap_model_call
async def select_frontend_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
) -> ModelResponse:
    enabled_tools = set(request.state.get("enabled_tools", []))
    return await handler(
        request.override(tools=filter_selectable_tools(request.tools, enabled_tools))
    )


dynamic_tools_agent = create_deep_agent(
    model=get_frontend_model(disable_tool_streaming=True),
    tools=[lookup_weather, calculate_total],
    subagents=[],
    middleware=[select_frontend_tools],
    state_schema=DynamicToolsState,
    system_prompt=(
        "你是 Deep Agents 动态工具教学助手。"
        "只使用本轮提供给你的工具；工具不存在时明确说明该能力本轮未启用，禁止假装调用。"
        "查询天气必须调用 lookup_weather，计算商品总价必须调用 calculate_total。"
        "最后简短列出本轮实际调用的工具。"
    ),
)


SELECTABLE_MCP_TOOL_NAMES = {"teaching_lookup_exchange_rate"}
SKILL_PATHS = {"currency-guide": "/skills/currency-guide/SKILL.md"}
SKILL_DESCRIPTIONS = {
    "currency-guide": "解释汇率结果，并明确教学数据不是实时市场报价。",
}
CAPABILITIES = {
    "currency": {
        "tools": {"teaching_lookup_exchange_rate"},
        "skills": {"currency-guide"},
    }
}
FRONTEND_WORKSPACE = Path(__file__).resolve().parent / "workspace"
EMPTY_SKILLS_WORKSPACE = FRONTEND_WORKSPACE / "empty-skills"
_mcp_tools_cache = None
_mcp_tools_lock = Lock()


class McpSkillsState(DeepAgentState):
    enabled_mcp_tools: list[str]
    enabled_capabilities: list[str]


def filter_selectable_mcp_tools(tools, enabled_tools: set[str]):
    return [
        item
        for item in tools
        if item.name not in SELECTABLE_MCP_TOOL_NAMES or item.name in enabled_tools
    ]


@wrap_model_call
async def select_mcp_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
) -> ModelResponse:
    enabled_tools = set(request.state.get("enabled_mcp_tools", []))
    return await handler(
        request.override(tools=filter_selectable_mcp_tools(request.tools, enabled_tools))
    )


async def load_mcp_tools():
    client = MultiServerMCPClient(
        {
            "teaching": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(Path(__file__).resolve().parent / "mcp_server.py")],
            }
        },
        tool_name_prefix=True,
    )
    return await client.get_tools()


async def cached_mcp_tools():
    global _mcp_tools_cache
    if _mcp_tools_cache is None:
        async with _mcp_tools_lock:
            if _mcp_tools_cache is None:
                _mcp_tools_cache = await load_mcp_tools()
    return _mcp_tools_cache


def static_capability_settings(values: object) -> tuple[set[str], set[str]]:
    capability_ids = values if isinstance(values, list) else []
    tools: set[str] = set()
    skills: set[str] = set()
    for capability_id in capability_ids:
        capability = CAPABILITIES.get(capability_id)
        if capability:
            tools.update(capability["tools"])
            skills.update(capability["skills"])
    return tools, skills


def load_selected_skill(skill_id: str, enabled_skills: set[str]) -> str:
    if skill_id not in enabled_skills:
        return f"Skill {skill_id!r} 未启用，拒绝读取。"
    path = SKILL_PATHS.get(skill_id)
    if path is None:
        return f"未知 Skill：{skill_id}"
    return (FRONTEND_WORKSPACE / path.removeprefix("/")).read_text(encoding="utf-8")


@tool
def load_skill(skill_id: str, runtime: ToolRuntime) -> str:
    """Load the full instructions for an enabled skill by its trusted ID."""
    _, enabled_skills = static_capability_settings(
        runtime.state.get("enabled_capabilities", [])
    )
    return load_selected_skill(skill_id, enabled_skills)


class StaticCapabilityMiddleware(AgentMiddleware):
    async def awrap_model_call(self, request, handler):
        enabled_tools, enabled_skills = static_capability_settings(
            request.state.get("enabled_capabilities", [])
        )
        visible_tools = [
            item
            for item in request.tools
            if item.name != load_skill.name
            and item.name not in SELECTABLE_MCP_TOOL_NAMES
        ]
        if enabled_tools:
            visible_tools.extend(
                item for item in await cached_mcp_tools() if item.name in enabled_tools
            )
        if enabled_skills:
            visible_tools.append(load_skill)
            discovery = "\n".join(
                f"- {skill_id}: {SKILL_DESCRIPTIONS[skill_id]}"
                for skill_id in sorted(enabled_skills)
            )
            base_prompt = request.system_message.text if request.system_message else ""
            system_message = SystemMessage(
                content=(
                    f"{base_prompt}\n\n本轮已启用 Skills：\n{discovery}\n"
                    "需要使用时，先调用 load_skill(skill_id) 读取完整指令。"
                )
            )
        else:
            system_message = request.system_message
        return await handler(
            request.override(tools=visible_tools, system_message=system_message)
        )

    async def awrap_tool_call(self, request: ToolCallRequest, handler):
        tool_name = request.tool_call["name"]
        if tool_name not in SELECTABLE_MCP_TOOL_NAMES:
            return await handler(request)

        enabled_tools, _ = static_capability_settings(
            request.state.get("enabled_capabilities", [])
        )
        if tool_name not in enabled_tools:
            return ToolMessage(
                content=f"MCP Tool {tool_name!r} 未启用，拒绝执行。",
                tool_call_id=request.tool_call["id"],
                status="error",
            )
        dynamic_tool = next(
            item for item in await cached_mcp_tools() if item.name == tool_name
        )
        return await handler(request.override(tool=dynamic_tool))


def selected_skill_ids(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str) and value in SKILL_PATHS]


def factory_skill_settings(values: object):
    enabled = selected_skill_ids(values)
    if enabled:
        return ["/skills/"], None
    return None, [
        FilesystemPermission(
            operations=["read", "write"],
            paths=["/skills/**"],
            mode="deny",
        )
    ]


def isolated_skill_settings(values: object):
    enabled = selected_skill_ids(values)
    root = FRONTEND_WORKSPACE if enabled else EMPTY_SKILLS_WORKSPACE
    return (
        FilesystemBackend(root_dir=root, virtual_mode=True),
        ["/skills/"] if enabled else None,
    )


def build_mcp_skills_graph(
    mcp_tools,
    *,
    backend,
    skills: list[str] | None,
    permissions=None,
):
    return create_deep_agent(
        model=get_frontend_model(disable_tool_streaming=True),
        tools=mcp_tools,
        subagents=[],
        middleware=[select_mcp_tools],
        state_schema=McpSkillsState,
        backend=backend,
        skills=skills,
        permissions=permissions,
        system_prompt=(
            "你是 Deep Agents MCP 与 Skills 教学助手。"
            "查询 USD/CNY 必须使用本轮可见的 MCP 工具；工具不可见时明确说明未启用。"
            "Skill 存在时先读取完整 SKILL.md，再按其要求解释。最后列出实际工具与 skill。"
        ),
    )


async def mcp_skills_factory_agent(config: RunnableConfig):
    skills, permissions = factory_skill_settings(
        config.get("configurable", {}).get("enabled_skills", [])
    )
    return build_mcp_skills_graph(
        await load_mcp_tools(),
        backend=FilesystemBackend(root_dir=FRONTEND_WORKSPACE, virtual_mode=True),
        skills=skills,
        permissions=permissions,
    )


async def mcp_skills_isolated_agent(config: RunnableConfig):
    backend, skills = isolated_skill_settings(
        config.get("configurable", {}).get("enabled_skills", [])
    )
    return build_mcp_skills_graph(
        await load_mcp_tools(),
        backend=backend,
        skills=skills,
    )


mcp_skills_static_agent = create_deep_agent(
    model=get_frontend_model(disable_tool_streaming=True),
    tools=[load_skill],
    subagents=[],
    middleware=[StaticCapabilityMiddleware()],
    state_schema=McpSkillsState,
    backend=FilesystemBackend(root_dir=FRONTEND_WORKSPACE, virtual_mode=True),
    permissions=[
        FilesystemPermission(
            operations=["read", "write"],
            paths=["/skills/**"],
            mode="deny",
        )
    ],
    system_prompt=(
        "你是 Deep Agents 静态能力包教学助手。"
        "查询 USD/CNY 必须调用本轮可见的 MCP 工具；不可见时明确说明能力未启用。"
        "存在已启用 Skill 时必须先调用 load_skill，再严格遵循返回的完整指令。"
        "最后列出实际调用的工具与 Skill。"
    ),
)
