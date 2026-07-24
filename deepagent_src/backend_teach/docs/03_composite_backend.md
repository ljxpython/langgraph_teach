# 03 CompositeBackend

## 学习目标

理解一句话：`CompositeBackend` 根据虚拟路径前缀，把文件操作转发给不同 Backend。

## 示例

代码见 [`../03_composite_backend.py`](../03_composite_backend.py)。

核心配置：

```python
backend = CompositeBackend(
    default=StateBackend(),
    routes={
        "/workspace/": FilesystemBackend(
            root_dir=workspace,
            virtual_mode=True,
        )
    },
)
```

路由结果：

```text
/draft.txt             -> StateBackend
/workspace/project.txt -> FilesystemBackend
```

没有匹配 `/workspace/` 的路径，全部交给 `default`。

## 运行

在项目根目录执行：

```bash
uv run python deepagent_src/backend_teach/03_composite_backend.py
```

运行调用模型一次，产生 API 费用。

Agent 会写入两个文件：

- `/draft-xxxx.txt`：只存在当前 Agent state 中。
- `/workspace/project-xxxx.txt`：写入真实磁盘的 `workspace/project-xxxx.txt`。

程序最后用 Python 检查磁盘：项目文件存在，草稿文件不存在。

## 挂载前缀

`/workspace/` 是 Agent 看到的虚拟挂载点：

```text
Agent 路径：/workspace/src/app.py
磁盘路径：<root_dir>/src/app.py
```

路由前缀会在转发时去掉，所以磁盘中不会额外出现一个 `workspace/` 目录。

## 为什么默认使用 StateBackend

Deep Agents 会自动保存一些内部数据，例如：

- `/large_tool_results/`
- `/conversation_history/`

如果直接把 `FilesystemBackend` 作为唯一 Backend，这些内部文件也会混进项目目录。

使用 `StateBackend` 作为默认 Backend，只把 `/workspace/` 挂载到磁盘，可以让临时数据和项目文件分开。

## 路由匹配规则

- 根据路径前缀匹配。
- 更长、更具体的前缀优先。
- 没匹配到任何 route 时使用 `default`。
- `ls`、`glob`、`grep` 会聚合多个 Backend 的结果。
- 聚合结果保留 Agent 看到的虚拟路径前缀。

例如：

```python
routes = {
    "/workspace/": project_backend,
    "/workspace/docs/": docs_backend,
}
```

访问 `/workspace/docs/readme.md` 时，较长的 `/workspace/docs/` 优先。

## 与前两课的关系

```text
StateBackend      = 临时文件
FilesystemBackend = 真实磁盘文件
CompositeBackend  = 把两者组合成一个虚拟文件系统
```

## 本课结论

实际项目优先使用 `CompositeBackend`：默认存临时 state，只把明确的项目路径映射到真实磁盘。

## 问题：Agent 怎么判断写临时目录还是 workspace？

Agent 不直接判断使用哪个 Backend，它只决定文件路径；`CompositeBackend` 再根据路径前缀机械路由。

```text
Agent 选择 /draft.txt             -> CompositeBackend 转给 StateBackend
Agent 选择 /workspace/report.md   -> CompositeBackend 转给 FilesystemBackend
```

本课示例能正确分流，是因为用户提示词明确指定了两个文件路径：

```text
把临时草稿写入 /draft-xxxx.txt
把项目文件写入 /workspace/project-xxxx.txt
```

真实项目通常在 `system_prompt` 中定义路径规则：

```python
agent = create_deep_agent(
    model=gpt_model,
    backend=backend,
    system_prompt="""
    临时草稿写到根目录。
    需要长期保留的项目文件必须写到 /workspace/。
    """,
)
```

执行流程是：

```text
用户需求 -> 模型根据提示词选择路径 -> 文件工具 -> CompositeBackend 路由
```

必须注意：

- `system_prompt` 只是引导，模型仍可能选错路径。
- 重要安全规则不能只靠提示词，应使用 Permissions 禁止不允许的读写。
- Deep Agents 自己使用 `/large_tool_results/`、`/conversation_history/` 等内部路径；这些路径没有匹配 `/workspace/`，所以进入默认 `StateBackend`。
- 应用代码也可以直接在任务描述中指定目标路径，这是最简单、最确定的方式。

一句话总结：模型负责选路径，Composite 负责按路径路由，Permissions 负责强制边界。

## Permissions：文件工具的硬闸门

`system_prompt` 只能告诉模型“应该怎么做”；`Permissions` 则在文件工具执行前检查路径。即使模型坚持要写禁区，Backend 也不会收到这次操作。

