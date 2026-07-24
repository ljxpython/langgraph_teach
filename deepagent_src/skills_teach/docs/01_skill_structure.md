# 01 把 skills 接进 DeepAgent

## 学习目标

理解一句话：DeepAgent 通过 `skills=[...]` 指定技能来源，再由 `SkillsMiddleware` 从 backend 读取每个 `SKILL.md` 的元数据。

## 它是什么

在 Deep Agents 里，`skills` 参数告诉 Agent 去哪些路径找技能。启动阶段不会把所有说明全塞进上下文，只读取每个 `SKILL.md` frontmatter 里的 `name` 和 `description`。这一步解决的是“Agent 先知道自己有哪些可用能力”，不是让 Agent 立刻执行 skill。

## 最小接入结构

```text
backend root/
└── skills/
    └── langgraph-docs/
        └── SKILL.md
```

接入代码的核心形态：

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

backend = FilesystemBackend(root_dir="deepagent_src/skills_teach/workspace", virtual_mode=True)

agent = create_deep_agent(
    model=model,
    backend=backend,
    skills=["/skills/"],
)
```

这里的 `/skills/` 不是随便写的装饰品。它告诉 `SkillsMiddleware`：去 backend 的这个路径下面找 skill 目录。

## 被发现的 skill 长什么样

```text
skills/
└── langgraph-docs/
    └── SKILL.md
```

最小 `SKILL.md`：

```md
---
name: langgraph-docs
description: Use this skill when the user asks for LangGraph documentation help.
---

# langgraph-docs

## Instructions

1. Read the documentation index.
2. Pick the pages relevant to the user's question.
3. Answer with links to the source pages.
```

关键规则：

- `SKILL.md` 必须放在 skill 自己的目录里，否则 discovery 扫不到。
- `name` 是技能名，应该和父目录名一致。
- `description` 是启动阶段最重要的信息，Agent 靠它判断后续任务是否可能用到这个 skill。
- markdown 正文不会在 discovery 阶段全量加载，任务匹配后才读取。

## 最小可运行例子

代码见 [`../01_skill_structure.py`](../01_skill_structure.py)。

这个例子只做一件事：从固定 backend root `deepagent_src/skills_teach/workspace` 读取 skill，然后用 Deep Agents 的 skills discovery 逻辑确认它能被发现。

它不调用模型。第一章只验证“DeepAgent 能从 `skills` 路径看到这个 skill”，激活读取放下一章，别一口吃成憨批。

## 运行

在项目根目录执行：

```bash
uv run python deepagent_src/skills_teach/01_skill_structure.py
```

预期输出类似：

```text
skills discovery ok: langgraph-docs /skills/langgraph-docs/SKILL.md
```

## 本地验证

脚本里的断言会验证：

- `FilesystemBackend(root_dir="deepagent_src/skills_teach/workspace", virtual_mode=True)` 能看到 `/skills/`。
- discovery 能读到 `langgraph-docs` 的 `name`。
- discovery 返回的 skill 文件路径是 `/skills/langgraph-docs/SKILL.md`。

## 常见误区

最常见的坑是把 `skills` 路径和 backend root 搞混。这里真实文件在 `deepagent_src/skills_teach/workspace/skills/langgraph-docs/SKILL.md`，但 DeepAgent 看到的是虚拟路径 `/skills/langgraph-docs/SKILL.md`。

## 下一章

下一章学“激活与渐进披露”：什么时候只看 `description`，什么时候才读取完整 `SKILL.md`。
