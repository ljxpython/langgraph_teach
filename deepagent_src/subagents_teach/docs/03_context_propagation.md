# 03 runtime context 传播

## 它是什么

父 Agent 调用时传入的 runtime context 会自动传给同步 subagent。子 Agent 的工具可以通过 `ToolRuntime[Context]` 读取同一份 `runtime.context`。它解决的问题是：用户 ID、session ID、权限位这类运行时配置不需要塞进 prompt。

## 常用程度

高。只要是多用户、多租户、带权限的 Agent，runtime context 基本绕不开。

适合放 context：

- `user_id`
- `tenant_id`
- `session_id`
- 当前角色或权限位
- 工具需要的连接信息引用

不适合放 context：

- 子 Agent 需要长期记住的信息，这应该走 memory/store。
- 需要被模型自然语言推理的大段业务资料，这通常放文件、skills 或工具结果。

## 传播链路

```text
parent.invoke(..., context=UserContext(...))
-> 主 Agent runtime.context 可见
-> task 启动 subagent
-> subagent runtime.context 仍然是同一份结构
-> subagent 工具通过 ToolRuntime[UserContext] 读取
```

注意：context 不会自动变成 prompt 文本。只有工具读取并返回，模型才会看到它。

## 最小代码

文件：`deepagent_src/subagents_teach/03_context_propagation.py`

```python
@dataclass
class UserContext:
    user_id: str
    session_id: str


@tool
def read_context_marker(runtime: ToolRuntime[UserContext]) -> str:
    return f"{runtime.context.user_id}@{runtime.context.session_id}"
```

## 运行

```bash
uv run python deepagent_src/subagents_teach/03_context_propagation.py
```

预期输出末尾：

```text
subagent context propagation real agent ok
```

## 验证方式

脚本真实调用主 Agent 并传入 `UserContext(user_id="user-123", session_id="session-abc")`，断言 subagent 的 `task` 结果能读到 `user-123@session-abc`。

这证明用户和会话信息没有塞进用户消息，也能被子 Agent 工具读到。

## 常见误区

context 传播不等于把这些值展示给模型。只有工具或 middleware 主动读取并输出时，模型才会看到相关内容。

如果不同 subagent 需要不同配置，别建一堆全局变量。用字段区分，例如 `researcher_max_depth`、`fact_checker_strict_mode`，或者用扁平 namespaced key。
