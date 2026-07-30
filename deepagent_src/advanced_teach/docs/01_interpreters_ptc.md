# 01 Interpreter 与 PTC

Interpreter 是 Deep Agents 的一个轻量代码执行层：模型不只发普通工具调用，还可以写一段 JavaScript 让运行时执行。PTC 是 Programmatic Tool Calling，它把允许的工具暴露到 Interpreter 的 `tools` 命名空间里，让代码循环、分支、并行调用工具。它解决的问题是：一批中间工具结果不必每一步都回到模型上下文，最后只把聚合结果交回模型。

## 最小代码

本章代码在：

```text
deepagent_src/advanced_teach/01_interpreters_ptc.py
```

核心配置只有两处：

```python
from langchain_quickjs import CodeInterpreterMiddleware

agent = create_deep_agent(
    model=get_gpt_model(disable_tool_streaming=True),
    tools=[lookup_plan, discount_amount],
    middleware=[CodeInterpreterMiddleware(ptc=["lookup_plan", "discount_amount"])],
    subagents=[],
)
```

这里 `lookup_plan` 和 `discount_amount` 仍然是普通 LangChain tool。区别在于：加了 `CodeInterpreterMiddleware(ptc=[...])` 后，模型可以在 `eval` 里写 JavaScript，并通过 `tools.lookupPlan(...)`、`tools.discountAmount(...)` 调这些工具。

## 运行命令

```bash
uv run python -m deepagent_src.advanced_teach.01_interpreters_ptc
```

预期现象：

1. 会发生一次真实 LLM 调用。轨迹里应该能看到模型调用 `eval`，而不是直接连续调用 `lookup_plan` / `discount_amount`。
2. `eval` 里的 JavaScript 会通过 `tools.lookupPlan(...)` 和 `tools.discountAmount(...)` 批量处理三个套餐。
3. 最终输出会包含 `starter`、`team`、`enterprise` 三个套餐的原价和 20% 折后价。

## 常见误区

最容易搞混的是把 Interpreter 当成 sandbox。Interpreter 默认没有文件系统、shell、网络、包管理器和系统时间；它只是 QuickJS 内存运行时。需要跑命令、装依赖、改真实文件时，用 sandbox；需要循环、分支、聚合中间工具结果时，用 Interpreter/PTC。

还有一个安全边界要记住：官方文档说明 PTC 通过 interpreter bridge 执行，当前不会走普通 tool calling 的逐工具 `interrupt_on` 审批流程。所以能进 PTC allowlist 的工具必须提前收窄，别把危险工具一股脑放进去，艹，这玩意放错就是自己给自己挖坑。

## 与普通工具调用的区别

普通 tool calling 的节奏是：模型决定调用哪些工具，工具结果回到模型，模型再决定下一步。PTC 的节奏是：模型先写一段代码，代码在 Interpreter 里批量调用工具、过滤和聚合结果，模型只看到最终返回。

所以本章判断是否跑通，不看工具函数能不能被 Python 直接调用，而看真实 Agent 轨迹里有没有 `eval` 工具调用。

## 版本说明

官方文档要求：

```text
langchain-quickjs>=0.2.0
Python >=3.11
```

本项目已经确认升级到 `deepagents[quickjs]==0.7.0b2`，`uv.lock` 中解析到 `langchain-quickjs==0.3.4`。示例仍保留依赖门控，这样换到新环境时不会用一个晦涩的 `ModuleNotFoundError` 把人整懵。

升级后实测关键签名：

```text
deepagents 0.7.0b2
CodeInterpreterMiddleware(..., ptc: list[str | BaseTool] | None = None, mode: "thread" | "turn" | "call" | None = None, ...)
FilesystemMiddleware(..., tools: list["ls" | "read_file" | "write_file" | "edit_file" | "delete" | "glob" | "grep" | "execute"] | "all" | None = None, ...)
```
