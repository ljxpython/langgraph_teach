# 03 条件中断

## 它是什么

条件中断用 `when` predicate 根据工具参数决定是否暂停。比如写 `/workspace/` 里可以自动通过，写 `/secrets/` 就必须审批。它解决的问题是：不是每次调用同一个工具都同样危险。

## 常用程度

中。只要同一个工具既能做低风险操作，又能做高风险操作，就应该考虑条件中断。

## 最小代码

文件：`deepagent_src/human_loop_teach/03_conditional_interrupt.py`

```python
def writes_outside_workspace(request: ToolCallRequest) -> bool:
    path = request.tool_call["args"].get("file_path", "")
    return not path.startswith("/workspace/")
```

## 运行

```bash
uv run python deepagent_src/human_loop_teach/03_conditional_interrupt.py
```

预期输出末尾：

```text
conditional interrupt HITL real agent ok
```

## 验证方式

脚本跑两次：

- `/workspace/a.txt`：`when` 返回 `False`，不 interrupt，工具直接执行。
- `/secrets/a.txt`：`when` 返回 `True`，触发 interrupt，脚本用 `reject` 恢复。

## 常见误区

`when` 只决定是否暂停，不负责权限执行本身。真正的访问控制还应该在工具内部、后端或文件系统权限层做。

