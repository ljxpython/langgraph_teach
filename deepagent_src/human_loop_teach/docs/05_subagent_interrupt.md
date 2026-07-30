# 05 subagent interrupts

## 它是什么

Subagent 可以定义自己的 `interrupt_on`，覆盖或补充父 Agent 的审批策略。子 Agent 触发的中断会冒泡到父 Agent 的 `GraphOutput.interrupts`，恢复方式仍然是 `Command(resume=...)`。它解决的问题是：专家子 Agent 有自己的风险边界。

## 常用程度

中。只要 subagent 有敏感工具，就应该考虑给它单独配置。

## 最小代码

文件：`deepagent_src/human_loop_teach/05_subagent_interrupt.py`

```python
secret_reader_subagent = {
    "name": "secret-reader",
    "tools": [read_secret],
    "interrupt_on": {
        "read_secret": {"allowed_decisions": ["approve", "reject"]},
    },
}
```

## 运行

```bash
uv run python deepagent_src/human_loop_teach/05_subagent_interrupt.py
```

预期输出末尾：

```text
subagent interrupt HITL real agent ok
```

## 验证方式

主 Agent 先通过 `task` 委派给 `secret-reader`，子 Agent 调 `read_secret` 时触发 interrupt。脚本 approve 后，父 Agent 的 `task` 工具结果包含子 Agent 返回值。

## 常见误区

父 Agent 的 `interrupt_on` 不一定适合每个 subagent。自定义 subagent 指定 `interrupt_on` 后，会以子 Agent 自己的配置为准。

