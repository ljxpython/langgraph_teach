# 01 Input context：启动时上下文

## 它是什么

Input context 是 Agent 启动时就进入系统上下文的信息，包括 `system_prompt`、memory、skills 和工具描述。它解决的问题是：哪些规则、长期约定和可发现能力应该每次运行前就被 Agent 知道。memory 是始终注入，skills 是先发现元信息、需要时再读完整内容。

## 最小代码

文件：`deepagent_src/context_engineering_teach/01_input_context.py`

```python
agent = create_deep_agent(
    model=model,
    backend=backend,
    system_prompt="You teach Deep Agents context engineering.",
    memory=["/memories/AGENTS.md"],
    skills=["/skills/"],
)
```

## 运行

```bash
uv run python deepagent_src/context_engineering_teach/01_input_context.py
```

预期输出：

```text
input context real agent ok
```

## 验证方式

脚本会读取 `/memories/AGENTS.md`，格式化 memory prompt；同时扫描 `/skills/` 下的 skill frontmatter，确认 `context-scout` 被发现。最后会真实调用一次 Agent。

## 常见误区

别把大段业务资料全塞进 `system_prompt`。总是相关、短小稳定的规则放 memory；按任务才用的工作流放 skills。
