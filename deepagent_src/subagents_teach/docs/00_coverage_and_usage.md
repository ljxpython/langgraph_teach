# 00 覆盖清单与常用程度

## 这套教程覆盖了吗

没有把官方文档里的每个高级分支都写成可运行脚本；那样会又臭又长，还会引入额外服务和依赖。当前教程把“最常用、能在本项目里真实跑通”的主线做成脚本，把需要部署、外部服务或额外运行时的内容写成讲义边界。

## 知识点覆盖表

| 知识点 | 覆盖方式 | 常用程度 | 说明 |
| --- | --- | --- | --- |
| 默认 `general-purpose` subagent | 01 章真实脚本 | 高 | 不传自定义同步 subagent 时自动存在，主 Agent 可通过 `task` 委派 |
| `task` 工具委派 | 01/02/03/04 章真实脚本 | 高 | 同步 subagent 的核心入口，主 Agent 会阻塞等待结果 |
| 自定义 `SubAgent` 字典 | 02 章真实脚本 | 高 | 生产里最常见配置方式 |
| `name` / `description` / `system_prompt` | 02 章讲义和脚本 | 高 | 三个必填字段，描述写不好主 Agent 就容易选错 |
| `tools` 最小化 | 02 章讲义和脚本 | 高 | 子 Agent 应只拿自己需要的工具 |
| runtime context 传播 | 03 章真实脚本 | 高 | 用户 ID、session、权限位常见都走这里 |
| `response_format` structured output | 04 章真实脚本 | 中高 | 当父 Agent 需要解析结果时很常用 |
| 禁用同步 subagents | 05 章真实脚本 | 中 | 简单 Agent 或禁止委派时用 |
| Async subagent 工具入口 | 06 章真实脚本 | 中 | 本地验证 `list_async_tasks`，启动后台任务需要 Agent Protocol 服务 |
| `model` 覆盖 | 讲义覆盖 | 中 | 子 Agent 可用不同模型；本项目为省成本没有额外跑第二模型 |
| `skills` 隔离 | 讲义覆盖 | 中 | general-purpose 继承主 Agent skills；自定义 subagent 不自动继承 |
| `permissions` 替换父权限 | 讲义覆盖 | 中 | 涉及文件系统权限，生产重要，入门先知道规则 |
| `middleware` / `interrupt_on` | 讲义覆盖 | 中低 | 人工审批和自定义行为需要时再学 |
| Streaming subagent 进度 | 讲义覆盖 | 中 | 调试体验好，但不是 subagent 的核心配置 |
| LangSmith `lc_agent_name` tracing | 讲义覆盖 | 中低 | 生产观测常用，本地无 LangSmith key 不跑 |
| `CompiledSubAgent` | 讲义覆盖 | 低到中 | 已有复杂 LangGraph 才需要；普通 subagent 用字典就够 |
| Dynamic subagents | 讲义覆盖 | 低 | 需要 interpreter middleware 和额外依赖，属于高级编排 |
| Async transport/deployment topology | 06 章讲义覆盖 | 中低 | 真正后台任务必须有 Agent Protocol 部署 |

## 最常用主线

真实项目里最常用的是这条：

```text
自定义 SubAgent 字典
-> 写清 name / description / system_prompt
-> 给最小 tools
-> 父 Agent 通过 task 委派
-> 子 Agent 返回简短总结或 JSON
-> 必要时通过 runtime context 传用户和权限信息
```

优先掌握 01、02、03、04。05 是控制开关，06 是异步高级能力。

## 不常用或高级能力

`CompiledSubAgent`、dynamic subagents、远端 async subagents、LangSmith 过滤和自定义 middleware 都不是第一天就该上手的东西。艹，先别把一辆自行车改成飞机；只有当任务复杂到普通字典 subagent 表达不下，或者真的需要后台任务、可取消、可追加指令时，再上这些高级能力。

## 学习判断

如果你只是想“让主 Agent 把某类任务交给专家处理”，学到 02 就够写代码。

如果你要“多用户、多权限、工具要读用户身份”，学到 03。

如果你要“父 Agent 继续程序化处理子 Agent 结果”，学到 04。

如果你要“长任务后台跑，用户继续聊天”，才进入 06 和 async 部署。

