# 07 综合案例

## 它是什么

综合案例在同一个 Agent 配置里同时启用自定义工具审批和文件系统权限审批。脚本遇到中断后会在终端展示工具名、参数和可选决策，由你手动输入 `approve`、`edit` 或 `reject`。它解决的问题是：真实项目通常会同时有多类风险动作，但最终决策来自人，不是代码写死。

## 最小代码

文件：`deepagent_src/human_loop_teach/07_comprehensive_case.py`

```python
interrupt_on={
    "notify_email": {"allowed_decisions": ["approve", "edit", "reject"]},
}
permissions=[
    FilesystemPermission(
        operations=["write"],
        paths=["/secrets/**"],
        mode="interrupt",
    )
]
```

## 运行

```bash
uv run python deepagent_src/human_loop_teach/07_comprehensive_case.py
```

预期输出末尾：

```text
interactive comprehensive HITL demo completed
```

运行过程中会出现类似提示：

```text
需要人工审核：
tool: notify_email
args: {'to': 'wrong@example.com', 'subject': 'Deploy', 'body': 'Ready'}
可选: approve, edit, reject
请输入决策:
```

## 串联了哪些知识点

- `interrupt_on`：拦截 `notify_email`
- `FilesystemPermission(mode="interrupt")`：拦截 `/secrets/**` 写入
- `approve`：按原参数执行工具
- `edit`：在终端逐个字段修改工具参数
- `reject`：在终端输入拒绝原因，跳过工具执行
- 同一个 `thread_id`：每次暂停后都必须用对应的同一份 config 恢复

## 常见误区

不要把“同一个 Agent 同时配置多种审批规则”和“模型同一轮生成多个工具调用”混成一件事。第 04 章演示批量审批；本章演示同一套 Agent 配置如何覆盖不同风险动作。
