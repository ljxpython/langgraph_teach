

from langchain.agents import create_agent
from llms import get_default_model
from rag_chat.chat.tools import get_mcp_rag_tools, get_available_collections

tools = [get_available_collections] + get_mcp_rag_tools()
agent = create_agent(model=get_default_model(),
                     tools=tools,
                     system_prompt="根据用户的问题从合适的集合中查询相关知识。"
                                   "如果不确定当前使用的collection_name，可以使用 get_available_collections 工具获取所有可用的集合信息，"
                                   "然后根据集合的描述和用户的问题选择最合适的 collection_name。"
                     )