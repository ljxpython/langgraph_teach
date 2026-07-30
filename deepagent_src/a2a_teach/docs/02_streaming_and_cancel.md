# 第二章：A2A 流式状态、超时和取消

代码在 `deepagent_src/a2a_teach/02_streaming_and_cancel.py`。

第 1 章的任务只有最终结果。本章用 `SlowExecutor` 制造一个可控的长任务，验证 A2A 的三件事：

1. Executor 先发布初始 `Task`，再用 `TaskUpdater.start_work()` 发布 `working` 状态。
2. Executor 发布一个进度 artifact；它不是最终结果，`last_chunk=False` 表示后面还有内容。
3. Client 只等待 250ms。超时后显式发送 `CancelTaskRequest`，并确认服务端执行器的 `cancel()` 被调用、Task 进入 `TASK_STATE_CANCELED`，且不会产生 `result` 最终 artifact。

```bash
uv run python -m deepagent_src.a2a_teach.02_streaming_and_cancel
```

预期输出类似：

```text
stream_event: task
stream_event: status_update
status: TASK_STATE_WORKING
stream_event: artifact_update
client_wait: timed out after 250ms
cancel_state: TASK_STATE_CANCELED
a2a streaming, timeout, and cancel ok
```

## 超时不等于取消

`asyncio.timeout(0.25)` 只限制本地 Client 等待流的时间；它不会可靠地停止远端工作。超时后必须把取得的 `task_id` 传给 `CancelTaskRequest`，远端 `AgentExecutor.cancel()` 必须发布 `TASK_STATE_CANCELED`。

SDK 在收到取消请求时会取消正在执行的 `execute()` 协程，然后调用 `cancel()`。所以 `execute()` 中要让长耗时操作能够响应取消，例如 `await` 可取消的网络请求、子进程管理或支持取消的模型流。已发布的 progress artifact 会保留在 Task 历史中，取消只阻止后续工作；不能只在 Client 超时后丢弃 HTTP 连接，否则服务端任务可能继续消耗资源。

本章的慢任务使用 `asyncio.sleep(5)`，这是为了稳定验证 A2A 协议事件和取消生命周期，不代表已经验证了某个 LLM 提供商的 generation cancel。对真实 Deep Agent，要把模型流、工具调用和子进程的取消策略单独接入并压测。

## 何时使用流式 A2A

流式调用适合远端任务持续数秒以上、调用方需要进度或需要随时取消的场景。短小且只关心最终结果的远端调用，使用第 1 章的非流式模式更简单。
