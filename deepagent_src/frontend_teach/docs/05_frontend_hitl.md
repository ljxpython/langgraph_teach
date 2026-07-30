# 05 Frontend HITL

## 它是什么

Frontend HITL 把有副作用的工具调用暂停在 checkpoint，让用户批准、修改或拒绝后再恢复原 run。后端决定哪些工具必须审批，前端只负责展示 `stream.interrupt` 并返回结构化 decision。

## 最小链路

```text
用户请求
  -> Agent 生成 send_release_announcement 工具调用
  -> interrupt_on 暂停并写入 checkpoint
  -> stream.interrupt.value 到达 React
  -> 用户 approve / edit / reject
  -> stream.respond({ decisions: [...] })
  -> 原 run 从暂停点继续
```

后端配置：

```python
hitl_agent = create_deep_agent(
    model=model,
    tools=[send_release_announcement],
    interrupt_on={
        "send_release_announcement": {
            "allowed_decisions": ["approve", "edit", "reject"],
        }
    },
)
```

当前 Python middleware 的 interrupt payload 使用蛇形字段：

```text
interrupt.value.action_requests
interrupt.value.review_configs
```

当前项目安装的 `@langchain/react` v1 使用 `respond` 恢复单个 interrupt：

```ts
await stream.respond(
  { decisions: [{ type: "approve" }] },
  { interruptId: stream.interrupt.id },
);
```

它仍然映射到底层 LangGraph `Command(resume=...)`。官网部分跨语言示例使用 `stream.submit(null, { command: { resume } })` 和驼峰 payload；实现时应以当前 SDK 类型和 Python 后端的真实 payload 为准。

## 三种决策

- `approve`：按 Agent 原参数执行工具。
- `edit`：使用 `edited_action` 替换工具参数后执行。
- `reject`：不执行工具，把拒绝原因作为工具结果交还 Agent。

`respond` 适用于用户代替工具直接提供结果，本章的通知工具有副作用，因此不使用它来表达拒绝。

## 运行

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，进入 `05 Frontend HITL` 并提交默认请求。预期先出现审批卡，工具不能在审批前产生成功结果；选择决策后 interrupt 清空，原 run 继续输出工具结果和最终回复。

## 常见误区

- 不要把审批实现成“先执行工具，再弹确认框”；interrupt 必须发生在工具执行之前。
- 恢复必须沿用同一个 thread 和 checkpoint，不能重新提交一条普通用户消息冒充恢复。
- Python HITL 的 Edit 字段是 `edited_action`，不是 `editedAction`。
- decision 数量必须和待审批 action 数量一致；并行审批需要 `respondAll`，不能逐个恢复同一 checkpoint。
- 拒绝有副作用的工具应使用 `reject` 并给清楚原因，不要使用代表成功工具结果的 `respond`。

## 教学边界

`send_release_announcement` 是确定性的本地教学工具，不发送真实网络通知。它验证的是真实 Agent、middleware interrupt、checkpoint 和恢复链路；生产环境再把工具函数替换为经过鉴权和审计的通知 API。

## 官方资料

- Deep Agents HITL: `https://docs.langchain.com/oss/python/deepagents/human-in-the-loop`
- Frontend HITL: `https://docs.langchain.com/oss/python/langchain/frontend/human-in-the-loop`
- React `useStream`: `https://reference.langchain.com/javascript/langchain-react/index/useStream`
