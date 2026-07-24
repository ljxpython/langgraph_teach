# 06 综合案例：把 skills 串起来

## 学习目标

把前面 1 到 5 章连成一个完整流程：发现 skill、读取指令、按需用资源、隔离 backend、加权限、给 subagent 配置独立能力。

## 场景

做一个“文档研究助手”：

- 主 Agent 从固定 workspace 里的 `/skills/` 加载 `langgraph-docs` skill。
- skill 的 `SKILL.md` 告诉 Agent 去读 `references/`，必要时执行 `scripts/`，输出报告时用 `assets/` 模板。
- 共享 skill 库只读，防止 Agent 改规范。
- 个人/团队记忆走 store，临时草稿走 state。
- 自定义 `researcher` subagent 也能拿到同一个 skill，但权限可以单独收紧。

## 这条链怎么串

```text
create_deep_agent(..., skills=["/skills/"], backend=CompositeBackend(...))
  -> SkillsMiddleware 扫到 /skills/langgraph-docs/SKILL.md
  -> 系统提示词只注入 name / description / 路径
  -> SKILL.md 说明支持资源的位置
  -> resources 按需读取
  -> permissions 禁止写共享技能
  -> subagent 显式拿到 skills 和 permissions
  -> report template 生成最终输出
```

## 最小可运行例子

代码见 [`../06_comprehensive_case.py`](../06_comprehensive_case.py)。

这个例子做的不是“再讲一遍概念”，而是把概念放到同一条流程里：

- `FilesystemBackend` 承载 `/skills/` 和 `/workspace/`
- `StoreBackend` 承载 `/memories/`
- `StateBackend` 作为默认临时层
- `SkillsMiddleware` 负责发现和摘要
- `FilesystemPermission` 保护共享 skill
- `subagents` 给研究子 Agent 单独配 skill

注意：`CompositeBackend` 路由会剥掉 route 前缀。所以 `/skills/` 路由的 `FilesystemBackend` root 要指向真实 `workspace/skills`，这样 `/skills/langgraph-docs/SKILL.md` 才会落到后端里的 `/langgraph-docs/SKILL.md`。

## 真实 Agent 调用

如果只想最后打印完整消息链，用 `invoke_and_pretty_print()` 或原生 `pretty_print()`：

```python
from langchain.messages import HumanMessage

messages = [HumanMessage(content="请使用 langgraph-docs skill，总结 DeepAgent skills 的使用链路。")]
messages = graph.invoke({"messages": messages})
for message in messages["messages"]:
    message.pretty_print()
```

如果想实时看到 Agent 过程，用这章实际采用的流式方法：

```python
from langchain.messages import HumanMessage

from deepagent_src.agent_output import stream_values_and_pretty_print

messages = [HumanMessage(content="请使用 langgraph-docs skill，总结 DeepAgent skills 的使用链路。")]
messages = stream_values_and_pretty_print(
    graph,
    {"messages": messages},
    {"configurable": {"thread_id": "skills-comprehensive-case"}},
)
```

在项目根目录执行：

```bash
uv run python deepagent_src/skills_teach/06_comprehensive_case.py
```

预期现象：

- 终端打印完整消息链，包括 `HumanMessage`、模型消息和工具调用相关消息。
- Agent 会根据 `/skills/` 的 discovery 信息读取 `/skills/langgraph-docs/SKILL.md`。
- 如果模型按指令继续走，会读取 `references/resource-map.md` 和 `assets/report-template.md`。
- 最后输出 `comprehensive skills case ok`。

注意：运行这章会调用 `deepagent_src.llms.get_gpt_model()`，会产生真实模型请求和可能的 API 费用。

## 你应该从这个案例记住什么

1. `skills` 不是“再多一个目录”，而是 Agent 的按需能力入口。
2. `SKILL.md` 不是资料堆，而是调度说明书。
3. `references/`、`scripts/`、`assets/` 是延迟加载的支持件。
4. backend 决定文件放哪儿，permissions 决定能不能改，subagent 决定谁能用。

## 常见误区

最常见的误区是把前面每一章看成孤立特性。实际上 skills 的价值就是把发现、读取、执行、权限、隔离这几件事连成一条稳定链路。拆开看都懂，合起来就经常写崩，艹，所以最后一定要看综合案例。

另一个坑是权限顺序。规则是 first match wins，所以如果你先写 `deny /skills/**`，后面的 `interrupt /skills/personal/**` 就永远匹配不到。更具体的规则要放前面。
