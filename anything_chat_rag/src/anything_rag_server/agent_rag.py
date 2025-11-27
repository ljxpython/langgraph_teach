"""
LangGraph 1.0 Agent，加载 MCP RAG 工具与本地 workspace 工具（rag_storage）。

说明：
- LangChain 的 StructuredTool 默认异步；create_agent 会在内部处理 async。
- 如果需要同步调用，可包一层 asyncio.run。
"""

import asyncio
import os
from typing import List

from langchain.agents import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool, StructuredTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from llms import get_default_model
from anything_rag_server.collections_tool import (
    get_available_collections,
    get_available_collections_raw,
)


def _wrap_sync(tool: BaseTool) -> StructuredTool:
    """给只有异步实现的 MCP 工具补同步入口，避免 sync 调用时报错。"""

    async def _acall(**kwargs):
        result = await tool.ainvoke(kwargs)
        # 对于 MCP 工具默认 response_format='content_and_artifact' 的场景，只保留内容，避免上层 StructuredTool 期待二元组
        if getattr(tool, "response_format", "") == "content_and_artifact":
            if isinstance(result, tuple):
                return result[0]
        return result

    def _scall(**kwargs):
        return asyncio.run(_acall(**kwargs))

    return StructuredTool.from_function(
        func=_scall,
        coroutine=_acall,
        name=tool.name,
        description=tool.description or "",
        args_schema=getattr(tool, "args_schema", None),
        infer_schema=False,
        response_format="content",
        metadata=getattr(tool, "metadata", None),
    )


def get_rag_tools():
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
    tools = asyncio.run(client.get_tools())
    # MCP 工具默认只有异步实现，补同步入口并规整返回格式，便于后续 agent.invoke 同步调用
    return [_wrap_sync(t) for t in tools]



def build_agent():
    tools: List[BaseTool] = [get_available_collections]
    tools.extend(get_rag_tools())

    system_prompt = (
        "你是检索增强助手，流程：\n"
        "1) 如不确定工作空间，先调用 get_available_collections。\n"
        "2) 选择 workspace，使用 RAG 工具（rag_query_rewrite / rag_retrieve / rag_answer / rag_multi_query_search）。\n"
        "3) 输出简洁答案并标注 workspace/来源；错误时给出可行的下一步。"
    )

    from langchain.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt + "\n\n可用工具列表：{tool_names}\n{tools}"),
            ("human", "{input}"),
            ("assistant", "{agent_scratchpad}"),
        ],
        template_variables={"input", "agent_scratchpad", "tools", "tool_names"},
    )

    llm = get_default_model()
    return create_react_agent(llm, tools=tools, prompt=prompt)


def example():
    # 调试工作空间信息（同步）
    print(get_available_collections_raw())

    try:
        agent = build_agent()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] 构建 agent 失败：{exc}")
        return

    try:
        result = agent.invoke({"messages": [HumanMessage(content="帮我查询知识库中关于部署的文档。")]})
        for i in result["messages"]:
            i.pretty_print()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] 示例调用失败：{exc}")


if __name__ == "__main__":
    example()
