# Deep Agents Context Engineering 学习路线

## 学习主题

这部分学习 Deep Agents 的 context engineering：把正确的信息、工具和持久化位置放到正确的上下文层里，让 Agent 长任务里不迷路、不爆上下文、不把用户隔离搞穿。

艹，先分清楚：context engineering 不是“把所有资料塞进 prompt”。真正要学的是哪些信息启动时加载，哪些运行时传入，哪些交给 state、filesystem、subagent 或 long-term memory 管。

## 课程大纲

### 01 Input context：启动时上下文

目标：理解 `system_prompt`、`memory`、`skills` 和 tool metadata 怎么进入 Agent 的启动上下文。

### 02 Runtime context：每次调用的静态配置

目标：理解 `context_schema` 和 `invoke(..., context=...)` 适合传 user_id、role、API key 这类每轮固定信息。

### 03 Custom state schema：可变图状态

目标：理解 `state_schema` 适合保存 Agent 生命周期内会变化、要 checkpoint 的数据。

### 04 Context compression：自动压缩与手动 compact

目标：理解 Deep Agents 内置 offloading 和 summarization，并学会给 Agent 加 `compact_conversation` 工具。

### 05 Subagents：上下文隔离

目标：理解重活交给 subagent 后，主 Agent 只拿最终总结，避免工具日志把主上下文撑爆。

### 06 综合案例：长期记忆

目标：把 `CompositeBackend`、`StoreBackend`、`/memories/` 和系统提示词串起来，理解跨 thread 持久化信息放哪里。

## 推荐学习顺序

1. 先学 Input context，知道什么东西一启动就进 prompt。
2. 再学 Runtime context 和 State，别把静态配置和可变状态混成一锅。
3. 然后学 compression 和 subagent，解决长任务上下文膨胀。
4. 最后学 long-term memory，把跨会话信息落到 `/memories/`。

## 本地版本

- `deepagents==0.6.12`
- 示例通过本目录 `_model.py` 复用项目已有 `deepagent_src.llms.get_gpt_model()`，会执行真实 Agent 调用。
- 示例通过 `deepagent_src.agent_output.invoke_and_pretty_print()` 打印完整消息链，能看到用户消息、AI 消息、工具调用和工具结果。
- 运行前需要配置真实模型环境变量：`CHATGPT_API_KEY` 和 `CHATGPT_API_URL`。
- 官方资料来源：`https://docs.langchain.com/oss/python/deepagents/context-engineering`

## 当前章节

- [01 Input context：启动时上下文](01_input_context.md)
- [02 Runtime context：每次调用的静态配置](02_runtime_context.md)
- [03 Custom state schema：可变图状态](03_custom_state_schema.md)
- [04 Context compression：自动压缩与手动 compact](04_context_compression.md)
- [05 Subagents：上下文隔离](05_context_isolation_subagents.md)
- [06 综合案例：长期记忆](06_long_term_memory_case.md)
