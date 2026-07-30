# 03 Todo list

## 它是什么

Deep Agent 内置 `write_todos` 工具和 `todos` state，用于跟踪多步骤任务。前端不计算任务状态，只读取响应式的 `stream.values.todos`，每次 state 更新都会自动重渲染任务列表。

## 最小数据流

```text
模型调用 write_todos
  -> LangGraph 更新 state.todos
  -> useStream 收到新的 stream.values.todos
  -> TodoPanel 重新计算计数和进度
```

单个 todo 的真实结构来自当前安装的 `langchain.agents.middleware.todo.Todo`：

```ts
type Todo = {
  content: string;
  status: "pending" | "in_progress" | "completed";
};
```

前端核心代码只有一行：

```ts
const todos = stream.values?.todos ?? [];
```

## 本章示例

后端 `todo_agent` 被注册到本目录的 `langgraph.json`。它先创建三个任务，将第一项设为 `in_progress`，再逐项调用 `write_todos` 更新完整列表，直到全部为 `completed`。

启动服务：

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，切换到 `03 Todo list`，提交默认问题。预期右侧先显示“Agent 正在创建计划”，随后出现三项任务；进行中项为黄色，完成项为绿色，进度最终变为 `3/3`。

## 最小真实验证

```bash
uv run python - <<'PY'
from langgraph_sdk import get_sync_client

client = get_sync_client(url="http://127.0.0.1:2024")
for chunk in client.runs.stream(
    None,
    "todo_agent",
    input={"messages": [{"role": "human", "content": "请分三步解释 stream.values.todos"}]},
    stream_mode="values",
):
    todos = chunk.data.get("todos", [])
    if todos:
        print([todo["status"] for todo in todos])
PY
```

当前真实验证得到：

```text
in_progress, pending, pending
completed, in_progress, pending
completed, completed, in_progress
completed, completed, completed
```

## 常见误区

`write_todos` 每次提交的是完整列表，并会替换之前的 todo state，不是只提交发生变化的那一项。不要在前端复制一份独立状态、手动轮询或猜测任务进度，否则 UI 会与 LangGraph state 分叉。

Todo list 是执行进度，不是最终答案。Agent 将最后一项标为 `completed` 后，仍应继续输出用户真正需要的结果。

## 官方资料

- Deep Agents Todo list: `https://docs.langchain.com/oss/python/deepagents/frontend/todo-list`
- Deep Agents Frontend overview: `https://docs.langchain.com/oss/python/deepagents/frontend/overview`
