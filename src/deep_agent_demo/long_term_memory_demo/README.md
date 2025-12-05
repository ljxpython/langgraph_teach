# Long-term Memory Demo

本目录学习要点（文件夹内先列出学习的内容）：
- 使用 `CompositeBackend` 路由 `/memories/` 到持久化 Store，其余路径使用内存态 `StateBackend`
- 搭配 `InMemoryStore` 快速体验跨线程记忆；生产可切换 SQLite/Postgres 等 `BaseStore`
- 系统提示中明确哪些信息要写入 `/memories/`，哪些保留在临时区
- 通过 `HumanMessage` + `pretty_print` 观察对话输出
- 示例代码：`agent.py` 展示建链、调用入口与 SQLite Store 的可选配置
