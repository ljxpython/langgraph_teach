# 04 Context compression：自动压缩与手动 compact

## 它是什么

Context compression 是 Deep Agents 控制长任务上下文膨胀的内置机制。大工具输入或输出会被 offload 到虚拟文件系统，消息历史逼近上下文限制时会触发 summarization。需要主动清理上下文时，可以额外给 Agent 加 `compact_conversation` 工具。

## 最小代码

文件：`deepagent_src/context_engineering_teach/04_context_compression.py`

```python
model = get_real_model()
compaction_middleware = create_summarization_tool_middleware(model, StateBackend)
agent = create_deep_agent(model=model, middleware=[compaction_middleware])
```

## 运行

```bash
uv run python deepagent_src/context_engineering_teach/04_context_compression.py
```

预期输出：

```text
context compression real agent ok
```

## 验证方式

脚本断言 middleware 暴露了 `compact_conversation` 工具，并真实调用一次 Agent。自动 offloading 和阈值 summarization 需要真实长对话才会触发，所以这里不伪造大上下文。

## 常见误区

别以为加了手动 compact 就关闭了自动压缩。Deep Agents 默认仍会在上下文接近限制时自动总结。
