# 07 MCP + Skills 严格选择

## 它是什么

前端只提交后端白名单中的 MCP Tool ID 和 Skill ID。MCP tools 在模型调用前被硬过滤；Skills 不再靠系统提示词劝模型遵守，而是通过 graph factory 动态注册或独立 backend 物理隔离。

当前页面里的 `1 Factory` 和 `2 Isolation` **都是 graph factory**，都会在每次 run 时调用 `create_deep_agent(...)`。二者比较的是 Skill 的隔离强度，不是“动态图与静态图”：

- `1 Factory`：动态决定是否注册 `SkillsMiddleware`，再用文件权限阻止猜路径读取。
- `2 Isolation`：动态决定 backend，未选择的 Skill 在该 backend 中物理不存在。

真正生产中更常见的“静态图 + 运行时选择”见后文。普通 Tool/Skill 选择不必为了动态而每轮重建 Agent。

## Graph、Thread 与 Run 的生命周期

这三个概念不能混在一起：

| 对象 | 静态 graph | graph factory |
| --- | --- | --- |
| Graph/Agent 构建 | `langgraph dev` 导入模块时构建，当前 worker 后续复用 | worker 处理 run 时调用 factory；读取 schema、thread state 等接口也可能调用 |
| Thread 创建 | 只创建对话状态和 checkpoint，不创建 Agent 实例 | 同左 |
| Run 执行 | 当前 worker 使用已构建 graph 执行 | factory 返回本轮 graph 后执行 |
| 多 worker/副本 | 每个进程各有一个 graph 实例，不是整个集群共享一个 Python 对象 | 每个 worker 分别调用 factory |

因此静态 graph 不是“每个线程一个 Agent”，而是同一 worker 中的多个线程共享 graph 定义，各自通过 `thread_id` 读取独立状态。开发模式代码变化触发 reload 后，进程和静态 graph 才会重建。

官方建议多数定制优先在固定拓扑的节点或 middleware 中读取运行时 config，而不是动态改变整个 graph。graph factory 更适合按用户连接 MCP、解析不同 backend、创建 sandbox 等必须依赖本轮资源的场景。

## 前端提交

Skill 选择必须进入 run config，因为 LangGraph 在输入 state 进入图之前调用 graph factory：

```tsx
stream.submit(
  {
    messages: [{ type: "human", content }],
    enabled_mcp_tools: ["teaching_lookup_exchange_rate"],
  },
  {
    config: { configurable: { enabled_skills: ["currency-guide"] } },
  },
);
```

浏览器不能提交 Skill 路径、MCP command、server URL、密钥或包名。后端只接受 `currency-guide` 这类 ID，并映射到受信资源。

## 方案 1：动态构建 Agent

`mcp_skills_factory_agent(config)` 是 LangGraph async graph factory。它先校验 `configurable.enabled_skills`，再决定是否把 Skill source 注册给 Deep Agent：

```python
async def mcp_skills_factory_agent(config: RunnableConfig):
    skills, permissions = factory_skill_settings(
        config.get("configurable", {}).get("enabled_skills", [])
    )
    return build_mcp_skills_graph(
        await load_mcp_tools(),
        backend=FilesystemBackend(root_dir=FRONTEND_WORKSPACE, virtual_mode=True),
        skills=skills,
        permissions=permissions,
    )
```

选中时传 `skills=["/skills/"]`，`SkillsMiddleware` 才会扫描并注入 `currency-guide` discovery。未选时传 `skills=None`，图里根本没有 `SkillsMiddleware`；同时 `FilesystemPermission` 拒绝 `/skills/**`，防止模型猜到路径后调用 `read_file`。

这个方案适合受信 Skill 集合较小、每次运行允许重建图的应用。当前教学项目只有一个 Skill，所以选择结果是启用或禁用整个受信 source；多 Skill 项目应把选中的 Skill 复制、挂载或路由到本轮专用 discovery 根，不能把单个 `SKILL.md` 路径直接传给 `skills=`。

## 方案 2：独立 Backend 隔离

`mcp_skills_isolated_agent(config)` 根据白名单选择 backend：

```python
backend, skills = isolated_skill_settings(enabled_skill_ids)

# 已选：backend root 包含 /skills/currency-guide/SKILL.md
# 未选：backend root 指向独立 empty-skills 目录
return build_mcp_skills_graph(
    await load_mcp_tools(),
    backend=backend,
    skills=skills,
)
```

未选时 Skill 文件根本不在本轮 backend 中。因此不只是 discovery 为空：即使绕开 Agent 文件工具直接调用 backend，读取 `/skills/currency-guide/SKILL.md` 也会返回 `path_not_found`。这才是租户隔离、敏感 Skill 和不同权限域应采用的边界。生产中通常把空目录替换成租户专属 sandbox、store namespace 或只读挂载。

## 两种方案对比

