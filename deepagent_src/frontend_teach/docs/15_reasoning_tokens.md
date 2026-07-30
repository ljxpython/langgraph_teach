# 15 Reasoning Tokens

## 它是什么

支持推理的模型可以在同一条 `AIMessage` 中返回 `reasoning` 与 `text` 两类标准内容块。前端将推理放进默认折叠区域，将 `text` 作为最终回答展示，避免两种内容混在一个气泡里。不是所有模型都会返回 reasoning，没有 reasoning 时应退化为普通消息。

## 后端消息协议

本章用确定性 LangGraph 节点返回标准内容块，不调用付费模型：

```python
AIMessage(
    content_blocks=[
        {"type": "reasoning", "reasoning": "先分析问题，再组织答案。"},
        {"type": "text", "text": "这是最终回答。"},
    ]
)
```

真实模型的原始字段各不相同。LangChain 将支持的响应标准化到 `AIMessage.content_blocks`，前端只处理标准类型，不应绑定 OpenAI、Anthropic 等厂商的私有响应结构。

## 前端提取

```tsx
const reasoning = message.contentBlocks
  .filter((block) => block.type === "reasoning" && block.reasoning.trim())
  .map((block) => block.reasoning)
  .join("");

const text = message.contentBlocks
  .filter((block) => block.type === "text" && block.text.trim())
  .map((block) => block.text)
  .join("");
```

一条消息可能包含多个同类型块，所以不能只读取第一个。需要保留 reasoning/text 交错顺序时，应按 `contentBlocks` 原顺序逐块渲染，而不是分别 `join()`。

## 折叠推理

本章使用浏览器原生 `<details>`，不额外维护 React 展开状态：

```tsx
<details>
  <summary>
    <span>推理过程</span>
    <small>{reasoning.length} 字符</small>
  </summary>
  <p>{reasoning}</p>
</details>
```

原生控件自带键盘操作和 `open` 状态。推理默认折叠，最终回答始终可见；如果消息没有 reasoning，则直接复用普通 `MessageBubble`。

## 运行与预期

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173` 并进入 `15 Reasoning Tokens`：

1. 提交默认问题。
2. 页面显示独立的“推理过程”和“final answer”。
3. 点击“推理过程”可以展开或折叠，最终回答不受影响。

后端最小测试：

```bash
uv run python -m unittest deepagent_src.frontend_teach.tests.test_reasoning_tokens
```

## 真实模型配置

真实项目需要选择明确支持 reasoning 的模型，并按模型供应商配置推理强度或 token budget。前端不应假定 reasoning 一定存在，也不应把模型未返回的内容自行包装成“推理过程”。

## 安全边界

- reasoning 是模型输出，不是事实证明，也不等于可复现的审计日志。
- 某些供应商只返回 reasoning summary 或加密块，前端必须按实际标准化结果处理。
- 推理可能包含敏感上下文、系统提示或不适合终端用户的信息，生产环境应经过权限与内容策略检查后再展示。
- 不要把 reasoning 与最终回答拼成 Markdown 后统一渲染，否则用户无法区分内部分析和正式结论。

## 常见误区

- 不要从 `message.text` 读取推理；`text` 只聚合面向用户的文本块。
- 不要假设只有一个 reasoning block。
- 不要用字符串前缀如 `Thought:` 解析类型，应读取 `block.type`。
- 不要为了折叠框引入状态库，原生 `<details>` 已经足够。

## 下一章

第 16 章学习 Structured Output：让后端返回可验证结构，并在前端渲染稳定的数据视图。

## 官方资料

- Reasoning tokens: `https://docs.langchain.com/oss/python/langchain/frontend/reasoning-tokens`
