# 16 Structured Output

## 它是什么

Structured Output 让 Agent 返回符合预定义 schema 的对象，前端据此渲染表格、指标或领域组件，而不是解析自由文本。本章使用最终 `AIMessage.tool_calls[0].args` 承载学习计划，并在浏览器中用 Zod 验证后再渲染。展示型 tool call 只传递结果，不执行工具逻辑。

## 后端响应

教学图不调用模型，直接返回一个确定性的结构化 tool call：

```python
AIMessage(
    content="",
    tool_calls=[
        {
            "name": "render_learning_plan",
            "args": {
                "topic": "学习结构化输出",
                "level": "intermediate",
                "objectives": ["识别结构化响应"],
                "lessons": [
                    {"title": "定义 schema", "duration_minutes": 20}
                ],
                "total_minutes": 20,
            },
            "id": "learning-plan-...",
            "type": "tool_call",
        }
    ],
)
```

这个 tool call 是最终响应协议，不应该连接 `ToolNode`。如果执行它，后端会等待一个没有实际实现的工具，并把本应展示的数据错误地当成待处理动作。

## 前端 schema

TypeScript 类型会在编译后消失，所以不能直接写 `call.args as LearningPlan`。本章复用项目已有 Zod，在运行时校验服务端数据：

```tsx
const LearningPlanSchema = z.object({
  topic: z.string().min(1),
  level: z.enum(["beginner", "intermediate", "advanced"]),
  objectives: z.array(z.string().min(1)).min(1),
  lessons: z.array(z.object({
    title: z.string().min(1),
    duration_minutes: z.number().int().positive(),
  })).min(1),
  total_minutes: z.number().int().positive(),
});

type LearningPlan = z.infer<typeof LearningPlanSchema>;
```

## 提取最后一个结果

对话可能有多轮，必须从后往前找最后一条包含目标 tool call 的 AIMessage：

```tsx
for (const message of [...messages].reverse()) {
  const toolCalls = message.tool_calls ?? message.toolCalls ?? [];
  const call = toolCalls.find((item) => item.name === "render_learning_plan");
  if (!call) continue;

  const parsed = LearningPlanSchema.safeParse(call.args);
  if (parsed.success) return parsed.data;
}
```

不能使用第一条 AIMessage，也不能默认使用第一个任意 tool call；真实 Agent 可能在结构化响应前调用搜索、数据库等普通工具。

## 流式边界

模型生成 tool arguments 时，SDK 可能先收到不完整参数。页面在 `stream.isLoading` 为 `true` 时显示生成状态；运行完成后才把 schema 错误展示给用户，避免把正常的部分 JSON 当成失败。

本章等待完整对象后整体渲染。需要渐进展示时，可以使用 `schema.partial()` 校验已到达字段，但数组元素和嵌套对象仍要逐层防御，不能只判断顶层 key 存在。

## 运行与预期

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173` 并进入 `16 Structured Output`：

1. 输入学习主题并点击“生成”。
2. 左侧保留请求，右侧显示经过验证的主题、级别、总时长、目标和课程安排。
3. 页面不显示原始 JSON，也不会执行 `render_learning_plan` 工具。

后端最小测试：

```bash
uv run python -m unittest deepagent_src.frontend_teach.tests.test_structured_output
```

## 与 Agent `response_format` 的关系

不同 Agent 封装可能把结构化结果放入 graph state 的 `structured_response`，也可能通过最终 tool call 暴露。前端必须按实际部署的 state schema 和消息协议选择一种稳定契约；本章严格跟随 LangChain Frontend 页面演示的 `AIMessage.tool_calls[].args` 模式。

## 常见误区

- 不要用 `JSON.parse(message.text)` 解析结构化结果。
- 不要只做 TypeScript 类型断言，网络数据必须运行时验证。
- 不要把展示型 tool call 交给 `ToolNode`。
- 不要在流式参数未完成时立即显示 schema 错误。
- 不要设计无必要的深层 schema，嵌套越深越难渐进渲染和兼容升级。

## 下一章

第 17 章学习 Message Queues：当前 run 执行时继续接收用户输入，并明确排队、合并与取消语义。

## 官方资料

- Structured output: `https://docs.langchain.com/oss/python/langchain/frontend/structured-output`
