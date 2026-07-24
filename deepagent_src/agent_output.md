# Agent 输出方法

这几个方法专门给后续教学和真实 Agent 验证用。

## `pretty_print_messages(messages)`

把一组消息逐条 `pretty_print()`。

## `invoke_and_pretty_print(graph, inputs, config=None)`

先 `graph.invoke(...)`，再打印完整消息链。

## `stream_values_and_pretty_print(graph, inputs, config=None)`

实时流式输出。每次拿到新的 state，就只打印新增消息。

## `stream_updates(graph, inputs, config=None)`

打印每个节点的更新字典，适合看流程和调试。

## `stream_messages(graph, inputs, config=None)`

实时打印模型消息块。文本 chunk 会被合并成连续输出，不再每个 chunk 打一个标题。

## `stream_messages_and_updates(graph, inputs, config=None)`

同时打印节点更新和模型消息块。文本 chunk 会合并输出，适合教学时观察 Agent 跑到哪一步、哪个节点在输出。

## `stream_debug_trace(graph, inputs, config=None)`

全量调试输出。输入消息、连续的模型正文、每个 update、工具调用、工具返回、metadata 都会打印，适合排查为什么 Agent 没走到预期分支。

常见消息类型：

- `HumanMessage`：用户输入。
- `SystemMessage`：系统提示词。
- `AIMessage`：模型完整回复，通常能看到 `tool_calls`。
- `AIMessageChunk`：流式模型片段，可能只有一小段文本，也可能包含 `tool_call_chunks`。
- `ToolMessage`：工具执行结果，通常带 `tool_call_id`。
- `FunctionMessage`：旧版函数调用消息，现代工具调用里较少见。
- `RemoveMessage`：LangGraph 状态裁剪时用于删除历史消息。

调试时优先看 `stream_debug_trace()`；只想看用户可见回答时，用 `stream_messages()`。

## `stream_events(graph, inputs, config=None, version="v2")`

打印底层事件流，适合更细粒度的排错。
