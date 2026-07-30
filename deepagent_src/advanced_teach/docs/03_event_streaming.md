# 第三章：Event Streaming

Event Streaming 是把一次 Agent 运行拆成连续事件：模型消息、工具开始/结束、状态快照和最终输出都会按运行过程吐出来。它解决的是前端不能只等最终答案的问题，IDE、聊天窗口、工具执行面板都需要边跑边更新。Deep Agents 继承 LangGraph 的流式协议，并额外提供面向子代理的 `subagents` 投影。

## 最小代码

代码在 `deepagent_src/advanced_teach/03_event_streaming.py`。

这个例子只做一件事：让真实 LLM 必须调用 `echo_topic` 工具，然后通过 `agent.stream_events(..., version="v3")` 收集同一次运行里的 `messages`、`tools`、`values` 和最终 `output`。

关键逻辑：

```python
stream = agent.stream_events(input, version="v3")

for event in stream:
    method = event.get("method")
    if method == "messages":
        # AIMessage，可能包含 tool_calls，也可能包含最终文本
        ...
    if method == "tools":
        # tool-started / tool-finished
        ...

output = stream.output
```

这里直接迭代原始事件，而不是同时消费多个 projection。原因很简单：`GraphRunStream` 的 projection 是单消费者模型，同一条流不要被多个循环抢着读，复杂 UI 再按需要用 `interleave(...)` 或 `tee(...)`。

## `stream_events`、`stream`、`astream` 的关系

这几个 API 都是在驱动同一个 LangGraph/Deep Agents 运行，只是返回形态不同。`stream` / `astream` 是 stream-mode API：你传 `stream_mode="updates"`、`"values"`、`"messages"`、`"custom"` 等模式，然后自己按 chunk 类型分支处理。`stream_events` / `astream_events` 是 Event Streaming API：它返回 run stream 对象，直接给你 `messages`、`tool_calls`、`values`、`subagents`、`output` 这些投影。

| API | 同步/异步 | 返回什么 | 适合场景 | 当前建议 |
| --- | --- | --- | --- | --- |
| `agent.stream(...)` | 同步 | `Iterator`，按 `stream_mode` 吐 chunk | 旧代码、调试 LangGraph runtime、只要某个 stream mode | 能用，但新前端优先不用它 |
| `agent.astream(...)` | 异步 | `AsyncIterator`，按 `stream_mode` 吐 chunk | async 服务端、WebSocket/SSE 中直接异步转发 | 和 `stream` 一样，是 stream-mode 路线 |
| `agent.stream_events(..., version="v3")` | 同步 | `GraphRunStream`，有 typed projections 和原始事件 | 本地脚本、同步服务端、教学验证、前端协议整理 | 新应用和前端优先选它 |
| `agent.astream_events(..., version="v3")` | 异步 | `AsyncGraphRunStream`，异步 typed projections | FastAPI、SSE、WebSocket、并发消费多个投影 | 生产服务端最常用 |

它们的关系可以这么记：`stream/astream` 是“按模式吐运行片段”，`stream_events/astream_events` 是“按语义通道吐运行事件”。官方新文档更推荐新应用使用 Event Streaming，因为前端通常关心的是消息、工具、状态、子代理这些语义通道，而不是自己解析一堆 `stream_mode` chunk。

同步和异步只是消费方式不同，不改变 Agent 本身：脚本里用 `stream_events` 简单；FastAPI 这类异步后端用 `astream_events`，这样不会堵住事件循环。`stream` 和 `astream` 仍然有价值，尤其是你已经有基于 `stream_mode="updates"`、`stream_mode="messages"` 的旧代码，或者你正在调 LangGraph 底层 stream mode。

一个最小对照：

```python
# stream-mode：自己根据 chunk 类型分支
for chunk in agent.stream(input, stream_mode=["messages", "updates"], version="v2"):
    print(chunk["type"], chunk["data"])

# event-streaming：直接消费语义投影
stream = agent.stream_events(input, version="v3")
for message in stream.messages:
    print(message.text)
final_state = stream.output
```

## 运行命令

```bash
uv run python -m deepagent_src.advanced_teach.03_event_streaming
```

这会触发一次真实 LLM 调用，使用项目里的 `get_gpt_model(disable_tool_streaming=True)`。如果没有 `CHATGPT_API_KEY` 或 `CHATGPT_API_URL`，真实调用会失败。

## 预期现象

输出里应该能看到：

```text
methods: values, messages, values, tools, tools, values, messages, values
tool_calls: echo_topic
tool_results: 工具已收到主题: event streaming
final: ... event streaming ... 前端 ...
message_count: 4
event streaming real call ok
```

顺序可能随 beta 版本略有变化，但核心应该成立：先有状态快照，再有模型 tool call，再有工具事件，最后有模型最终消息。

## 常见误区

不要把 `stream.messages`、`stream.tool_calls`、`stream.values` 当成可以随便重复遍历的列表。`GraphRunStream` 是运行中的流，projection 是单消费者；你遍历一次就等于驱动 Agent 往前跑。前端要多面板同时显示时，用官方的并发消费方式，或者在自己的事件总线里把原始事件分发出去。

另一个误区是把 `stream.subgraphs` 当成产品 UI。Deep Agents 文档更推荐用户界面使用 `stream.subagents`，因为它表达的是“代理委派任务”，不是 LangGraph 内部节点结构。

## 验证

本章验证点：

1. `messages` 事件出现，说明模型消息可流出。
2. `tools` 事件出现，说明工具开始/结束可被前端观察。
3. `values` 事件出现，说明状态快照可被观察。
4. 最终 `stream.output` 能拿到完整 state。
5. 断言 `echo_topic` 被真实调用，最终文本包含 `event streaming` 和 `前端`。

官方依据：`/oss/python/deepagents/event-streaming` 说明 Deep Agents 使用 `agent.stream_events(input, version="v3")`，并暴露 `messages`、`tool_calls`、`values`、`subagents`、`output`、`interleave(...)` 等投影；其中 `subagents` 是 Deep Agents 面向产品 UI 的重点能力。
