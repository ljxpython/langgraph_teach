# System prompt to steer the agent to be an expert researcher
import asyncio
import os
from src.llms import get_default_model
from deepagents import create_deep_agent
from langchain_deepseek import ChatDeepSeek
from langchain_mcp_adapters.client import MultiServerMCPClient
def get_zhipu_search_mcp_tools():
    client = MultiServerMCPClient(
        {
            "search": {
                "url": os.environ["zhipu_search_mcp_url"],
                "transport": "sse",
            }
        }
    )
    tools = asyncio.run(client.get_tools())
    return tools
tools = get_zhipu_search_mcp_tools()


# client = MultiServerMCPClient(
#     {
#         "research": {
#             "transport": "streamable_http",  # HTTP-based remote server
#             "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=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",
#         }
#     }
# )
# tools = asyncio.run(client.get_tools())
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""




agent = create_deep_agent(
    model=get_default_model(),
    tools=tools,
    system_prompt=research_instructions
)