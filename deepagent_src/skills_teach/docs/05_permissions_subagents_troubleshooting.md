# 05 权限、子 Agent 与排错

## 学习目标

理解一句话：生产里使用 skills 时，要控制谁能看、谁能改、哪个 subagent 能用，以及 skill 没加载时该查哪里。

## 它是什么

`skills` 让 Agent 读取专业说明，但这也意味着 Agent 可能读到或改到不该碰的文件。权限规则用来限制文件系统操作，subagent 的 `skills` 用来控制每个子 Agent 能看到哪些技能。排错时先查路径和 frontmatter，别上来怀疑模型，十有八九是配置写歪了。

## 权限：共享 skill 默认只读

共享 skill 库通常不该让 Agent 改。最小配置：

```python
from deepagents import FilesystemPermission, create_deep_agent

agent = create_deep_agent(
    model=model,
    backend=backend,
    skills=["/skills/"],
    permissions=[
        FilesystemPermission(
            operations=["write"],
            paths=["/skills/**"],
            mode="deny",
        )
    ],
)
```

这条规则只禁止写 `/skills/**`，不禁止读。Agent 还能发现和读取 `SKILL.md`，但不能改共享技能源。

## 权限：个人 skill 可以人工审批

如果你允许 Agent 帮用户维护个人 skill，又不想它直接乱写，可以用 `interrupt`：

```python
FilesystemPermission(
    operations=["write"],
    paths=["/skills/personal/**"],
    mode="interrupt",
)
```

`interrupt` 会要求 human-in-the-loop，通常还要配 `checkpointer`。这不是自动安全，只是写入前把人拉回来确认，别把它当权限系统的银弹。

## 子 Agent：自定义 subagent 要单独配 skills

通用子 Agent 会继承主 Agent 的 skills；自定义 subagent 不自动继承主 Agent 的 skills。要让自定义 subagent 使用某个 skill，直接在 subagent spec 里写：

```python
research_subagent = {
    "name": "researcher",
    "description": "Research with the shared LangGraph docs skill.",
    "system_prompt": "Use the configured skills when the task matches.",
    "skills": ["/skills/"],
}
```

权限规则不同：自定义 subagent 如果不写 `permissions`，会继承父 Agent 权限；如果写了，就会替换父 Agent 的权限。

## 最小可运行例子

代码见 [`../05_permissions_subagents_troubleshooting.py`](../05_permissions_subagents_troubleshooting.py)。

这个例子验证四件事：

- 正常 `/skills/` 能发现 `langgraph-docs`。
- 错误 `/missing-skills/` 会返回加载错误。
- `/skills/**` 写权限可以被 `deny`。
- 自定义 subagent spec 需要显式写 `skills`。

## 运行

在项目根目录执行：

```bash
uv run python deepagent_src/skills_teach/05_permissions_subagents_troubleshooting.py
```

预期输出：

```text
permissions and subagent config ok
```

## 排错清单

Skill 没激活，先查：

- `description` 是否具体，是否包含用户任务里的关键词。
- 用户任务是否真的匹配这个 skill，而不是你自己觉得应该匹配。
- 是否传了 `skills=["/skills/"]`。

Skill 启动时缺失，先查：

- backend root 和 `/skills/` 虚拟路径有没有搞混。
- `SKILL.md` 是否在 skill 子目录里。
- frontmatter 是否有 `name` 和 `description`。
- `name` 是否符合小写字母、数字、连字符，且和目录名一致。
- 同名 skill 是否被后面的 source 覆盖了，last source wins。

支持资源找不到，先查：

- `SKILL.md` 是否明确引用了资源文件。
- 资源路径是否相对 skill 根目录。
- sandbox 场景下资源是否同步进 sandbox。

## 常见误区

最常见的坑是把共享 skill 做成可写，然后让 Agent 自己改“真理来源”。艹，这种设计迟早把规范改成一坨浆糊。共享库只读，个人库可写或审批，这个边界要先划清楚。

## 到这里应该掌握什么

你现在应该能回答这五个问题：

- DeepAgent 怎么通过 `skills` 参数发现技能。
- 为什么启动时只加载 `name` 和 `description`。
- `references/`、`scripts/`、`assets/` 什么时候才会被用到。
- 三种 backend 下 skill 文件分别怎么进入 Agent。
- 生产里怎么限制 skill 写入，以及 custom subagent 怎么拿到 skills。
