## LangGraph/LangChain Memory 学习待办

- [x] 短期记忆持久化：使用 SqliteSaver/SQLite checkpointer 落库 `src/data`，验证同一 `thread_id` 恢复对话。
- [x] 自定义 AgentState：扩展字段（如 user_id/preferences），在 state_schema 中使用。
- [x] 消息管理中间件：`@before_model` 截断、`@after_model` 过滤；验证 RemoveMessage 删除与保留策略。
- [x] 摘要中间件：SummarizationMiddleware 按消息阈值压缩历史，确保「我是谁」可答。
- [x] 工具读写短期记忆：使用 ToolRuntime.state/Command(update=...) 读取/写回状态。
- [x] 长期记忆存储：使用 LangGraph Store（生产用 DB，示例可用内存/SQLite），演示 put/get/search。
- [x] 工具访问长期记忆：在 tool 中通过 runtime.store 读取用户画像。
- [x] 工具写入长期记忆：在 tool 中向 store.put 更新画像，验证跨对话读取。
