# 06 Permissions

## 学习目标

理解一句话：Permissions 在文件工具调用 Backend 前拦截路径，模型选错路径也不能越权写入。

代码见 [`../06_permissions.py`](../06_permissions.py)。

## 本课规则

```python
permissions = [
    FilesystemPermission(["write"], ["/workspace/protected/**"], "deny"),
    FilesystemPermission(["write"], ["/workspace/**"], "allow"),
    FilesystemPermission(["write"], ["/**"], "deny"),
]
```

按顺序解释：

1. `/workspace/protected/**`：最具体，禁止写入。
2. `/workspace/**`：其他 workspace 文件允许写入。
3. `/**`：未匹配的其他路径全部禁止写入，形成写入白名单。

第一条命中即停止匹配。因此最具体规则必须放前面，兜底规则必须放最后。

## 运行

```bash
uv run python deepagent_src/backend_teach/06_permissions.py
```

运行会调用模型一次，产生 API 费用。

预期结果：

```text
/workspace/public/ok-xxxx.txt       -> 创建成功
/workspace/protected/no-xxxx.txt    -> permission denied
```

程序最后直接检查真实磁盘：允许文件存在，受保护文件不存在。

## 为什么这叫强制边界

模型可以在回复中说“我要写 protected”，也可以真的发出 `write_file` 工具调用；但权限检查发生在工具调用之后、Backend 调用之前：

```text
模型 -> write_file -> Permissions 拒绝 -> Backend 未调用 -> 磁盘未修改
```

这和 system prompt 完全不同。Prompt 是建议；Permissions 是代码执行的硬规则。

## 参数速查

```python
FilesystemPermission(
    operations=["write"],
    paths=["/workspace/protected/**"],
    mode="deny",
)
```

- `operations`：`read` 或 `write`。
- `paths`：以 `/` 开头的虚拟路径模式。
- `mode`：`allow`、`deny` 或 `interrupt`。

`read` 管 `ls`、`read_file`、`glob`、`grep`；`write` 管 `write_file`、`edit_file`、`delete`。

## 本课范围

本例只演示 `deny`。`interrupt` 会暂停 Agent，等待 Human-in-the-Loop 审批后再继续；它适合删除、发布和修改关键配置。

Permissions 不限制 Shell 的 `execute`。需要执行不可信命令时使用 Sandbox，不要使用 `LocalShellBackend`。

详细规则说明见 [03 CompositeBackend 讲义](03_composite_backend.md#permissions文件工具的硬闸门)。
