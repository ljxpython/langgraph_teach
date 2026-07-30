# 04 structured output

## 它是什么

Subagent 可以设置 `response_format`，让子 Agent 最终结果按 schema 结构化。父 Agent 收到的是 JSON 序列化后的 `ToolMessage` 内容，不再是随意文本。它适合父 Agent 需要继续处理结果、传给下游工具或保存到结构化存储的场景。

## 常用程度

中高。只要父 Agent 后面还要程序化处理子 Agent 结果，就该优先考虑。

适合：

- 子 Agent 返回评分、置信度、sources、风险等级。
- 父 Agent 要把结果写数据库或传给另一个工具。
- UI 需要固定字段展示。

不适合：

- 子 Agent 只需要返回一段总结。
- schema 还没稳定，频繁改字段会让示例和下游都变烦。

## 父 Agent 收到什么

没有 `response_format` 时：

```text
ToolMessage content = 子 Agent 最后一条文本
```

有 `response_format` 时：

```text
ToolMessage content = JSON 字符串
```

所以父 Agent 或你的代码需要 `json.loads(...)` 后再处理字段。

## 最小代码

文件：`deepagent_src/subagents_teach/04_structured_output.py`

```python
class LessonFinding(BaseModel):
    summary: str
    confidence: float
    sources: list[str]


structured_subagent = {
    "name": "structured-reporter",
    "description": "Use this subagent when the parent needs JSON findings.",
    "system_prompt": "Return structured data.",
    "response_format": LessonFinding,
}
```

## 运行

```bash
uv run python deepagent_src/subagents_teach/04_structured_output.py
```

预期输出末尾：

```text
subagent structured output real agent ok
```

## 验证方式

脚本真实调用主 Agent，让它委派 `structured-reporter`；随后解析父 Agent 收到的 `task` 工具内容为 JSON，并断言字段符合 schema。

本章断言三个字段：

```text
summary = structured-subagent-summary
confidence = 0.91
sources = ["subagent-docs"]
```

## 常见误区

structured output 约束的是 subagent 的最终返回结果，不是 subagent 内部每一步工具输出。

另一个坑：父 Agent 拿到的是 JSON 字符串，不是 Python 对象。你在应用代码里要自己解析。
