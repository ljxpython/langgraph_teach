"""集成版 Deep Agent（适配 LangGraph API 部署）。

- 不自带 store/checkpointer，使用平台提供的持久化
- 后端：State + /memories/ 路由到 Store
- 子智能体：研究（智谱 MCP 搜索）+ 写作
"""

import asyncio
import os
from collections.abc import Callable
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langchain.messages import HumanMessage
from langchain.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.llms import get_default_model
from src.deep_agent_demo.integrated_agent_demo.agent import DEFAULT_SYSTEM_PROMPT  # 复用系统提示


def get_zhipu_search_mcp_tools():
    """获取智谱搜索 MCP 工具列表，依赖环境变量 zhipu_search_mcp_url。"""
    url = os.environ.get("zhipu_search_mcp_url")
    if not url:
        raise RuntimeError("缺少环境变量 zhipu_search_mcp_url，无法初始化搜索工具")
    client = MultiServerMCPClient(
        {
            "search": {
                "url": url,
                "transport": "sse",
            }
        }
    )
    return asyncio.run(client.get_tools())


@tool
def write_outline(title: str) -> str:
    """生成简短提纲，便于写作子智能体使用。"""
    return f"Outline for {title}: 背景/要点/总结"


def build_subagents() -> list[dict[str, Any]]:
    search_tools = get_zhipu_search_mcp_tools()
    research_subagent = {
        "name": "research-agent",
        "description": "负责检索与信息汇总，适合复杂研究型问题",
        "system_prompt": """你是研究专家：
1) 拆分查询并调用 search 工具收集要点
2) 整理 150-200 字摘要，给出关键发现""",
        "tools": search_tools,
    }

    writer_subagent = {
        "name": "writer-agent",
        "description": "负责提纲与成稿，突出行动项和结论",
        "system_prompt": """你是写作助手：
1) 若缺少结构先生成提纲（可调用 write_outline）
2) 输出 150-200 字报告，提炼行动项""",
        "tools": [write_outline],
    }

    return [research_subagent, writer_subagent]


def build_backend() -> Callable[[Any], Any]:
    """仅使用 State + /memories/ 路由到 Store，避免本地磁盘映射，适合托管部署。"""
    return lambda rt: CompositeBackend(
        default=StateBackend(rt),
        routes={"/memories/": StoreBackend(rt)},
    )


def build_integrated_agent_api() -> Callable[..., Any]:
    """适配 LangGraph API 的 Agent（无自定义 store/checkpointer）。"""
    return create_deep_agent(
        model=get_default_model(),
        backend=build_backend(),
        subagents=build_subagents(),
        system_prompt=DEFAULT_SYSTEM_PROMPT,
    )


async def arun_demo_request(agent: Callable[..., Any], user_message: str, thread_id: str = "integrated-agent-api") -> Any:
    """示例调用（async），方便本地快速验证。"""
    messages = [HumanMessage(content=user_message)]
    result = await agent.ainvoke(
        {"messages": messages},
        config={"configurable": {"thread_id": thread_id}},
    )
    for message in result["messages"]:
        message.pretty_print()
    return result


# 供 LangGraph API 直接加载的 graph 变量
agent = build_integrated_agent_api()


if __name__ == "__main__":
    asyncio.run(
        arun_demo_request(
            agent,
            "请调研'企业知识库检索最佳实践'，把关键信息存入 /memories/research/notes.txt，给我一个精简答复。",
        )
    )
