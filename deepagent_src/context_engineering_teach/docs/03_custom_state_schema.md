# 03 Custom state schema：可变图状态

## 它是什么

Custom state schema 是 Deep Agent 的可变图状态扩展，适合保存运行中会变化并需要 checkpoint 的数据。它解决的问题是：工具和 middleware 要共享“当前页面、已收集文件、计数器”等运行中状态。不可变的用户配置仍然优先放 runtime context。

## 最小代码

文件：`deepagent_src/context_engineering_teach/03_custom_state_schema.py`

```python
class ResearchState(DeepAgentState):
    page_url: str
    file_urls: list[str]


@tool
def cite_page(runtime: ToolRuntime) -> str:
    """Return the page URL stored in mutable agent state."""
    return runtime.state["page_url"]
```

## 运行

```bash
uv run python deepagent_src/context_engineering_teach/03_custom_state_schema.py
```

预期输出：

```text
custom state schema real agent ok
```

## 验证方式

脚本确认 `ResearchState` 暴露了新增 state 字段，并真实调用 Agent，要求 Agent 调用 `cite_page` 工具从 `runtime.state` 读到 `page_url`。

## 常见误区

别用 state 存 API key、用户角色这类每轮静态配置。那些信息放 runtime context 更清楚，也更不容易被模型上下文污染。
