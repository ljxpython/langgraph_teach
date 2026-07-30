# 01 基础中断与 approve

## 它是什么

`interrupt_on` 可以让某个工具在执行前暂停，先交给人类审批。`approve` 表示按模型原始工具参数继续执行。它解决的问题是：敏感操作不让模型直接落地执行。

## 常用程度

高。删除、发送邮件、付款、写生产数据、改权限这类工具都应该优先考虑。

## 最小代码

文件：`deepagent_src/human_loop_teach/01_basic_approve.py`

```python
agent = create_deep_agent(
    model=get_real_model(),
    tools=[remove_file],
    interrupt_on={"remove_file": True},
    checkpointer=MemorySaver(),
)
```

## 运行

```bash
uv run python deepagent_src/human_loop_teach/01_basic_approve.py
```

预期输出末尾：

```text
basic approve HITL real agent ok
```

## 运行现象

第一次调用会返回 interrupt：

```text
tool=remove_file args={'path': '/tmp/a.txt'}
review=remove_file decisions=['approve', 'edit', 'reject', 'respond']
```

然后脚本用：

```python
Command(resume={"decisions": [{"type": "approve"}]})
```

恢复同一个 thread，工具才真正执行。

## 常见误区

HITL 必须有 checkpointer，并且恢复时必须使用同一个 `thread_id`。换 thread 就像让另一个人接着听半截电话，肯定对不上。