| 项目 | 方案 1：Graph factory | 方案 2：Backend isolation |
| --- | --- | --- |
| 未选 Skill discovery | 不注册 `SkillsMiddleware` | 不注册且 backend 中不存在 |
| 猜路径读取 | 文件工具权限拒绝 | backend 直接返回不存在 |
| 适用场景 | 同一可信资源池的动态能力组合 | 租户、敏感数据、强隔离 |
| 成本 | 每轮按 config 构图 | 每轮解析或连接对应 backend |
| 安全边界 | graph 结构 + 文件工具权限 | 存储可见性 |

两种方案都没有拼接“Only use selected skills”之类的系统提示词。系统消息里出现 Skills discovery 是 Deep Agent 原生 `SkillsMiddleware` 的渐进披露机制，不是授权机制。

## Deep Agents 原生 Skill 到底怎样加载

`SkillsMiddleware` 分两步工作：

1. `before_agent` 扫描每个 Skill 目录的 `SKILL.md`，读取 `name`、`description` 和 `path`，把这些元数据写入 `skills_metadata`。同一 thread 后续轮次已经有该字段时会跳过扫描。
2. `wrap_model_call` 把 Skill 元数据列表追加到系统消息。模型只先看到名称、描述和路径；当任务匹配某个描述时，模型自行决定调用 `read_file` 读取完整 `SKILL.md`。

所以“先把 Skill 描述放进系统提示词”是对的，但“自动触发 Skill”不准确。框架不会像事件监听器一样确定性触发某个 Skill；是 LLM 根据描述判断，然后产生文件工具调用。完整 Skill 正文默认不会全部塞进首次模型请求，这就是 progressive disclosure。

还要注意，原生 `SkillsMiddleware` 会把所发现的全部 Skill 元数据放进系统消息，而且 `skills_metadata` 默认在同一 thread 复用。若前端每轮都能切换 Skill，不能直接把全部 Skill 交给它再指望模型只用勾选项。

## 生产常用：静态图 + 前端能力选择

用户在前端选择 Tool，并且只有选择后才能使用关联 Skill，可以把 Tool 与 Skill 组合成后端定义的“能力包”：

```python
CAPABILITIES = {
    "currency": {
        "tools": {"teaching_lookup_exchange_rate"},
        "skills": {"currency-guide"},
    }
}
```

前端只能提交能力包 ID：

```tsx
stream.submit({
  messages: [{ type: "human", content }],
  enabled_capabilities: ["currency"],
});
```

后端使用一个启动时创建的静态 Agent，并在每次 run/model call 做三件事：

```text
前端 enabled_capabilities
  -> 后端白名单展开为 allowed_tool_ids + allowed_skill_ids
  -> wrap_model_call 只向模型暴露允许的 Tool schema
  -> dynamic skill middleware 只注入允许的 Skill 描述
  -> 模型按需调用 load_skill(skill_id)
  -> load_skill 再校验 allowed_skill_ids，成功后才返回完整 SKILL.md
```

这套方案的关键不是“把选择拼进提示词”，而是三层职责分开：

| 层 | 作用 | 是否安全边界 |
| --- | --- | --- |
| Skill 描述动态注入 | 只让模型发现已选择 Skill | 否，只是可见性和上下文优化 |
| `load_skill(skill_id)` | 按需返回完整 Skill 内容 | 是，必须校验白名单 |
| backend/namespace/sandbox | 隔离敏感文件和租户资源 | 是，强隔离场景使用 |

`load_skill` 是静态注册的一把受控入口，Agent 不需要重建。未选 Skill 时，即使模型猜到 ID，工具也会拒绝；若连 `load_skill` 都不需要显示，可以和其他 Tool 一样在 `wrap_model_call` 中隐藏，但执行入口仍必须鉴权。

MCP 也采用同一原则：应用启动时建立远程连接或连接池并缓存 Tool catalog，每次 run 只过滤模型可见工具和执行权限。不要像本教学示例一样每轮启动 stdio MCP 子进程，除非是本地桌面 Agent、一次性 sandbox 或明确需要进程隔离。

### 方案 3：静态 Agent 的实际实现

本项目的 `mcp_skills_static_agent` 是模块顶层对象，不是 factory 函数：

```python
mcp_skills_static_agent = create_deep_agent(
    model=get_frontend_model(disable_tool_streaming=True),
    tools=[load_skill],
    middleware=[StaticCapabilityMiddleware()],
    state_schema=McpSkillsState,
    permissions=[
        FilesystemPermission(
            operations=["read", "write"],
            paths=["/skills/**"],
            mode="deny",
        )
    ],
)
```

`langgraph dev` 导入模块时只构建一次该图；创建 thread 不会创建新的 Agent。前端在每次提交时只发送能力包 ID：

```tsx
stream.submit({
  messages: [{ type: "human", content }],
  enabled_capabilities: ["currency"],
});
```

`StaticCapabilityMiddleware.awrap_model_call` 将 `currency` 展开为 MCP Tool 与关联 Skill。它异步懒加载并缓存 MCP catalog，只把允许的 MCP Tool schema 加到本轮 `request.tools`；同时只把已选 Skill 的 ID 和描述追加到系统消息。没有选择能力包时，两者都不会进入模型上下文。

