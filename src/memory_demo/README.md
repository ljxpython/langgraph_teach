## Memory Demo 学习指南

本目录收集了 LangGraph/LangChain 记忆相关的最小可跑示例，帮助你快速理解短期记忆与长期记忆的使用方式。

### 环境与前置
- Python 环境已安装 langgraph/langchain（项目依赖已满足）。
- 真实调用示例使用 `src/llms.py` 的 `get_default_model`（DeepSeek）；需可用的 API Key 与网络。
- 若仅想跑通流程，可将示例中的 `get_default_model()` 替换为假模型（如 FakeChatModel）。

### 目录索引（示例文件）
- `inmemory_short_term.py`：短期记忆 InMemorySaver。
- `sqlite_short_term.py`：短期记忆 SqliteSaver 持久化到 `src/data/memory_checkpoints.sqlite`。
- `middleware_state.py`：自定义 AgentState + before/after 中间件截断/过滤。
- `summarization_middleware.py`：SummarizationMiddleware 自动摘要长对话。
- `tool_state_interaction.py`：工具读取/写回短期状态（Command(update=... )）。
- `long_term_memory_sqlite.py`：SqliteStore 长期画像读写。
- `graph_short_term_sqlite.py`：StateGraph + SqliteSaver 持久化。
- `graph_long_term_store_sqlite.py`：StateGraph + SqliteStore 长期画像。
- `graph_trim_delete.py`：trim_messages 截断控制上下文。
- `checkpoint_management.py`：检查点查看、历史、清理示例。
- `semantic_search_store.py`：InMemoryStore 语义搜索（内置简易 embedding，可离线）。

### 推荐学习顺序
1) 短期记忆基础：`inmemory_short_term.py` → `sqlite_short_term.py`（理解 thread_id 与持久化文件）。  
2) 状态与中间件：`middleware_state.py`（自定义 AgentState、截断/过滤）、`graph_trim_delete.py`（trim_messages）。  
3) 长对话治理：`summarization_middleware.py`（摘要压缩）。  
4) 工具与状态交互：`tool_state_interaction.py`（ToolRuntime.state / Command 写回）。  
5) 长期记忆：`long_term_memory_sqlite.py`（store.put/get/search），再看 `graph_long_term_store_sqlite.py`（在 StateGraph 节点中读写 store）。  
6) 辅助：`checkpoint_management.py`（查看/删除检查点）、`semantic_search_store.py`（开箱即用的简单语义搜索）。

### 快速运行
```bash
# 示例：短期记忆 SQLite 持久化
python -m src.memory_demo.sqlite_short_term

# 示例：StateGraph + 持久化
python -m src.memory_demo.graph_short_term_sqlite

# 示例：长期记忆 SqliteStore
python -m src.memory_demo.long_term_memory_sqlite
```
其余文件同样使用 `python -m src.memory_demo.<文件名去掉后缀>` 运行。

### 验证与自测建议
- 首轮输入“我叫 XX”，二轮询问“我叫什么名字？”应能记住姓名（短期记忆）。
- 重新运行同一 thread_id 时，SQLite 持久化示例应继续记住先前内容。
- 对长对话，摘要示例应在阈值后仍能回答“我是谁/我喜欢什么”。
- 长期记忆示例应能在跨会话读取已存的用户画像。

### 常见问题
- 无法联网或无 API Key：请替换 `get_default_model()` 为假模型，或只运行 `semantic_search_store.py` 等离线示例。
- 持久化文件位置：短期/长期 SQLite 文件位于 `src/data/`，可删除以重置状态。
