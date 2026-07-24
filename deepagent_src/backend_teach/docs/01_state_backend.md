# 01 StateBackend

## 学习目标

理解一句话：`StateBackend` 把文件保存在当前 thread 的 LangGraph state 中。

## 示例

代码见 [`../01_state_backend.py`](../01_state_backend.py)。

示例只做两件事：

1. 在 thread `state-backend-demo` 中写入 `/note.txt`。
2. 使用同一个 thread 再次调用 Agent，读取 `/note.txt`。

关键配置：

```python
agent = create_deep_agent(
    model=gpt_model,
    backend=StateBackend(),
    checkpointer=InMemorySaver(),
)
config = {"configurable": {"thread_id": "state-backend-demo"}}
```

- `StateBackend()`：文件进入 Agent state。
- `InMemorySaver()`：保存每次运行后的 state。
- `thread_id`：决定读取哪一个 thread 的 state。

## 运行

在项目根目录执行：

```bash
uv run python deepagent_src/backend_teach/01_state_backend.py
```

运行会调用模型两次，产生 API 费用。

## 观察重点

第二次调用能读到第一次写入的文件，因为两次调用使用了同一个 `thread_id`。

如果把第二次调用的 `thread_id` 改掉，它就读不到原 thread 中的 `/note.txt`。

## 生命周期

当前示例使用 `InMemorySaver`：

- 同一 Python 进程内可以跨多次调用保存文件。
- 程序退出后，内存 checkpoint 消失。
- 需要重启后继续保存时，应换成持久化 checkpointer。

## StateBackend 适合什么

- Agent 临时草稿
- 中间分析结果
- 大工具输出的临时存放
- supervisor 与 subagent 共享本次 thread 的文件

不适合跨用户、跨 thread 的长期记忆；这种需求后面学习 `StoreBackend`。