执行顺序：

```text
模型选择路径
    -> 文件工具调用
    -> Permissions 匹配规则
    -> allow：调用 Backend
       deny：直接返回 permission denied，Backend 不执行
       interrupt：暂停，等待人工批准后才继续
```

Permissions 检查的是 Agent 看到的虚拟路径，不是磁盘物理路径。因此对 CompositeBackend，应写 `/workspace/...`，不要写 `root_dir` 的真实绝对路径。

### 最小规则

```python
from deepagents import FilesystemPermission

permissions = [
    FilesystemPermission(
        operations=["write"],
        paths=["/workspace/config/**"],
        mode="deny",
    )
]
```

把规则传给 Agent：

```python
agent = create_deep_agent(
    model=gpt_model,
    backend=backend,
    permissions=permissions,
)
```

此时模型调用 `write_file`、`edit_file` 或 `delete` 操作 `/workspace/config/...` 时，工具直接返回拒绝错误，不会修改磁盘。

### operations 到底管哪些工具

| operations | 被控制的文件工具 |
| --- | --- |
| `read` | `ls`、`read_file`、`glob`、`grep` |
| `write` | `write_file`、`edit_file`、`delete` |

拒绝 `read` 后，直接读文件会报 permission denied；目录列举、glob 和 grep 的结果也会过滤掉无权读取的路径，避免“不能读内容却能看到文件名”。

### allow、deny、interrupt 的区别

| mode | 行为 | 适用场景 |
| --- | --- | --- |
| `allow` | 立即执行 | 明确允许的工作区 |
| `deny` | 返回拒绝错误，不调用 Backend | 密钥、配置、删除保护 |
| `interrupt` | 暂停运行，等人工批准 | 删除、发布、重要文件修改 |

`interrupt` 需要接入 Human-in-the-Loop 流程；它不是自动允许。适合写成明确的路径前缀，例如 `/workspace/secrets/**`。对于 `/**/secrets` 这种没有固定开头的模式，`ls`、`glob`、`grep` 可能过度触发审批。

### 规则顺序：第一条命中获胜

当前版本按传入顺序逐条匹配，第一条匹配的规则立即生效。具体规则必须放前面，兜底规则放最后：

```python
permissions = [
    # 1. 最具体的禁区先拦住
    FilesystemPermission(
        operations=["write"],
        paths=["/workspace/secrets/**"],
        mode="deny",
    ),
    # 2. 允许普通项目文件修改
    FilesystemPermission(
        operations=["write"],
        paths=["/workspace/**"],
        mode="allow",
    ),
    # 3. 其余位置一律禁止写入，形成真正白名单
    FilesystemPermission(
        operations=["write"],
        paths=["/**"],
        mode="deny",
    ),
]
```

如果把 `/**` 的 deny 放第一条，后面的 allow 永远没有机会匹配；如果只写第二条 allow，则其他路径仍会因为“未命中默认 allow”而被允许。这是最容易写错的地方。

### 路径模式规则

```python
FilesystemPermission(
    operations=["read", "write"],
    paths=["/workspace/**/*.py", "/memories/**"],
    mode="allow",
)
```

- 路径必须以 `/` 开头。
- 不允许 `..` 或 `~`。
- `*` 匹配一层路径，`**` 匹配多层路径。
- 一个规则可以同时写多个路径和多个操作。

### 它能保护什么，不能保护什么

能保护：

- Agent 自己发出的内置文件工具调用。
- 不同 Backend 后面的虚拟路径，例如 State、Filesystem、Store、Composite。
- 写入、编辑、删除等落盘前的文件操作。

不能保护：

- `LocalShellBackend` 或 Sandbox 的 `execute` 命令。Shell 命令能绕过文件工具直接访问系统。
- 你的 Python 业务代码自己调用 `Path.write_text()`。
- 已经拥有宿主机权限的其他进程。

因此：`virtual_mode=True` 负责限制 FilesystemBackend 的路径解析；Permissions 负责限制 Agent 文件工具；Shell 隔离应使用 Sandbox。三者不是同一个东西，谁也替代不了谁。

### 实际项目的最小策略

```text
临时文件：默认 StateBackend
项目文件：只允许 /workspace/**
密钥文件：deny /workspace/secrets/**
高风险操作：interrupt
执行命令：生产环境用 Sandbox，不用 LocalShellBackend
```

一句话总结：Prompt 负责建议，Permissions 负责拒绝，Sandbox 负责隔离。
