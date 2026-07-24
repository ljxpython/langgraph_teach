# 03 只读与可写 Memory

## 学习目标

理解一句话：memory 默认可以读写，但共享政策和组织级记忆应该只读。

## 它是什么

Agent 可以通过 `edit_file` 更新 memory，但不是所有 memory 都该让它改。用户偏好可以写，组织政策通常只读，敏感记忆可以要求人工审批。这个边界不划清，prompt injection 一来就能把共享记忆改烂，艹，后患无穷。

## 最小配置

```python
FilesystemPermission(
    operations=["write"],
    paths=["/policies/**"],
    mode="deny",
)
```

个人记忆需要人工确认时：

```python
FilesystemPermission(
    operations=["write"],
    paths=["/memories/personal/**"],
    mode="interrupt",
)
```

## 最小可运行例子

代码见 [`../03_memory_permissions.py`](../03_memory_permissions.py)。

这个例子验证：

- `/policies/AGENTS.md` 可读但不可写。
- `/memories/personal/AGENTS.md` 写入会触发 `interrupt`。
- 普通 `/memories/AGENTS.md` 可以写。

## 运行

```bash
uv run python deepagent_src/memory_teach/03_memory_permissions.py
```

预期输出：

```text
memory permissions ok
```

## 常见误区

权限规则是 first match wins。更具体的规则要放前面，否则会被宽泛规则提前吃掉。
