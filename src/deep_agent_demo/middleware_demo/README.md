# Middleware Demo

本目录学习要点（文件夹内先列出学习的内容）：
- 深入理解 create_deep_agent 默认挂载的三大中间件：TodoListMiddleware、FilesystemMiddleware、SubAgentMiddleware
- 自定义子智能体只需通过 `subagents=[...]` 传入，避免重复手动添加默认中间件（否则会触发重复实例错误）
- 结合 CompositeBackend 路由 `/memories/` 持久化，其他路径保持临时态
- 使用 `HumanMessage` + `pretty_print` 观察中间件生效后的对话
- 示例代码：`agent.py` 使用默认中间件，但通过系统提示和自定义子智能体展示规划/文件系统/委派协作流程
