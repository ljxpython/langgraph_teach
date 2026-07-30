# 第六章：Rubric 与 Evaluation

Rubric 是把“做好”写成可判断标准，避免只凭感觉说 Agent 输出不错。`RubricMiddleware` 在一次 Deep Agent 运行内做 runtime LLM-as-a-judge：工作 Agent 输出后，独立 grader 依据 rubric 给出 `satisfied`、`needs_revision` 或 `failed`；只有 `needs_revision` 才会把反馈注入对话并让 Agent 再改。

## 最小代码

代码在 `deepagent_src/advanced_teach/06_rubric_evaluation.py`。

例子要求 Agent 输出固定标题和两条 bullet；grader 用三条 rubric 检查标题、bullet 数量和关键字段。`on_evaluation` 收集每次 grader 结果，测试再断言三条标准都通过。

```python
agent = create_deep_agent(
    model=get_gpt_model(disable_tool_streaming=True),
    middleware=[
        RubricMiddleware(
            model=get_gpt_model(disable_tool_streaming=True),
            max_iterations=2,
            on_evaluation=on_evaluation,
        )
    ],
    checkpointer=InMemorySaver(),
)

result = agent.invoke(
    {"messages": [HumanMessage(content="...")], "rubric": RUBRIC},
    config={"configurable": {"thread_id": "rubric-teach"}},
)
```

`checkpointer` 和稳定 `thread_id` 不能省。revision 会通过 LangGraph 状态恢复执行；没有持久化，运行时 self-evaluation 无法安全暂停、反馈、继续。

## 运行命令

```bash
uv run python -m deepagent_src.advanced_teach.06_rubric_evaluation
```

这会触发两次真实 LLM 调用：一次工作 Agent，一次 grader。若 grader 判定 `needs_revision`，会继续调用工作 Agent，最多到 `max_iterations=2`。

## 预期现象

```text
grader iteration 0: satisfied
final: Deployment readiness
- thread_id: ...
- context: ...
criteria: [
  {"name": "...", "passed": True},
  {"name": "...", "passed": True},
  {"name": "...", "passed": True}
]
rubric runtime evaluation real call ok
```

本例第一稿已经满足 rubric，所以只会看到一次 grader。真正缺项时，grader 返回 `needs_revision`，中间件把每项 `gap` 作为反馈注入，Agent 再生成一稿。

## Runtime Rubric 与离线 Evaluation

| 机制 | 何时运行 | 目标 | 成本与结果 |
| --- | --- | --- | --- |
| `RubricMiddleware` | 单次用户运行内部 | 让当前结果达标，必要时立即修订 | 增加 grader 调用；会改变本次最终输出 |
| LangSmith offline evaluation | 发布前或回归测试 | 在 dataset 上比较 Agent 版本 | 不改变线上单次输出；用于实验、基准和回归 |
| LangSmith online evaluation | 生产 trace 之后 | 监控质量、安全、异常 | 不阻塞主要交互；用于采样监控和反馈闭环 |

工程上先用确定性断言覆盖硬规则，例如文件是否存在、工具是否调用、JSON 是否可解析；再用 rubric 或 LLM judge 判断表达质量、完整性和是否符合业务意图。不要把本该用代码判断的东西全交给 LLM judge，贵而且不稳定。

## 当前版本注意

`RubricMiddleware` 在 `deepagents 0.7.0b2` 仍是 beta。本项目的当前 GPT provider 配置首次使用默认 grader prompt 时返回了不符合 `GraderResponse` 的字段，因此示例额外明确了 grader 必须返回 `result`、`explanation`、`criteria[{name, passed, gap?}]`。这是当前 provider 的结构化输出兼容性处理；仍以本地真实运行结果为准。

## 常见误区

不要把 rubric 写成“回答要好”“内容要专业”这种空话。每一条都应能被判定，例如“恰好三条 bullet”“包含订单号与金额”“所有引用都来自工具结果”。

也不要把 `max_iterations` 设得很大。它是质量保护，不是无限自我反思开关；通常 1-3 次足够，超过后应记录 trace，补 prompt、工具或确定性校验。

## 验证

1. `on_evaluation` 至少收到一次事件。
2. grader 返回 `satisfied`。
3. 三条 rubric criterion 都是 `passed=True`。
4. 最终文本有准确标题、两条 bullet、`thread_id` 与 `context`。

官方依据：`/oss/python/deepagents/rubric` 定义了 runtime `RubricMiddleware`、`needs_revision` 回环和 `max_iterations`；`/langsmith/evaluation` 定义了离线 dataset/experiment 与线上 trace evaluation 的工作流。
