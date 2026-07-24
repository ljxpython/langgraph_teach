# 03 使用支持资源目录

## 学习目标

理解一句话：`references/`、`scripts/`、`assets/` 是 skill 的按需资源，DeepAgent 不会在启动时自动读取它们。

## 它是什么

支持资源目录用来放 `SKILL.md` 放不下、也不该每次都加载的东西。`references/` 放详细说明，`scripts/` 放可执行辅助逻辑，`assets/` 放模板和静态文件。Agent 先读 `SKILL.md`，只有正文指令说需要这些资源时，才继续读或执行它们。

## 示例目录

```text
skills/langgraph-docs/
├── SKILL.md
├── references/
│   └── resource-map.md
├── scripts/
│   └── show_resource_map.py
└── assets/
    └── report-template.md
```

`SKILL.md` 里要明确告诉 Agent 什么时候用资源：

```md
Use supporting resources only when the task needs them:

- Read `references/resource-map.md` when you need the resource loading rules.
- Run `scripts/show_resource_map.py` when you need a local resource summary.
- Copy or adapt `assets/report-template.md` when the user asks for a report format.
```

不写这几句，Agent 不会自己凭空知道这些文件该怎么用。别指望目录名能读心，代码没这么玄乎。

## 最小可运行例子

代码见 [`../03_supporting_resources.py`](../03_supporting_resources.py)。

这个例子验证三件事：

- discovery 阶段没有加载 `references/` 和 `assets/` 的正文。
- 完整 `SKILL.md` 会告诉 Agent 支持资源在哪里。
- 资源文件可以通过 backend 的虚拟路径单独读取。

## 运行

在项目根目录执行：

```bash
uv run python deepagent_src/skills_teach/03_supporting_resources.py
```

预期输出：

```text
supporting resources ok
```

## 什么时候用哪个目录

`references/`：放会被 Agent 阅读的长文档，比如 API 细则、业务规则、错误码表、风格指南。

`scripts/`：放可执行逻辑，比如校验脚本、转换脚本、检索脚本。脚本能不能执行取决于 Agent 有没有 shell 或 sandbox 能力；只有能读文件不代表能运行脚本。

`assets/`：放模板、schema、图片、示例文件这类静态资源。Agent 通常是读取、复制或改写它，不把它当流程说明。

## 常见误区

最常见的坑是把一大坨参考资料直接塞进 `SKILL.md`。这样 skill 一激活就吃掉大量上下文，等于把 progressive disclosure 自己打烂，艹，费钱还费脑子。

## 边界

这章只验证资源“可被按需读取”。脚本执行要看后端和运行环境；普通 backend 能读脚本文件，真正执行脚本通常需要 shell 或 sandbox。

## 下一章

下一章学“不同后端下使用 skills”：同样的 `/skills/`，在 `StateBackend`、`StoreBackend`、`FilesystemBackend` 下到底怎么放文件。
