# Integrated Agent Demo

本目录学习要点（文件夹内先列出学习的内容）：
- 综合使用默认中间件（规划/TODO、文件系统、子智能体）与 `CompositeBackend` 路由长期记忆
- `/memories/` 挂载持久化 Store，`/workspace/` 映射本地磁盘（虚拟化），其余路径临时态
- 自定义子智能体：研究（通过智谱 MCP 搜索工具检索与整理）与写作（提纲+成稿），主 Agent 负责协调
- 使用 `HumanMessage` + `pretty_print` 打印对话，便于观察多轮调用与委派
- 支持 InMemoryStore（默认）或 SqliteStore 落盘；可通过参数切换根目录与存储（需要 `zhipu_search_mcp_url` 环境变量初始化搜索工具）
- MCP 搜索工具仅提供异步接口，示例通过 `ainvoke`/`asyncio.run` 调用，请保证 Python 能使用 asyncio
- 示例入口：`agent.py` 中的 `run_demo_request` 和 `__main__` 场景
