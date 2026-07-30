# 18 Join & Rejoin Streams

## 它是什么

Join & Rejoin 允许客户端离开正在运行的 Agent stream，但不停止服务端 run；稍后使用同一个 `threadId` 重新挂载流消费者，就能恢复遗漏消息和实时状态。它适用于页面跳转、移动端切后台、网络短暂中断和长时间任务。

## 四个核心机制

| API | 作用 |
| --- | --- |
| `threadId` | 标识需要重新加入的 LangGraph thread |
| `onThreadId` | 首次创建 thread 后持久化 ID |
| `stream.disconnect()` | 断开客户端连接，但不取消服务端 run |
| 使用相同 `threadId` remount | 重新附着到运行中或已完成的 thread |

当前安装的 `@langchain/react` v1 使用 v2 streaming protocol，remount 时会自动 re-attach，不需要旧版的 `joinStream` 或 `reconnectOnMount`。

## 保存 thread ID

没有稳定的 thread ID 就无法重新加入。本章同时保存到 React state 和 `sessionStorage`：

```tsx
const [threadId, setThreadId] = useState<string | null>(
  () => sessionStorage.getItem("langchain-join-rejoin-thread-id"),
);

const updateThreadId = useCallback((id: string | null) => {
  setThreadId(id);
  if (id) sessionStorage.setItem("langchain-join-rejoin-thread-id", id);
  else sessionStorage.removeItem("langchain-join-rejoin-thread-id");
}, []);
```

流消费者必须接收同一个 ID：

```tsx
const stream = useStream({
  apiUrl: "http://localhost:2024",
  assistantId: "join_rejoin",
  threadId,
  onThreadId: updateThreadId,
});
```

## 断开不是停止

离开页面时调用：

```tsx
await stream.disconnect();
```

它等价于 `stream.stop({ cancel: false })`：客户端不再接收事件，但服务端继续执行。不要在这里调用默认的 `stream.stop()`，因为它会取消当前 run。

## 重新加入

本章断开后卸载 `JoinRejoinStream`，点击“重新加入”时重新挂载，并继续传入持久化的 `threadId`：

```tsx
function rejoin() {
  setMountKey((key) => key + 1);
  setConnected(true);
}
```

如果 run 仍在执行，重新挂载后 `stream.isLoading` 会恢复为 `true`；如果 run 已结束，前端会直接取得最终 state 和断开期间产生的消息。

## 后端教学图

后端延时 2.5 秒，方便在完成前断开连接：

```python
async def join_rejoin_node(state: MessagesState) -> dict:
    await asyncio.sleep(2.5)
    prompt = next(
        message.content
        for message in reversed(state["messages"])
        if message.type == "human"
    )
    return {"messages": [AIMessage(content=f"后台运行完成：{prompt}")]}
```

延时只用于教学观察。Join/rejoin 的关键能力来自 LangGraph Agent Server 和前端 streaming protocol，不是这个节点自己实现的。

## 运行与预期

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，进入 `18 Join & Rejoin`：

1. 提交任务，状态变为 `running`。
2. 点击“断开但继续运行”，页面显示 `disconnected`。
3. 等待 2.5 秒以上，此时服务端 run 已经完成。
4. 点击“重新加入”，同一 thread 的用户消息和“后台运行完成”回复被恢复。

最小后端测试：

```bash
uv run python -m unittest deepagent_src.frontend_teach.tests.test_join_rejoin
```

## 常见误区

- `disconnect()` 是离开但继续执行；`stop()` 是取消当前 run，语义完全不同。
- 重新创建一个 thread 不是 rejoin，必须使用原 `threadId`。
- 只把 thread ID 放在组件局部变量里不可靠，组件卸载后会丢失。
- 当前 SDK v1 不需要旧版 `joinStream`；复制旧教程会引入多余或不存在的 API。
- 客户端显示的 `connected` 是 UI 状态，不等于服务端 run 状态；重连后要以服务端恢复结果为准。
- 生产应用应在页面可见性恢复时自动 rejoin，并处理 thread 已删除或超时的错误。

## 下一章

第 19 章学习 Time Travel：从历史 checkpoint 恢复状态、修改输入并重新执行后续图节点。

## 官方资料

- Join & rejoin streams: `https://docs.langchain.com/oss/python/langchain/frontend/join-rejoin`
