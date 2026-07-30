# Middleware 学习路线

这组小章节专门补 Deep Agents / LangChain / LangGraph 里的 middleware。代码放在 `deepagent_src/middleware_teach/`，讲义放在 `deepagent_src/middleware_teach/docs/`。

## 为什么这块值得单独学

middleware 是 Agent 运行时最容易混淆的一层：它既不是 prompt，也不是 tool 本身，更不是 LangGraph 节点图手写逻辑。它的职责是拦截 agent loop 中的固定时机，在模型调用前后、工具执行前后或整轮运行前后插入控制逻辑。

Deep Agents 自己也大量依赖 middleware：文件系统、skills、subagents、summarization、memory、HITL 都是靠 middleware 叠出来的。所以不懂 LangChain middleware，就看不透 Deep Agents 的“自动能力”到底是怎么塞进去的。

## 课程大纲

### 01 生命周期钩子：`before_model` / `after_model`

目标：看懂 node-style hook 的触发时机，知道它们返回的是“状态更新”而不是直接替代模型。

### 02 `wrap_model_call`：改模型请求与短路

目标：理解 wrap-style hook 如何包住模型调用，什么时候该用它改模型、重试、fallback 或直接短路。

### 03 `wrap_tool_call`：工具重试与错误恢复

目标：理解工具层 middleware 与 `ToolRetryMiddleware` / `ToolErrorMiddleware` 的工作位置。

### 04 Deep Agents 默认栈

目标：理解 `create_deep_agent(..., middleware=[...])` 时，你自己的 middleware 插在默认 stack 的哪里，哪些是可替换的，哪些不能乱删。

### 05 综合案例

目标：把 LangChain 自定义 middleware 和 Deep Agents 默认 middleware 串起来，做一个“动态模型选择 + 工具容错”的最小真实流程。

### 06 类中间件与 `state_schema`

目标：理解什么时候从装饰器写法升级到 `AgentMiddleware` 类写法，以及如何用 `state_schema` 给 agent state 增加 middleware 专属字段。

## 当前版本依据

- `deepagents==0.7.0b2`
- `langchain==1.0.7`
- 官方资料：
  - `/oss/python/deepagents/customization#middleware`
  - `/oss/python/langchain/middleware/built-in`
  - `/oss/python/langchain/middleware/custom`

## 第一章运行

```bash
uv run python -m deepagent_src.middleware_teach.01_lifecycle_hooks
```

这章不走真实网络、不调用付费模型，只用 `FakeListChatModel` 做本地验证。原因很简单：第一章只想看 middleware 生命周期，艹，没必要为一个钩子顺序去烧 token。

## 第二章运行

```bash
uv run python -m deepagent_src.middleware_teach.02_wrap_model_call
```

这章验证 `wrap_model_call` 的两个边界：正常路径调用 `handler(request)`，短路路径直接返回 `ModelResponse`，不会触发模型调用。

## 第三章运行

```bash
uv run python -m deepagent_src.middleware_teach.03_wrap_tool_call
```

这章验证 `wrap_tool_call` 的工具层边界：调用 `handler(request)` 才真正执行工具，返回的 `ToolMessage` 会进入对话历史。

## 第四章运行

```bash
uv run python -m deepagent_src.middleware_teach.04_deepagents_default_stack
```

这章验证 Deep Agents 默认 middleware 栈的可观察节点：`PatchToolCallsMiddleware.before_agent` 在用户自定义 `before_model` 节点之前。

## 第五章运行

```bash
uv run python -m deepagent_src.middleware_teach.05_comprehensive_case
```

这章会触发真实 `gpt-5.5` Deep Agent 调用，验证模型层 middleware 与工具层 middleware 可以在同一条 agent loop 中协作。

## 第六章运行

```bash
uv run python -m deepagent_src.middleware_teach.06_class_state_schema
```

这章不走真实网络，只验证类中间件声明 `state_schema` 后，`before_model` / `after_model` 写入的扩展状态会保留在最终 agent state 中。
