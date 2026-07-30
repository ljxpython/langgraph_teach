# 05 Subagents：上下文隔离

## 它是什么

Subagent 用独立上下文处理重活，主 Agent 只接收最终结果。它解决的问题是：网页搜索、文件读取、数据库查询这类多步工具调用会制造大量中间日志，容易把主上下文撑爆。runtime context 会传给 subagent，所以用户和权限信息仍然可用。

## 最小代码

文件：`deepagent_src/context_engineering_teach/05_context_isolation_subagents.py`

```python
research_subagent = {
    "name": "researcher",
    "description": "Do heavy research and return only a concise summary.",
    "system_prompt": "Keep the final answer under 120 words. Do not return raw tool logs.",
    "tools": [get_user_marker],
}
```

## 运行

```bash
uv run python deepagent_src/context_engineering_teach/05_context_isolation_subagents.py
```

预期输出：

```text
context isolation subagent real agent ok
```

## 验证方式

脚本真实调用主 Agent，让它把任务交给 subagent；subagent 调用 `get_user_marker` 工具，验证 runtime context 能传到 subagent。

## 常见误区

别让 subagent 返回原始搜索结果和完整工具日志。subagent 的价值就是隔离上下文，返回一份够主 Agent 决策的短总结。
