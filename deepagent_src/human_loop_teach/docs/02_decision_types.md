# 02 decision types

## 它是什么

HITL 的 decision 决定人类如何处理待执行工具。`approve` 直接执行，`edit` 修改参数后执行，`reject` 跳过工具并告诉模型被拒绝，`respond` 用人类回复作为工具结果。它解决的问题是：不同风险操作需要不同审批动作。

## 常用程度

高：`approve`、`reject`。

中高：`edit`。

中低：`respond`，只适合 ask-user 类工具。

## 最小代码

文件：`deepagent_src/human_loop_teach/02_decision_types.py`

```python
interrupt_on = {
    "notify_email": {"allowed_decisions": ["approve", "edit", "reject"]},
    "ask_user": {"allowed_decisions": ["respond"]},
}
```

## 运行

```bash
uv run python deepagent_src/human_loop_teach/02_decision_types.py
```

预期输出末尾：

```text
decision types HITL real agent ok
```

## 决策区别

| decision | 是否执行原工具 | 典型用途 |
| --- | --- | --- |
| `approve` | 是 | 原参数没问题 |
| `edit` | 是，但用 edited args | 修改邮件收件人、路径、金额 |
| `reject` | 否 | 拒绝删除、拒绝发邮件 |
| `respond` | 否 | 人类直接回答 `ask_user` 工具 |

## 常见误区

不要用 `respond` 表示拒绝危险操作。`respond` 会被模型当成工具结果，容易被误解为“操作成功返回了某个内容”。拒绝副作用工具时用 `reject`。

