# 01 Memory 启动加载

## 学习目标

理解一句话：DeepAgent 的 long-term memory 是文件，`memory=[...]` 指定哪些文件会被加载进系统提示词。

## 它是什么

Memory 保存跨对话都应该保留的上下文，比如用户偏好、项目约定、组织政策。Deep Agents 的 memory 由 `MemoryMiddleware` 加载，默认格式是 Markdown 文件，常见文件名是 `AGENTS.md`。它解决的是“下一次对话还能记住稳定信息”，不是保存当前 thread 的临时草稿。

## 最小结构

```text
memory_teach/workspace/
└── memories/
    └── AGENTS.md
```

Agent 接入时的核心形态：

```python
graph = create_deep_agent(
    model=model,
    backend=backend,
    memory=["/memories/AGENTS.md"],
)
```

## 最小可运行例子

代码见 [`../01_memory_loading.py`](../01_memory_loading.py)。

这个例子读取固定目录里的 `workspace/memories/AGENTS.md`，再用 `MemoryMiddleware` 生成会注入系统提示词的 memory 片段。

## 运行

```bash
uv run python deepagent_src/memory_teach/01_memory_loading.py
```

预期输出：

```text
memory loading ok
```

## 常见误区

最常见的坑是把 memory 当成 skills。memory 是启动时加载的长期上下文；skills 是按任务匹配后才读取的能力说明。
