# Backends Demo

本目录学习要点（文件夹内先列出学习的内容）：
- 区分内存态 `StateBackend`、本地磁盘 `FilesystemBackend`、持久化 `StoreBackend`、路由式 `CompositeBackend`
- 如何通过 `create_deep_agent(backend=...)` 指定后端、传入必要的 runtime（store、state、checkpoint）
- 在 `/memories/` 等路径前缀上路由到持久化存储，其余保持临时态
- 虚拟文件系统与真实磁盘的映射方式（`root_dir` + `virtual_mode`）
- 使用 `MemorySaver`、`InMemoryStore` 保留会话线程与跨线程数据
- 使用 `SqliteStore`（存储路径示例：`src/data/backends.sqlite`）持久化跨线程文件，连接开启 `check_same_thread=False + isolation_level=None`（autocommit）并设置 `journal_mode=WAL`，避免多线程或嵌套事务报错

示例代码见 `src/deep_agent_demo/backends_demo/agent.py`。
