# 07 LocalShellBackend

## 学习目标

理解一句话：`LocalShellBackend` = `FilesystemBackend` + `execute`，但命令直接在宿主机执行，没有隔离。

代码见 [`../07_local_shell_backend.py`](../07_local_shell_backend.py)。

## 最小示例

```python
agent = create_deep_agent(
    model=gpt_model,
    backend=LocalShellBackend(
        root_dir=workspace,
        virtual_mode=True,
        env={"PATH": "/usr/bin:/bin"},
        timeout=10,
    ),
)
```

Agent 收到明确指令后调用：

```text
execute("pwd")
```

预期输出是 `shell_workspace` 的绝对路径。

## 运行

```bash
uv run python deepagent_src/backend_teach/07_local_shell_backend.py
```

运行会调用模型一次并允许它执行 Shell 命令。当前提示词只允许 `pwd`，但模型拥有的是宿主机 Shell 权限；只在自己的可信开发环境运行。

## 参数

| 参数 | 含义 |
| --- | --- |
| `root_dir` | Shell 命令的初始工作目录 |
| `virtual_mode` | 约束文件工具路径；不隔离 Shell 命令 |
| `timeout` | 单个命令最长执行秒数，默认 120 |
| `max_output_bytes` | 最大输出字节数，默认 100000 |
| `env` | 传给命令的环境变量 |
| `inherit_env` | 是否继承当前 Python 进程的全部环境变量，默认 `False` |

本例只提供最小 `PATH`，避免把 API Key 等父进程环境变量传进 Shell。

## 最重要的安全边界

```text
root_dir       只是 Shell 的起始目录
virtual_mode   只能约束文件工具路径
execute        可以执行任意 Shell 命令并访问宿主机其他路径
```

因此以下写法不安全：

```python
LocalShellBackend(root_dir=".", virtual_mode=True)
```

即使加了 `virtual_mode=True`，Agent 仍可通过 Shell 命令访问根目录外的文件。不要把它用于 Web 服务、多租户系统或不可信输入。

## Permissions 为什么拦不住 Shell

Permissions 只检查 `read_file`、`write_file`、`edit_file`、`delete`、`ls`、`glob`、`grep` 等文件工具；Shell 的 `execute` 不在它的保护范围。

```text
Permissions -> 文件工具
Sandbox     -> 命令隔离
```

需要在生产环境执行命令时，使用 Sandbox Backend；不要试图用 Permissions 把 `LocalShellBackend` 变安全。

## 适用场景

- 可信的个人本地开发环境
- 本地编码助手
- 已隔离的 CI 环境

不适用：生产服务、公开 API、多用户系统、处理不可信提示词或不可信代码。

## 本课结论

`LocalShellBackend` 方便，但不是沙箱。开发机上能用，生产环境换 Sandbox。
