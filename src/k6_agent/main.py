import os
from dotenv import load_dotenv
# pragma: no cover  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002WVc5UE5BPT06ZTk5MDM3ZGQ=

load_dotenv()  # 加载 .env 文件

from langchain_deepseek import ChatDeepSeek

from k6_agent import create_k6_agent, K6AgentConfig
config = K6AgentConfig()
# 移除硬编码的 API Key，改为从环境变量读取
deepseek = ChatDeepSeek(model="deepseek-chat")
# noqa  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002WVc5UE5BPT06ZTk5MDM3ZGQ=

agent = create_k6_agent(model=deepseek, config=config, enable_knowledge_retrieval=False)
