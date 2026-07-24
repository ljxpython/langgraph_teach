# Deep Agents Skills 学习路线

## 学习主题

这部分学习 Deep Agents 里怎么使用 `skills`：把 skills 目录传给 `create_deep_agent`，让 `SkillsMiddleware` 在启动时发现技能，并在任务匹配时读取完整说明。

艹，重点别学歪了：我们不是专门学怎么写一套 Agent Skills 规范，而是学 DeepAgent 使用 skills 时的加载、触发、路径、资源和权限。

## 课程大纲

### 01 把 skills 接进 DeepAgent

目标：理解 `skills=["/skills/"]` 如何让 DeepAgent 从 backend 中发现可用技能。

### 02 Skill 激活与渐进披露

目标：理解 Agent 启动时只加载 `name` 和 `description`，任务匹配后才读取完整 `SKILL.md`。

### 03 使用支持资源目录

目标：理解 Agent 什么时候读取 `scripts/`、`references/`、`assets/`，以及这些文件如何配合任务执行。

### 04 不同后端下使用 skills

目标：理解 `StateBackend`、`StoreBackend`、`FilesystemBackend` 加载 skills 的差异和路径规则。

### 05 权限、子 Agent 与排错

目标：理解生产环境如何限制 skill 可见性、写权限、人工审批，以及自定义 subagent 为什么不会自动继承主 Agent 的 skills。

## 推荐学习顺序

1. 先把一个已有 skill 放到 backend 能看到的 `/skills/` 路径下。
2. 再把 `/skills/` 传给 `create_deep_agent(skills=[...])`。
3. 然后观察 discovery、激活读取、资源读取这三步。
4. 最后才学多后端、权限和 subagent。这个顺序最省脑子，也最不容易被一堆配置绕晕。

## 和已有 backend_teach 的关系

项目已有 `deepagent_src/backend_teach` 学后端存储。`skills_teach` 只学 skills 本身：

- 后端教程回答“文件放哪儿、怎么持久化”。
- skills 教程回答“DeepAgent 怎么加载、发现、触发和隔离专业说明”。

## 当前已完成章节

- [01 把 skills 接进 DeepAgent](01_skill_structure.md)
- [02 Skill 激活与渐进披露](02_progressive_disclosure.md)
- [03 使用支持资源目录](03_supporting_resources.md)
- [04 不同后端下使用 skills](04_backend_loading.md)
- [05 权限、子 Agent 与排错](05_permissions_subagents_troubleshooting.md)
- [06 综合案例：把 skills 串起来](06_comprehensive_case.md)
