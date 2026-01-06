import asyncio

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient

from llms import get_default_model

@tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

client = MultiServerMCPClient(
    {
        "mcp-server-rag": {
            "url": "http://127.0.0.1:8000/sse",
            "transport": "sse",
        }
    }
)
tools = asyncio.run(client.get_tools())
print(tools)
#
agent = create_agent(model=get_default_model(),
                     tools=[add]
                     )