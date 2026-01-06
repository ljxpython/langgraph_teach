"""MCP工具集成 - RAG知识检索和Chart图表生成."""
import asyncio
from typing import Any

from langchain_core.tools import BaseTool

from k6_agent.config import K6Config, DEFAULT_CONFIG


def get_rag_tools(config: K6Config | None = None) -> list[BaseTool]:
    """获取RAG MCP工具.
    
    Args:
        config: K6配置，默认使用DEFAULT_CONFIG
        
    Returns:
        RAG工具列表
    """
    cfg = config or DEFAULT_CONFIG
    
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        client = MultiServerMCPClient({
            "rag-server": {
                "url": cfg.rag_mcp_url,
                "transport": "sse",
            }
        })
# pylint: disable
        
        tools = asyncio.run(client.get_tools())
        return list(tools)
    except Exception as e:
        print(f"Warning: Failed to load RAG MCP tools: {e}")
        return []


def get_chart_tools(config: K6Config | None = None) -> list[BaseTool]:
    """获取Chart MCP工具.
    
    Args:
        config: K6配置，默认使用DEFAULT_CONFIG
        
    Returns:
        Chart工具列表
    """
    cfg = config or DEFAULT_CONFIG
    
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        client = MultiServerMCPClient({
            "chart-server": {
                "command": cfg.chart_mcp_command,
                "args": cfg.chart_mcp_args,
                "transport": "stdio",
            }
        })
        
        tools = asyncio.run(client.get_tools())
        return list(tools)
    except Exception as e:
        print(f"Warning: Failed to load Chart MCP tools: {e}")
        return []

def get_login_tools(config: K6Config | None = None) -> list[BaseTool]:
    """获取登录工具.

    Args:
        config: K6配置，默认使用DEFAULT_CONFIG

    Returns:
        登录工具列表
    """
    cfg = config or DEFAULT_CONFIG

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        client = MultiServerMCPClient({
            "login-server": {
                "url": cfg.login_mcp_url,
                "transport": "sse",
            }
        })
        tools = asyncio.run(client.get_tools())
        return list(tools)
    except Exception as e:
        print(f"Warning: Failed to load Login MCP tools: {e}")
        return []
def get_all_mcp_tools(config: K6Config | None = None) -> list[BaseTool]:
    """获取所有MCP工具.
    
    Args:
        config: K6配置
        
    Returns:
        所有MCP工具列表
    """
    tools = []
    tools.extend(get_rag_tools(config))
    tools.extend(get_chart_tools(config))
    return tools

