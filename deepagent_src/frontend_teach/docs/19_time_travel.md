# 19 Time Travel

## 它是什么

Time Travel 是从 thread 的历史 checkpoint 恢复状态，再重新执行后续图节点。它适合调试、审计和人工恢复，不是简单地重新发送一条聊天消息。

LangGraph 在图状态变化后保存 checkpoint。前端通过 checkpoint 能看到当时的完整状态，以及下一步准备执行什么。

| 字段 | 含义 |
| --- | --- |
| `checkpoint` | checkpoint 标识，恢复时使用 `checkpoint_id` |
| `values` | 当时的完整 graph state |
| `tasks` | 当前 checkpoint 关联的待处理任务 |
| `next` | 接下来准备执行的节点；空数组表示图已结束 |

## 后端教学图

本章使用最小两节点图：

```text
START -> draft -> finalize -> END
```

`draft` 保存草稿，`finalize` 每次执行都会生成不同的六位标识。因此，从 `next = ["finalize"]` 的 checkpoint 重放后，可以直接观察到后续节点确实重新执行了。

```python
class TimeTravelState(MessagesState):
    draft: str


async def time_travel_draft_node(state: TimeTravelState) -> dict:
    prompt = next(
        message.content
        for message in reversed(state["messages"])
        if message.type == "human"
    )
    return {"draft": f"草稿：{prompt}"}
```

## 获取历史

`useStream` 不会把全部 checkpoint 历史直接放进 `stream.messages`，需要显式查询：

```tsx
const history = await stream.client.threads.getHistory(threadId, { limit: 50 });
```

本章在 run 空闲后刷新历史，并展示 checkpoint ID、任务名、`next` 和消息数量。选择一项后，右侧直接检查 `values`。

## 从 checkpoint 重放

确认 checkpoint 仍有后续节点后，调用：

```tsx
stream.submit({}, { forkFrom: checkpointId });
```

当前项目安装的 `@langchain/react` 类型要求 `forkFrom` 是 checkpoint ID 字符串。官方页面部分示例仍写成 `{ forkFrom: { checkpointId } }`，遇到这种版本差异应以本地 TypeScript 类型和构建结果为准。

重放不会删除旧 checkpoint，而是从历史状态产生一条新执行路径。页面会在操作前使用 `window.confirm` 明确确认。

## 与 Branching Chat 的区别

第 14 章 Branching Chat 从消息对应的父 checkpoint 编辑问题或重新生成回答，面向普通聊天用户。Time Travel 则展示完整 checkpoint 时间线与 graph state，面向调试、审计和运维恢复。两者底层都使用 checkpoint，但产品语义不同。

## 运行与预期

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，进入 `19 Time Travel`：

1. 提交默认问题，得到带六位标识的最终回答。
2. 在时间线选择 `next: finalize` 的 checkpoint。
3. 检查右侧 `values` 中的 `draft`。
4. 点击“从这里重放”并确认。
5. 新最终回答的六位标识不同，原 checkpoint 仍保留。

最小测试：

```bash
uv run python -m unittest deepagent_src.frontend_teach.tests.test_time_travel
```

## 常见误区

- `stream.messages` 不是 checkpoint 历史，历史需要 `getHistory()`。
- 结束态的 `next` 为空，没有后续节点可重放。
- 重放产生新路径，不会原地覆盖或删除旧历史。
- 不要把整份敏感 state 无条件展示给所有用户；生产环境需要权限检查和字段脱敏。
- 历史较长时必须分页，不要固定一次加载全部 checkpoint。
- 恢复操作可能重复外部副作用，生产环境必须确认并保证工具调用具备幂等性。

## 下一章

第 20 章学习 Generative UI：让 Agent 的结构化输出选择并驱动前端组件。

## 官方资料

- Time travel: `https://docs.langchain.com/oss/python/langchain/frontend/time-travel`
