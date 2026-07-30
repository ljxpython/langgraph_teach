# 07 多目录加载多个 Skills

## 学习目标

理解同一个 Deep Agent 如何从多个互不相同的物理目录发现 Skills，并在一个真实任务中按需读取多份 `SKILL.md`。

## 目录结构

两份 Skill 不在同一个 workspace：

```text
skill_sources/
├── documentation/
│   └── langgraph-answer/SKILL.md
└── release/
    └── release-check/SKILL.md
```

不要为了满足 `skills=` 把文件复制到统一目录。`CompositeBackend` 可以将不同物理后端挂载到统一的 Agent 虚拟文件系统：

```python
backend = CompositeBackend(
    default=StateBackend(),
    routes={
        "/documentation-skills/": FilesystemBackend(
            root_dir=DOCUMENTATION_DIR, virtual_mode=True
        ),
        "/release-skills/": FilesystemBackend(
            root_dir=RELEASE_DIR, virtual_mode=True
        ),
    },
)

graph = create_deep_agent(
    model=get_gpt_model(disable_tool_streaming=True),
    backend=backend,
    skills=["/documentation-skills/", "/release-skills/"],
)
```

路由会剥掉虚拟前缀。例如 Agent 读取：

```text
/documentation-skills/langgraph-answer/SKILL.md
```

实际由 `DOCUMENTATION_DIR` 对应的 backend 读取：

```text
/langgraph-answer/SKILL.md
```

## 真实调用链路

```text
create_deep_agent(skills=[source A, source B])
  -> SkillsMiddleware 分别扫描两个 source 的 frontmatter
  -> 模型先看到两个 Skill 的名称、描述和虚拟路径
  -> 用户任务同时匹配两项能力
  -> 模型调用 read_file 读取 source A 的完整 SKILL.md
  -> 模型调用 read_file 读取 source B 的完整 SKILL.md
  -> 最终回答同时遵循两份完整指令
```

实例化时仍然只扫描元数据，不会把两个 `SKILL.md` 正文全部塞进模型上下文。正文是在模型确认任务匹配后通过 `read_file` 加载的。

## 运行

在项目根目录执行：

```bash
uv run python -m deepagent_src.skills_teach.07_multi_source_skills
```

该命令会真实调用项目配置的 `gpt-5.5`，产生少量 API 费用。脚本不是只检查内部函数，它会断言真实消息轨迹中出现以下两个读取路径：

```text
/documentation-skills/langgraph-answer/SKILL.md
/release-skills/release-check/SKILL.md
```

最终回答还必须同时包含 `架构结论：`、`发布检查：` 和 `通过`。成功时输出：

```text
multi-source skills real call ok
```

## 边界

- `skills` 中填写的是 Agent 虚拟路径，不是宿主机绝对路径。
- 每个 source 下仍需保持 `<skill-name>/SKILL.md` 结构。
- 多 source 解决发现和路由，不等于权限隔离；本例额外禁止写两个 Skill 挂载。
- 多租户敏感 Skill 应使用独立 `StoreBackend` namespace、sandbox 或远程 backend，不能只靠目录命名隔离。
- 自定义 subagent 不会自动继承主 Agent 的 sources，需要在 subagent 配置中显式传入。
