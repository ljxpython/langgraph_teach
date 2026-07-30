# 04 多工具批量审批

## 它是什么

当模型一次生成多个需要审批的工具调用，Deep Agents 会把它们合并进一个 interrupt。人类恢复时必须按 `action_requests` 的顺序提供同样数量的 decisions。它解决的问题是：一次审一批，避免来回打断。

## 常用程度

中。模型并行调用多个工具时常见，尤其是“删除文件并发邮件通知”这类组合任务。

## 最小代码

文件：`deepagent_src/human_loop_teach/04_multiple_tool_calls.py`

```python
interrupt_on = {
    "delete_record": {"allowed_decisions": ["approve", "reject"]},
    "notify_email": {"allowed_decisions": ["approve", "reject"]},
}
```

## 运行

```bash
uv run python deepagent_src/human_loop_teach/04_multiple_tool_calls.py
```

预期输出末尾：

```text
multiple tool calls HITL real agent ok
```

## 验证方式

脚本断言 interrupt 里有两个 action：

```text
delete_record
notify_email
```

然后按顺序 approve 第一个、reject 第二个。

## 常见误区

decisions 不是按工具名自动匹配，而是按 action_requests 顺序匹配。生产 UI 里要小心保持顺序，不然就会把审批结果套错工具。

