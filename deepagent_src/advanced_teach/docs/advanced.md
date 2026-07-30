# Deep Agents 高级能力教学

这个目录继续学习 Deep Agents 里更靠近生产的能力。每章只做一个核心概念，代码放在 `deepagent_src/advanced_teach/`，讲义放在 `deepagent_src/advanced_teach/docs/`。

## 课程路线

1. `01_interpreters_ptc`：Interpreter 与 Programmatic Tool Calling，让 Agent 用代码批量编排工具调用。
2. `02_sandbox_lifecycle`：线程级 sandbox 的创建、复用、隔离和生产 TTL 思路。
3. `03_event_streaming`：Deep Agents 的 messages、tools、values、output 流怎么给前端用。
4. `04_fault_tolerance`：工具可恢复错误、重试、限流、fallback、HITL 的生产容错分层。
5. `05_going_to_production`：graph factory、thread-scoped sandbox、`thread_id` 与 `context`、部署边界。
6. `06_rubric_evaluation`：运行时 LLM-as-a-judge、rubric revision 与离线/线上 evaluation 的边界。
7. `07_multimodal`：通过 `read_file` 读取图片、PDF 等多模态文件，并理解模型支持边界。
8. `08_model_capability_routing`：模型能力注册表、运行时模型选择与 provider 能力边界。

## 当前版本边界

本项目当前本地环境已升级到 `deepagents 0.7.0b2`，并安装了 `deepagents[quickjs]`。`0.7.0b2` 是 beta 预发布版，后续每章按官方最新文档和本地可验证 API 编写；遇到 beta API 变动时，以本地签名和真实运行结果为准。

## 第一章运行

```bash
uv run python -m deepagent_src.advanced_teach.01_interpreters_ptc
```

当前项目已经安装 `deepagents[quickjs]`，可以直接运行第一章。如果换到新环境后看到缺少 `langchain_quickjs`，安装命令是：

```bash
uv add "deepagents[quickjs]"
```

这会改项目依赖和锁文件，执行前需要确认。本项目已确认升级，`pyproject.toml` 中依赖为 `deepagents[quickjs]==0.7.0b2`。

## 第二章运行

```bash
uv run python -m deepagent_src.advanced_teach.02_sandbox_lifecycle
```

这章使用 `LocalShellBackend` 做本地最小验证。它会真实执行 `pwd`，但只在临时目录里创建文件，程序结束后临时目录会被清理。生产环境不要用 `LocalShellBackend`，要换成 `LangSmithSandbox` 或其他隔离 sandbox provider。

## 第三章运行

```bash
uv run python -m deepagent_src.advanced_teach.03_event_streaming
```

这章会触发一次真实 LLM 调用，并通过 `stream_events(version="v3")` 观察模型消息、工具事件、状态快照和最终输出。当前 `v3` streaming protocol 在本地 `deepagents 0.7.0b2` / LangGraph 中仍会提示 experimental warning，教学代码以真实运行行为为准。

## 第四章运行

```bash
uv run python -m deepagent_src.advanced_teach.04_fault_tolerance
```

这章会触发一次真实 LLM 调用，并演示 `ToolErrorMiddleware` 如何把可恢复工具异常转成 `ToolMessage`，让模型修正参数后重试。未知异常不要兜底吞掉，应继续暴露给开发者。

## 第五章运行

```bash
uv run python -m deepagent_src.advanced_teach.05_going_to_production
```

这章用 `LocalShellBackend` 在临时目录模拟 thread-scoped sandbox，并真实调用一次 Agent 验证 `write_file` 发生在 `alpha` 线程的环境。生产环境要换成 `LangSmithSandbox` 或其他隔离 provider，并通过 async graph factory 从 `configurable.thread_id` 查找或创建 sandbox。

## 第六章运行

```bash
uv run python -m deepagent_src.advanced_teach.06_rubric_evaluation
```

这章会真实调用工作 Agent 和 LLM grader，使用 `RubricMiddleware` 检查 rubric。当前 `deepagents 0.7.0b2` 中该 middleware 是 beta；示例显式约束 grader 的结构化输出字段，并以本地验证结果为准。

## 第七章运行

```bash
uv run python -m deepagent_src.advanced_teach.07_multimodal
```

这章用同一张实拍机场照片比较直接图片输入和 Agent `read_file`。它验证直接视觉能力，并探测 provider 是否支持多模态 tool result；正确答案仅在断言中，不写进 prompt。生产环境还应限制上传大小、MIME type、页数和媒体时长，并确认目标模型支持对应模态和 tool result。

## 第八章运行

```bash
uv run python -m deepagent_src.advanced_teach.08_model_capability_routing
```

这章会真实调用一次 `gpt-5.5`，验证 `wrap_model_call` 根据 runtime context 选择 allowlist 中的模型。它还会在本地拒绝一个不具备 `vision_input` 能力的路由请求；模型能力由应用维护，不能只凭模型名称或营销说明猜测。
