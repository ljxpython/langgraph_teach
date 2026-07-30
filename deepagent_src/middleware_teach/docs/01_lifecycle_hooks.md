# 第一章：生命周期钩子 `before_model` / `after_model`

这两个 hook 是最基础的 middleware 入口：`before_model` 在每次模型调用前执行，`after_model` 在模型返回后执行。它们适合做日志、限流标记、状态统计、轻量校验；不适合改写整个模型调用流程，那是 `wrap_model_call` 的活。

## 最小代码

代码在 `deepagent_src/middleware_teach/01_lifecycle_hooks.py`。

```python
from langchain.agents import create_agent
from langchain.agents.middleware import before_model, after_model
from langchain_core.language_models.fake_chat_models import FakeListChatModel

event_log = []

@before_model
def log_before_model(state, runtime):
    event_log.append(f"before_model:{len(state['messages'])}")
    return None

@after_model
def log_after_model(state, runtime):
    event_log.append(f"after_model:{state['messages'][-1].text}")
    return None

agent = create_agent(
    model=FakeListChatModel(responses=["MIDDLEWARE_OK"]),
    tools=[],
    middleware=[log_before_model, log_after_model],
)
```

这里故意不用 `create_deep_agent`。原因不是它不能挂 middleware，而是 Deep Agents 默认还会注入文件系统、subagent 等 middleware；第一章只看生命周期钩子，用最底层 `create_agent` 更干净。等到第四章再回到 Deep Agents 默认栈。

## 运行命令

```bash
uv run python -m deepagent_src.middleware_teach.01_lifecycle_hooks
```

## 预期现象

你会看到：

```text
event_log: ['before_model:1', 'after_model:MIDDLEWARE_OK']
final: MIDDLEWARE_OK
middleware lifecycle hooks local check ok
```

这说明：

1. 用户消息先进入 state。
2. `before_model` 在真正模型调用前读取到当前消息数。
3. 模型返回后，`after_model` 能直接看到新增的 AIMessage。

## 一个常见误区

很多人第一次写 middleware，会把 `before_model` 当成“提前返回答案”的地方。这是错的。`before_model` / `after_model` 是 node-style hook，返回值是状态更新 dict，不是模型响应对象。要包住模型调用、决定是否继续调用、改 model request 或短路返回，请用 `wrap_model_call`。

## 和 Deep Agents 的关系

官方文档里，Deep Agents 的默认主栈会先后注入 `SkillsMiddleware`、`FilesystemMiddleware`、`SubAgentMiddleware`、`SummarizationMiddleware` 等，再把你传入的 `middleware=` 合并进去。也就是说，Deep Agents 不是不用 LangChain middleware；它恰恰是靠这套 middleware 机制把“技能、文件系统、记忆、HITL”这些能力缝起来的。
