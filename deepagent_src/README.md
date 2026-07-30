# Deep Agents 学习目录

这个目录沉淀 Deep Agents、LangChain、LangGraph 相关教学代码。每个子目录负责一个主题，代码尽量保持最小可运行，讲义通常放在各自的 `docs/` 目录下。

## 建议学习顺序

1. `skills_teach/`：Skills 的加载、选择、真实调用与多 workspace 案例。
2. `memory_teach/`：`AGENTS.md` memory、持久偏好和上下文注入。
3. `context_engineering_teach/`：上下文裁剪、offload、summarization、长任务控制。
4. `backend_teach/`：虚拟文件系统 backend、本地 backend、sandbox backend 的边界。
5. `subagents_teach/`：默认 subagent、自定义 subagent、隔离上下文和任务委派。
6. `human_loop_teach/`：HITL interrupt、审批、恢复运行。
7. `frontend_teach/`：前端 `useStream`、文件浏览、diff、工具事件和集成 UI。
8. `profiles_teach/`：harness profile、默认工具裁剪和模型能力差异。
9. `advanced_teach/`：模型能力注册表、运行时路由、流式事件、多模态等进阶主题。
10. `middleware_teach/`：LangChain middleware、Deep Agents 默认栈、类中间件与 `state_schema`。
11. `a2a_teach/`：Agent-to-Agent 通信、协议边界和真实调用。

## 运行方式

优先进入项目根目录运行：

```bash
uv run python -m deepagent_src.middleware_teach.06_class_state_schema
```

真实模型章节会读取项目已有模型配置，例如 `CHATGPT_API_KEY` / `CHATGPT_API_URL`。本地机制验证章节一般使用 fake model，不产生外部调用。

## 学习判断

Deep Agents 本质是 LangChain agent loop 加上一组默认 middleware 和后端能力。学习时按这个顺序拆开看最省事：

1. LangChain 负责模型、消息、工具和 middleware。
2. LangGraph 负责状态、图执行、stream、interrupt、checkpoint。
3. Deep Agents 负责把文件系统、skills、memory、subagents、sandbox、HITL 这些能力预装成 agent harness。

别把所有能力都理解成 prompt 拼接。prompt 只是输入层，真正的工具裁剪、状态扩展、审批、流式事件和文件系统访问，大多发生在 middleware、backend 或 LangGraph runtime 里。
