# 04 后台整理 Memory

## 学习目标

理解一句话：memory 可以在对话中热更新，也可以在对话结束后由后台任务统一整理。

## 它是什么

Hot path 是 Agent 在当前对话里直接写 memory，好处是立刻生效，坏处是增加延迟和干扰主任务。Background consolidation 是另一个任务在对话后整理近期历史，把真正长期有用的信息合并进 memory。它解决的是“别让主对话一边办事一边整理笔记整理到手忙脚乱”。

## 最小可运行例子

代码见 [`../04_background_consolidation.py`](../04_background_consolidation.py)。

这个例子不调用 LangSmith cron，也不搜真实历史；它只演示后台整理的核心动作：把新观察合并进 `AGENTS.md`，并避免重复条目。

## 运行

```bash
uv run python deepagent_src/memory_teach/04_background_consolidation.py
```

预期输出：

```text
background consolidation ok
```

## 常见误区

后台整理不是越频繁越好。整理频率应该接近真实使用频率，否则就是烧 token 做无用功。
