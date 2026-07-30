# 06 类中间件与 `state_schema`

`AgentMiddleware` 类写法适合把多个 hook 和它们共享的配置放在一起。`state_schema` 用来扩展 agent state，让 middleware 能把计数、标记、审计结果这类运行时信息写回最终 state。它不是全局变量，也不是系统提示词，作用域是这次 agent run 的状态。

## 最小代码

代码在：

```bash
deepagent_src/middleware_teach/06_class_state_schema.py
```

核心逻辑：

```python
class AuditState(AgentState):
    model_call_count: NotRequired[int]
    last_model_text: NotRequired[str]


class AuditStateMiddleware(AgentMiddleware[AuditState, Any]):
    state_schema = AuditState

    def before_model(self, state: AuditState, runtime: Runtime[Any]):
        return {"model_call_count": state.get("model_call_count", 0) + 1}

    def after_model(self, state: AuditState, runtime: Runtime[Any]):
        return {"last_model_text": state["messages"][-1].text}
```

`before_model` 在模型调用前把计数加一，`after_model` 在模型返回后记录最后的模型文本。两个 hook 共享同一个扩展状态结构。

## 运行

```bash
uv run python -m deepagent_src.middleware_teach.06_class_state_schema
```

预期输出包含：

```text
model_call_count: 1
last_model_text: STATE_SCHEMA_OK
class middleware state_schema local check ok
```

## 常见误区

不要把 `state_schema` 当数据库用。它只描述 agent state 中允许出现的字段，适合保存一次运行里的轻量状态；跨线程、跨会话持久化要用 checkpointer、store、Deep Agents memory 或后端存储。

## 和前面章节的关系

- 装饰器写法：适合一个简单 hook。
- 类写法：适合多个 hook、共享配置、复用成生产 middleware。
- `state_schema`：让 middleware 的状态字段有明确结构，避免到处塞魔法 key，艹，那种隐式字典最容易把人坑死。
