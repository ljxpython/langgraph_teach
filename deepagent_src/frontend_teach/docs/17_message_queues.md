# 17 Message Queues

## 它是什么

Message Queues 允许用户在当前 Agent run 尚未结束时继续提交消息。`multitaskStrategy: "enqueue"` 把这些提交保存在客户端 FIFO 队列，当前 run 结束后由 SDK 按提交顺序自动执行。它解决的是“用户连续追加任务”问题，不是并行执行多个 run。

## 最小实现

当前安装的 `@langchain/react` 已经包含队列协调器，不需要自己维护 React 数组：

```tsx
const stream = useStream({
  apiUrl: "http://localhost:2024",
  assistantId: "message_queues",
});
const queue = useSubmissionQueue(stream);

stream.submit(
  { messages: [{ type: "human", content }] },
  { multitaskStrategy: "enqueue" },
);
```

`queue.entries` 是尚未开始的提交，`queue.size` 是等待数量。当前 run 完成后，SDK 会取出第一项执行，再继续下一项。

## 取消与停止

两个动作不能混为一谈：

```tsx
await queue.cancel(entry.id); // 只移除尚未开始的这一项
await queue.clear();          // 只清空所有尚未开始项
await stream.stop();          // 中断当前正在执行的 run
```

一旦某项已经从队列进入运行状态，它就不再属于 `queue.entries`，此时只能停止当前 run。

## 后端为什么延时

本章后端是确定性教学图，节点等待 1.2 秒后返回：

```python
async def message_queues_node(state: MessagesState) -> dict:
    await asyncio.sleep(1.2)
    prompt = next(
        message.content
        for message in reversed(state["messages"])
        if message.type == "human"
    )
    return {"messages": [AIMessage(content=f"已处理：{prompt}")]}
```

延时仅用于让排队状态在浏览器中可观察；队列机制在前端 SDK，不在这个节点里。

## 运行与预期

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173` 并进入 `17 Message Queues`：

1. 提交第一项，在状态显示 `running` 时立即提交第二、第三项。
2. 右侧显示两个 pending 项，顺序与提交顺序一致。
3. 点击某项“取消”只删除该等待项；“清空等待项”删除所有 pending 项。
4. 当前项完成后，剩余项按 FIFO 自动运行。

后端最小测试：

```bash
uv run python -m unittest deepagent_src.frontend_teach.tests.test_message_queues
```

## 常见误区

- 默认提交策略不是排队；未指定 `enqueue` 时，常见默认策略 `rollback` 会用新提交替换当前 run。
- 不要在 `stream.isLoading` 时禁用输入与提交按钮，否则用户根本无法排队。
- 不要自己复制一份队列状态；`useSubmissionQueue(stream)` 已是 SDK 的真实状态源。
- `cancel` 和 `clear` 不会停止当前 run，`stop` 也不会自动清空等待项。
- 这是客户端 pending queue。页面卸载或客户端状态丢失时，不应把它误认为服务端持久任务队列。

## 下一章

第 18 章学习 Join and Rejoin：页面离开后重新加入仍在执行的 run，并恢复流式状态。

## 官方资料

- Message queues: `https://docs.langchain.com/oss/python/langchain/frontend/message-queues`
