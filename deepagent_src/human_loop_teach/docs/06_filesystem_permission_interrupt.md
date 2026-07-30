# 06 filesystem permission interrupts

## 它是什么

除了 `interrupt_on`，Deep Agents 的内置文件系统工具也能通过 `FilesystemPermission(mode="interrupt")` 暂停。命中规则时，会产生和普通工具审批一样的 interrupt。它解决的问题是：按路径和操作类型保护文件写入。

## 常用程度

中。涉及写文件、改配置、写 secrets、写生产目录时很有用。

## 最小代码

文件：`deepagent_src/human_loop_teach/06_filesystem_permission_interrupt.py`

```python
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
uv run python deepagent_src/human_loop_teach/06_filesystem_permission_interrupt.py
```

预期输出末尾：

```text
filesystem permission interrupt HITL real agent ok
```

## 验证方式

脚本要求 Agent 写 `/secrets/key.txt`，文件系统权限规则触发 interrupt。approve 后，虚拟文件系统的 `write_file` 才执行。

## 常见误区

这里保护的是 Deep Agents 的虚拟文件系统工具，不是操作系统真实 `/secrets`。生产里还要配真实后端权限，不要只靠模型层审批。

