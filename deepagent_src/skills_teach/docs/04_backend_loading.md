# 04 不同后端下使用 skills

## 学习目标

理解一句话：`skills=["/skills/"]` 只是告诉 DeepAgent 扫描哪个虚拟路径，真正的 skill 文件放哪儿由 backend 决定。

## 它是什么

DeepAgent 不直接关心文件是在磁盘、state 还是 store 里。它只通过 backend 读 `/skills/.../SKILL.md` 这种虚拟路径。backend 不同，塞 skill 文件的方式就不同，艹，这里混了就会出现“路径看着对但就是扫不到”的破问题。

## 三种常见方式

### FilesystemBackend

真实文件在磁盘：

```text
deepagent_src/skills_teach/workspace/skills/langgraph-docs/SKILL.md
```

DeepAgent 看到的虚拟路径：

```text
/skills/langgraph-docs/SKILL.md
```

核心代码：

```python
backend = FilesystemBackend(
    root_dir="deepagent_src/skills_teach/workspace",
    virtual_mode=True,
)
agent = create_deep_agent(
    model=model,
    backend=backend,
    skills=["/skills/"],
)
```

### StoreBackend

skill 文件存在 LangGraph store 里，适合跨 thread、跨会话复用：

```python
store.put(
    ("skills-teach",),
    "/skills/langgraph-docs/SKILL.md",
    create_file_data(skill_content),
)
backend = StoreBackend(
    store=store,
    namespace=lambda _rt: ("skills-teach",),
)
```

这里的 key 仍然是 `/skills/langgraph-docs/SKILL.md`。namespace 负责隔离不同用户、团队或租户。

### StateBackend

skill 文件存在当前 thread 的 state 里，适合临时实验：

```python
agent.invoke(
    {
        "messages": [{"role": "user", "content": "hello"}],
        "files": {
            "/skills/langgraph-docs/SKILL.md": create_file_data(skill_content),
        },
    },
    {"configurable": {"thread_id": "skills-state-backend-demo"}},
)
```

注意：`StateBackend` 不能在图执行外直接 `read`，它需要 LangGraph execution context。预填文件要走 `invoke(files={...})`，并且内容要用 `create_file_data()` 包一下，裸字符串不行。

## 最小可运行例子

代码见 [`../04_backend_loading.py`](../04_backend_loading.py)。

这个例子用同一份 `SKILL.md` 验证三件事：

- `FilesystemBackend` 能从固定 workspace 扫到 skill。
- `StoreBackend` 能从 `InMemoryStore` 的 namespace 扫到 skill。
- `StateBackend` 能通过 `invoke(files={...})` 把 skill 文件交给 Agent。

## 运行

在项目根目录执行：

```bash
uv run python deepagent_src/skills_teach/04_backend_loading.py
```

预期输出：

```text
backend loading ok
```

## 常见误区

最常见的坑是以为 `/skills/` 是本机绝对路径。不是。它是 backend 里的虚拟路径；只有 `FilesystemBackend(virtual_mode=False)` 时，绝对路径才会绕过 `root_dir`，这在教学和生产里都容易埋雷。

## 边界

这章只讲 skill 文件如何进入不同 backend。权限、只读共享库、个人可写 skill、subagent 继承规则放下一章处理。

## 下一章

下一章学“权限、子 Agent 与排错”：怎么防止 Agent 改共享 skill，以及为什么自定义 subagent 默认看不到主 Agent 的 skills。
