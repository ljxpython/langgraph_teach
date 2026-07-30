# 12 Headless Tools

## 它是什么

Headless Tool 的参数由 Agent 决定，但实现运行在浏览器。后端通过 `interrupt()` 暂停同一次运行，`useStream` 找到同名的前端工具后自动执行并恢复，因此适合 `localStorage`、剪贴板、定位和文件选择器等浏览器能力。

## 后端协议

Python 后端仍注册普通工具，但工具内部不执行浏览器逻辑：

```python
@tool
def browser_memory_put(key: str, value: str, runtime: ToolRuntime) -> dict:
    return interrupt({
        "type": "tool",
        "tool_call": {
            "id": runtime.tool_call_id,
            "name": "browser_memory_put",
            "args": {"key": key, "value": value},
        },
    })
```

`type` 必须是 `tool`，`tool_call.id` 必须沿用当前调用 ID，名称与参数必须和前端定义一致。这里的 interrupt 是机器处理的协议，不是第 05 章让用户批准的 HITL 请求。

## 前端实现

`langchain` 的 schema-only `tool()` 只声明工具，`.implement()` 才挂载浏览器实现：

```tsx
import { tool } from "langchain";
import * as z from "zod";

const browserMemoryPut = tool({
  name: "browser_memory_put",
  description: "Store a teaching value in browser localStorage.",
  schema: z.object({ key: z.string(), value: z.string() }),
}).implement(async ({ key, value }) => {
  localStorage.setItem(`headless:${key}`, value);
  return { success: true, key, value };
});

const stream = useStream({
  apiUrl: API_URL,
  assistantId: "headless_tools",
  tools: [browserMemoryPut],
});
```

`useStream` 自动完成四步：识别 headless interrupt、按名称找到实现、执行浏览器函数、把结果提交回原运行。Headless interrupt 会从 `stream.interrupts` 中过滤掉，不能再渲染成人工审批卡。

### 当前本地版本的兼容处理

标准写法是把实现传给 `useStream({ tools: [...] })`。本项目验证时，`@langchain/react@1.0.29` 的自动恢复使用批量 `respondAll`，而当前最新 Python `langgraph-api@0.9.1` 只接受单个 `interrupt_id`，两端会报 `input.respond requires an interrupt_id`。

本章页面因此保留官方的解析与执行器，只显式完成单个 interrupt 的恢复：

```tsx
const stream = useStream({ apiUrl: API_URL, assistantId: "headless_tools" });

const pending = stream.getThread()?.interrupts.find(/* headless interrupt */);
const payload = parseHeadlessToolInterruptPayload(pending.payload);
const result = await handleHeadlessToolInterrupt(
  payload,
  [browserMemoryPut],
  onTool,
);
await stream.respond(
  { [result.toolCallId]: result.value },
  { interruptId: pending.interruptId, namespace: pending.namespace },
);
```

这不是另一套业务协议，只是把 SDK 自动流程的最后一步改为服务端已支持的单中断恢复。待 Python API 支持批量 `responses` 后，应删除兼容 effect，恢复标准的 `tools: [browserMemoryPut]`。

## 运行与预期

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，进入 `12 Headless Tools` 并提交默认内容。预期现象：

1. `browser_memory_put` 工具卡从 `running` 变为 `finished`。
2. `localStorage["headless:lesson-12"]` 出现提交内容。
3. 后端继续执行并输出“浏览器工具执行完成”。
4. “可见人工中断”保持为 `0`。

后端协议测试：

```bash
uv run python -m unittest deepagent_src.frontend_teach.tests.test_headless_tools
```

## 常见误区

- 不要把 API Key 或其他秘密返回给模型；浏览器工具结果会进入 Agent state。
- 工具名和参数 schema 必须前后端一致，否则前端无法匹配或后端调用失败。
- `.implement()` 必须返回 Promise；异常会作为工具错误恢复到运行。
- 浏览器 API 仍受权限和用户手势限制。剪贴板写入、定位、文件选择器不能假定永远可用。
- 不要手动调用 `stream.submit` 恢复 Headless Tool；当前 SDK 已自动处理。

## 与 Frontend HITL 的区别

| 机制 | 谁处理 | 典型用途 |
| --- | --- | --- |
| Frontend HITL | 用户点击批准、编辑或拒绝 | 高风险操作审批 |
| Headless Tools | 前端注册的函数自动执行 | 浏览器能力与本地状态 |

## 下一章

第 13 章学习 Human-in-the-loop：从通用 LangChain Frontend 协议角度处理多个 interrupt 与恢复决策。

## 官方资料

- Headless tools: `https://docs.langchain.com/oss/python/langchain/frontend/headless-tools`
