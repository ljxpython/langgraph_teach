# 02 FilesystemBackend

## 学习目标

理解一句话：`FilesystemBackend` 把 Agent 的虚拟文件路径映射到真实磁盘目录。

## 示例

代码见 [`../02_filesystem_backend.py`](../02_filesystem_backend.py)。

核心配置：

```python
workspace = Path(__file__).with_name("workspace").resolve()

agent = create_deep_agent(
    model=gpt_model,
    backend=FilesystemBackend(
        root_dir=workspace,
        virtual_mode=True,
    ),
)
```

- `root_dir`：真实磁盘根目录。
- `virtual_mode=True`：Agent 只能通过文件工具访问这个根目录。
- Agent 看到 `/note-xxxx.txt`。
- 真实文件位于 `deepagent_src/backend_teach/workspace/note-xxxx.txt`。

## 运行

在项目根目录执行：

```bash
uv run python deepagent_src/backend_teach/02_filesystem_backend.py
```

运行会调用模型一次，产生 API 费用。

程序最后使用 Python 自己的 `Path.read_text()` 读取文件。这一步证明内容确实写进了真实磁盘，而不是只存在 Agent state 中。

## 为什么文件名每次不同

Backend 的 `write` 是 create-only：

- 文件不存在：创建成功。
- 文件已存在：返回错误，不覆盖原内容。

因此示例使用短 UUID 生成新文件名，保证可以重复运行。修改已有文件应使用 `edit_file`。

## 与 StateBackend 的区别

| 对比项 | StateBackend | FilesystemBackend |
| --- | --- | --- |
| 存储位置 | LangGraph state | 真实磁盘 |
| 是否需要 checkpointer | 跨调用保存时需要 | 不需要 |
| 程序退出后 | 取决于 checkpointer | 文件仍然存在 |
| 不同 thread 是否可见 | 默认不可见 | 访问同一目录就可见 |
| 典型用途 | 草稿、中间结果 | 项目文件、持久化产物 |

## 安全边界

```python
FilesystemBackend(root_dir=workspace, virtual_mode=True)
```

必须保留 `virtual_mode=True`，它会阻止文件工具通过 `..`、`~` 或外部绝对路径逃出 `root_dir`。

但仍要注意：

- Agent 可以读写 `workspace` 内的所有普通文件。
- 不要把 `.env`、API Key 或凭据放进可访问目录。
- 文件修改会直接落盘，无法像 StateBackend 那样随 thread 丢弃。
- Web API 和多租户服务不要直接暴露宿主机文件系统，应使用 Sandbox。

## 本课结论

`FilesystemBackend` 适合让可信 Agent 操作一个明确、隔离的本地目录；它的持久化来自磁盘，而不是 LangGraph checkpoint。
