# Deep Agents Memory 学习路线

## 学习主题

这部分学习 Deep Agents 的长期 memory：把持久上下文放进 memory 文件，由 backend 控制文件存储和访问范围，再通过 `memory=[...]` 注入 Agent。

艹，先别把 memory 和 checkpoint 混成一锅。checkpoint 管当前 thread 的短期状态；memory 是跨对话保留的长期信息。

## 课程大纲

### 01 Memory 启动加载

目标：理解 `memory=["/memories/AGENTS.md"]` 会让 Agent 在启动时加载 memory 文件并注入系统提示词。

### 02 Agent scope 与 User scope

目标：理解同一个 `/memories/AGENTS.md` 在不同 `StoreBackend` namespace 下会变成不同记忆空间。

### 03 只读与可写 Memory

目标：理解 shared policy 应该只读，个人 memory 可以写或人工审批。

### 04 后台整理 Memory

目标：理解 hot path 直接写 memory 和 background consolidation 的取舍。

### 05 综合案例：真实 Agent 读取 Memory

目标：把 memory 文件、backend、namespace、权限和实时输出串成一个真实 Agent 调用。

### 06 生产化：动态用户 Memory 设计

目标：理解多用户动态新增时如何用 namespace 隔离每个用户的长期 memory。

## 推荐学习顺序

1. 先分清短期状态和长期 memory。
2. 再看 memory 文件如何加载进系统提示词。
3. 然后学 namespace 如何隔离用户或 Agent。
4. 最后加权限和后台整理策略。

## 和已有教程的关系

- `backend_teach`：讲文件到底存在哪里。
- `skills_teach`：讲按需加载的过程说明。
- `memory_teach`：讲始终相关的长期上下文如何跨会话保留。

## 当前章节

- [01 Memory 启动加载](01_memory_loading.md)
- [02 Agent scope 与 User scope](02_scoped_memory.md)
- [03 只读与可写 Memory](03_memory_permissions.md)
- [04 后台整理 Memory](04_background_consolidation.md)
- [05 综合案例：真实 Agent 读取 Memory](05_comprehensive_case.md)
- [06 生产化：动态用户 Memory 设计](06_production_user_memory_design.md)
