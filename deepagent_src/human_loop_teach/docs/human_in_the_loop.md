# Deep Agents Human-in-the-loop 学习路线

## 学习主题

这部分学习 Deep Agents 的 human-in-the-loop（HITL）：让敏感工具调用在执行前暂停，交给人类决定 approve、edit、reject 或 respond。艹，这不是 UI 弹窗魔法，本质是 LangGraph interrupt + checkpointer + `Command(resume=...)`。

## 课程大纲

### 00 覆盖清单与常用程度

目标：先知道 HITL 文档里哪些能力是高频主线，哪些是生产治理或高级分支。

### 01 基础中断与 approve

目标：理解 `interrupt_on`、`checkpointer`、`thread_id`、`version="v2"` 和 approve 恢复流程。

### 02 decision types

目标：理解 `approve`、`edit`、`reject`、`respond` 的区别，尤其 reject 和 respond 别混用。

### 03 条件中断

目标：理解 `when` predicate 如何按工具参数决定是否暂停。

### 04 多工具批量审批

目标：理解多个待审工具会合并成一个 interrupt，恢复时 decisions 必须按 action 顺序提供。

### 05 subagent interrupts

目标：理解 subagent 可以有自己的 `interrupt_on`，并且中断会冒泡给父 Agent 处理。

### 06 filesystem permission interrupts

目标：理解内置文件系统权限可以用 `mode="interrupt"` 触发同一套 HITL 审批。

### 07 综合案例

目标：把工具审批、参数编辑、文件权限拒绝、同线程恢复串成一个真实流程。

## 最常用的部分

高频必学：

- `interrupt_on={tool_name: True | config | False}`
- `checkpointer=MemorySaver()`
- 同一个 `configurable.thread_id`
- `result.interrupts`
- `Command(resume={"decisions": [...]})`
- `approve` / `reject`

中频常用：

- `edit` 工具参数
- 条件中断 `when`
- 多工具批量审批
- 文件系统 `FilesystemPermission(mode="interrupt")`

高级或低频：

- `respond`，只适合 ask-user 类工具
- subagent 内部中断
- tool 内直接调用 `interrupt()`
- 生产 UI、审计记录、权限系统集成

## HITL 执行链路

```text
用户请求
-> Agent 生成工具调用
-> HumanInTheLoopMiddleware 检查 interrupt_on / permissions
-> 命中规则：返回 GraphOutput(interrupts=...)
-> 应用展示 action_requests 和 review_configs
-> 人类给 decisions
-> agent.invoke(Command(resume={...}), same_config, version="v2")
-> 工具执行或被跳过
-> Agent 继续生成最终回答
```

## 本地版本

- `deepagents==0.6.12`
- 示例通过 `_model.py` 复用项目已有 `deepagent_src.llms.get_gpt_model()`，会执行真实 Agent 调用。
- 示例使用安全工具：不会真实删除文件、不会真实发邮件。
- 文件系统章节使用 Deep Agents 虚拟文件系统，不写真实 `/secrets`。
- 官方资料来源：`https://docs.langchain.com/oss/python/deepagents/human-in-the-loop`

## 当前章节

- [00 覆盖清单与常用程度](00_coverage_and_usage.md)
- [01 基础中断与 approve](01_basic_approve.md)
- [02 decision types](02_decision_types.md)
- [03 条件中断](03_conditional_interrupt.md)
- [04 多工具批量审批](04_multiple_tool_calls.md)
- [05 subagent interrupts](05_subagent_interrupt.md)
- [06 filesystem permission interrupts](06_filesystem_permission_interrupt.md)
- [07 综合案例](07_comprehensive_case.md)

