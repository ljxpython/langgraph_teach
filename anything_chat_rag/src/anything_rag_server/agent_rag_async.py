"""
LangGraph 1.0 Agent 的纯异步版本：直接使用 MCP 工具，不做同步包装或返回裁剪，适配本地 LightRAG 向量库（workspace）。

用法与 src/examples/main.py 一致，整体运行在 async 上下文中：
- 工具加载：直接 await MultiServerMCPClient.get_tools()
- Agent 构建：await build_agent_async()
- 调用：await agent.ainvoke(...)
"""

import asyncio
import os
from typing import List

from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from langchain.agents import create_agent




from src.llms import get_default_model
from src.anything_rag_server.collections_tool import (
    get_available_collections,
    get_available_collections_raw,
)


async def _load_mcp_tools_async() -> List[BaseTool]:
    """直接异步加载 MCP 工具，不做同步包装。"""
    url = os.getenv("ANYTHING_RAG_MCP_URL", "http://0.0.0.0:8000/")
    transport = os.getenv("ANYTHING_RAG_MCP_TRANSPORT", "sse")
    server_name = os.getenv("ANYTHING_RAG_MCP_NAME", "anything-rag")
    client = MultiServerMCPClient({server_name: {"url": url, "transport": transport}})
    try:
        return await client.get_tools()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] 加载 MCP 工具失败：{exc}")
        return []


async def get_rag_tools_async() -> List[BaseTool]:
    """异步版本的 RAG MCP 工具加载。"""
    url = os.getenv("ANYTHING_RAG_MCP_URL", "http://0.0.0.0:8000/")
    transport = os.getenv("ANYTHING_RAG_MCP_TRANSPORT", "sse")
    server_name = os.getenv("ANYTHING_RAG_MCP_NAME", "anything-rag")
    client = MultiServerMCPClient(
        {
            server_name: {
                "url": url,
                "transport": transport,
            }
        }
    )
    try:
        return await client.get_tools()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] 加载 RAG MCP 工具失败：{exc}")
        return []


async def build_agent_async():
    """构建纯异步 Agent，工具直接使用 MCP 提供的 coroutine。"""
    # tools: List[BaseTool] = [get_available_collections]
    # # 根据需要选择加载哪组 MCP 工具，这里默认用 RAG 服务
    # tools.extend(await get_rag_tools_async())
    # 也可以换成 await _load_mcp_tools_async()

    system_prompt = (
        "你是检索增强助手，流程：\n"
        "1) 如不确定集合，先调用 get_available_collections。\n"
        "2) 选择集合，使用 RAG 工具（rag_query_rewrite / rag_retrieve / rag_answer / rag_multi_query_search）。\n"
        "3) 输出简洁答案并标注集合/来源；错误时给出可行的下一步。"
    )

    llm = get_default_model()
    return create_agent(model=llm, tools=await get_rag_tools_async(), system_prompt=system_prompt)


async def example_async():
    # 调试工作空间信息（同步工具，直接调用即可）
    print(get_available_collections_raw())

    try:
        agent = await build_agent_async()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] 构建 agent 失败：{exc}")
        return

    try:
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content="帮我查询知识库中关于部署的文档。")]}
        )
        for message in result["messages"]:
            message.pretty_print()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] 示例调用失败：{exc}")

agent = asyncio.run(build_agent_async())

if __name__ == "__main__":
    asyncio.run(example_async())