动态加入 model request 的 MCP Tool 并不在静态 ToolNode 注册表中，因此 `awrap_tool_call` 还要按官方 runtime tool registration 模式把真实 Tool 放回执行请求。这里会再次检查 capability，不能只相信模型上一步看到的 schema。

`load_skill` 始终静态注册在图中，但只有选中 Skill 时才向模型显示。即使模型或外部调用猜到 `currency-guide`，工具内部仍从当前 run state 重新展开 capability 并鉴权：

```python
@tool
def load_skill(skill_id: str, runtime: ToolRuntime) -> str:
    _, enabled_skills = static_capability_settings(
        runtime.state.get("enabled_capabilities", [])
    )
    return load_selected_skill(skill_id, enabled_skills)
```

静态 Agent 同时禁止通用文件工具读取 `/skills/**`，完整正文只能经过 `load_skill`。这使“描述注入”“正文加载”“文件权限”成为三条独立控制，而不是靠模型自觉。

### 静态方案适用边界

| 需求 | 推荐方式 |
| --- | --- |
| 前端选择普通 Tools | 静态 graph + `wrap_model_call` 过滤 + Tool 执行鉴权 |
| 前端选择普通 Skills | 静态 graph + 选中描述注入 + 受控 `load_skill` |
| Tool 与 Skill 必须成组启用 | 后端 capability 白名单统一展开 |
| 每用户不同 MCP 服务器/OAuth | graph factory，或长期连接管理器按用户解析 |
| 每线程独立 sandbox | graph factory 解析或创建 thread-scoped sandbox |
| 敏感 Skill 必须物理不可见 | backend namespace、只读挂载或 sandbox 隔离 |

因此生产默认优先静态 graph；只有底层资源本身必须按用户、线程或租户变化时才使用 factory。即使使用 factory，也应复用 MCP 连接、Skill registry 和 sandbox，避免每个 run 重复做昂贵初始化。

## 真实 MCP 链路

```text
graph factory
  -> MultiServerMCPClient 启动受信 FastMCP stdio server
  -> get_tools() 得到 teaching_lookup_exchange_rate
  -> create_deep_agent 注册 MCP tool
  -> select_mcp_tools 按 graph state 硬过滤 request.tools
```

MCP Tool 与 Skill 使用不同选择通道：Tool 是模型可调用函数，适合在 `wrap_model_call` 中过滤；Skill 是 discovery、指令和资源，必须在 graph/backend 边界选择。

## 运行与预期现象

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，进入 `07 MCP + Skills`：

1. 选择 `1 Factory`，启用 Skill：会看到汇率 MCP tool call 和读取 `SKILL.md`。
2. 选择 `1 Factory`，关闭 Skill：本轮没有 Skills discovery，猜路径也被文件权限拒绝。
3. 选择 `2 Isolation`，关闭 Skill：本轮 backend 不包含原 Skill，直接读取也失败。
4. 关闭 MCP Tool：模型看不到汇率工具；Skill 即使启用也不能凭空产生真实汇率。
5. 选择 `3 Static`：勾选 MCP Tool 会联动启用 Currency Skill；运行轨迹依次显示真实 MCP Tool 和 `load_skill`。
6. 在 `3 Static` 关闭能力包：MCP schema、Skill 描述与 `load_skill` 都不会向模型暴露；即使猜 ID，执行层仍拒绝。

每次提交都会真实调用 `gpt-5.5`，会产生少量 API 费用。Factory 与 Isolation 每次构图都会获取 MCP tools；Static 只在首次启用 capability 时启动 stdio MCP 并缓存 catalog。生产环境应复用远程连接，并配置 OAuth、连接池、超时和 TTL。

## 常见误区

- `skills=["/skills/currency-guide/SKILL.md"]` 是错的；Deep Agent 要扫描包含 Skill 子目录的 source 根。
- 不要把 Skill 当普通 Tool 过滤，它们进入模型上下文的生命周期不同。
- 不要把 prompt 当 RBAC；权限边界必须落实在 graph、filesystem tool 或 backend。
- 多租户不能共享一个能读到全部 Skill 的 backend 后再靠模型自觉。
- 同一 thread 改变 Skill 集合时必须由 graph factory 为每次 run 重建对应图，避免复用旧 `skills_metadata`。
- “动态 Skill”不等于“动态创建 Agent”；静态 Agent 也能动态控制 Skill 的发现、加载和授权。
- 只过滤系统消息不等于禁用 Skill；必须在 `load_skill`、文件工具或 backend 再做权限校验。

## 官方资料

- MCP: `https://docs.langchain.com/oss/python/langchain/mcp`
- Dynamic tool selection: `https://docs.langchain.com/oss/python/langchain/tools#dynamic-tool-selection`
- Dynamic middleware: `https://docs.langchain.com/oss/python/langchain/middleware/custom#dynamically-selecting-tools`
- Deep Agents Skills: `https://docs.langchain.com/oss/python/deepagents/skills`
- Rebuild graph at runtime: `https://docs.langchain.com/langsmith/graph-rebuild`
