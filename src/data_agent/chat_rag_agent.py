import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient

# 从仓库根目录 .env 加载环境变量（不覆盖已存在的系统环境变量）
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env", override=False)
_ = os.getenv("DEEPSEEK_API_KEY")

llm = init_chat_model("deepseek:deepseek-chat")
client = MultiServerMCPClient({
    "rag-server": {
        "url": "http://localhost:8002/sse",
        "transport": "sse",
    }
})

tools = asyncio.run(client.get_tools())
agent = create_agent(model=llm, tools=tools)
