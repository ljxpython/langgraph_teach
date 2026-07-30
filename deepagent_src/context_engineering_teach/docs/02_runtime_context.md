# 02 Runtime context：每次调用的静态配置

## 它是什么

Runtime context 是 `invoke` 时传入的每轮固定配置，比如用户 ID、角色、租户、连接信息或 API key。它默认不会进入模型 prompt，只有工具或 middleware 读取后才会产生影响。它解决的问题是：工具需要知道“当前是谁、有什么权限”，但不应该把敏感值直接塞进对话文本。

## 最小代码

文件：`deepagent_src/context_engineering_teach/02_runtime_context.py`

```python
@dataclass
class RunContext:
    user_id: str
    role: str


@tool
def current_user_note(query: str, runtime: ToolRuntime[RunContext]) -> str:
    """Return a note scoped to the invoking user."""
    return f"{runtime.context.user_id}:{runtime.context.role}:{query}"
```

## 运行

```bash
uv run python deepagent_src/context_engineering_teach/02_runtime_context.py
```

预期输出：

```text
runtime context real agent ok
```

## 验证方式

脚本会真实调用 Agent，并要求 Agent 调用 `current_user_note` 工具，断言工具输出里包含从 `runtime.context` 读到的 `user_id` 和 `role`。

## 常见误区

别把 runtime context 当成长期记忆。它只属于本次运行；跨 thread、跨会话要用 long-term memory 或外部存储。
