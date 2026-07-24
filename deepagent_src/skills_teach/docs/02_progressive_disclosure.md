# 02 Skill 激活与渐进披露

## 学习目标

理解一句话：DeepAgent 启动时只看到 skill 摘要，只有模型判断任务匹配时，才会用 `read_file` 读取完整 `SKILL.md`。

## 它是什么

渐进披露就是分层加载上下文。第一层是 `name` 和 `description`，用于让模型知道有哪些 skills；第二层是完整 `SKILL.md`，只在需要时读取；第三层是 `scripts/`、`references/`、`assets/`，只有 `SKILL.md` 指令要求时才继续读。它解决的是上下文膨胀，妈的，不然几十个 skill 一启动就把窗口塞爆。

## 三层加载

```text
Agent 启动
  -> 读取每个 SKILL.md 的 frontmatter
  -> 系统提示词里出现 name、description、SKILL.md 路径

用户任务匹配某个 skill
  -> 模型调用 read_file 读取对应 SKILL.md
  -> 按正文 instructions 执行

instructions 指向支持资源
  -> 再读取 references/、assets/ 或执行 scripts/
```

## 最小可运行例子

代码见 [`../02_progressive_disclosure.py`](../02_progressive_disclosure.py)。

这个例子读取固定目录里的 `deepagent_src/skills_teach/workspace/skills/langgraph-docs/SKILL.md`，文件正文里有一个特殊标记 `FULL_INSTRUCTIONS_ONLY_AFTER_READ`，然后验证两件事：

- discovery 文本里只有 skill 名称、描述和读取路径，不包含正文标记。
- 手动读取 `/skills/langgraph-docs/SKILL.md` 后，才看得到正文标记。

这就是 DeepAgent 使用 skills 的关键：先发现，再按需读取。

## 运行

在项目根目录执行：

```bash
uv run python deepagent_src/skills_teach/02_progressive_disclosure.py
```

预期输出：

```text
progressive disclosure ok
```

## 代码中的关键点

```python
skills, error = _list_skills_with_errors(backend, "/skills/")
middleware = SkillsMiddleware(backend=backend, sources=["/skills/"])
discovery_text = middleware._format_skills_list(skills)
```

`discovery_text` 对应 Agent 启动时能看到的技能摘要，它会提示：

```text
Read `/skills/langgraph-docs/SKILL.md` for full instructions
```

但它不会包含完整 `SKILL.md` 正文。

## 常见误区

最常见的误区是以为只要传了 `skills=["/skills/"]`，Agent 就已经读完整个技能目录了。错，启动阶段只读 frontmatter；完整说明和支持资源都要等任务匹配后再按需读取。

## 边界

这个脚本验证的是框架加载机制，不模拟模型“是否应该激活某个 skill”的判断。模型判断属于 LLM 行为，稳定教学里别拿它做断言，不然一次过一次挂，烦死人。

## 下一章

下一章学“使用支持资源目录”：`references/` 什么时候读，`scripts/` 什么时候跑，`assets/` 什么时候只是被复制或引用。
