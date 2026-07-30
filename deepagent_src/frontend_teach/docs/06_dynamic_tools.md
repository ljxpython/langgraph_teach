# 06 Dynamic Tools

## 它是什么

动态工具选择不是让前端任意创建工具，而是由后端预先注册可信工具，再按本轮请求过滤模型可见的工具集合。它解决不同用户、页面或任务只应看到部分能力的问题，同时保留后端的鉴权边界。

## 最小链路

```text
用户勾选工具
  -> stream.submit(..., enabled_tools)
  -> enabled_tools 写入 graph state
  -> @wrap_model_call 读取 request.state
  -> request.override(tools=已过滤工具)
  -> 模型只能调用本轮可见工具
```

前端提交选择结果：

```ts
stream.submit({
  messages: [{ type: "human", content }],
  enabled_tools: enabledTools,
});
```

后端扩展 state，并在模型调用前过滤：

```python
class DynamicToolsState(DeepAgentState):
    enabled_tools: list[str]


@wrap_model_call
async def select_frontend_tools(request, handler):
    enabled_tools = set(request.state.get("enabled_tools", []))
    tools = [
        item
        for item in request.tools
        if item.name not in SELECTABLE_TOOL_NAMES or item.name in enabled_tools
    ]
    return await handler(request.override(tools=tools))
```

`create_deep_agent()` 仍然注册完整工具集合：

```python
dynamic_tools_agent = create_deep_agent(
    model=model,
    tools=[lookup_weather, calculate_total],
    middleware=[select_frontend_tools],
    state_schema=DynamicToolsState,
)
```

## 为什么只过滤业务工具

Deep Agents 自带 `task`、文件系统和 todo 等框架工具。直接按前端列表过滤全部 `request.tools` 会误删这些内部能力，因此本章只管理后端明确列入 `SELECTABLE_TOOL_NAMES` 的业务工具：

```python
SELECTABLE_TOOL_NAMES = {"lookup_weather", "calculate_total"}
```

前端传来的名称只能缩小这个白名单，不能扩大它。即使用户篡改请求并提交 `delete_database`，后端没有注册并授权该工具，模型也拿不到它。

## Tools、MCP、Skills 能否由前端选择

可以，但三者的“选择”含义不同：

| 能力 | 前端提交 | 后端动作 | 安全边界 |
| --- | --- | --- | --- |
| Tools | 工具 ID | 从已注册工具中筛选 | 服务端工具白名单和业务鉴权 |
| MCP | MCP server/tool ID | 连接受信 MCP server，加载后再筛选工具 | 服务端连接配置、凭据和工具白名单 |
| Skills | Skill ID | 映射到受信的 skill 目录或为本轮构建 Agent | 服务端路径映射，禁止接受任意文件路径 |

本章只实现 Tools，因为它是最小且可直接验证的公共机制。MCP 工具加载后仍是 LangChain tools，可以复用同一个过滤 middleware；Skills 是按需读取的 `SKILL.md` 指令和资源，不应伪装成普通函数工具。真正需要每轮切换 Skills 时，应由后端 graph factory 根据受信 ID 选择 `skills=[...]`，而不是让浏览器传本地路径。

## 当前版本差异

官方 Python 示例常从 `request.runtime.context` 读取每轮配置。但本项目当前的 `@langchain/react==1.0.29` 类型定义不支持在 `stream.submit()` 的 options 顶层传 `context`，所以本章把 `enabled_tools` 作为自定义 graph state 提交，并从 `request.state` 读取。升级 SDK 后可以评估改为 per-run context，但当前实现已经通过实际 TypeScript 构建。

## MCP 依赖修复

项目原锁文件中的 `mcp==1.21.2` 与 `langchain-mcp-adapters==0.3.0` 不兼容，导入时缺少 `streamable_http_client`。当前 `uv.lock` 已升级到 `mcp==1.28.1`，并通过以下导入检查：

```bash
uv run python -c "from langchain_mcp_adapters.client import MultiServerMCPClient"
```

`pyproject.toml` 已声明 `langchain-mcp-adapters>=0.1.13`，因此无需再增加一个重复的直接依赖；锁文件负责让当前项目安装到已验证版本。

## 运行与预期现象

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，进入 `06 Dynamic Tools`：

1. 只勾选 `Weather`，提交默认请求，预期只出现 `lookup_weather` 工具卡。
2. 同时勾选两个工具，提交默认请求，预期天气和总价工具都可被调用。
3. 取消全部工具，模型应说明对应能力本轮未启用，不能伪造工具结果。

## 常见误区

- 前端 checkbox 不是授权系统；真正的授权和白名单必须在后端执行。
- “动态选择”不等于每次请求都安装 Python 包或创建 MCP 进程；优先复用已加载能力并过滤暴露集合。
- 不要过滤 `request.tools` 中所有未勾选项，否则会误删 Deep Agents 内置工具。
- 不要只在 system prompt 中告诉模型“别用某工具”；工具仍在 schema 中时，模型依然可能调用。
- graph state 会随 thread 持久化，本章前端每次提交都显式发送完整 `enabled_tools`，避免沿用上轮选择。

## 官方资料

- Dynamic tool selection: `https://docs.langchain.com/oss/python/langchain/tools#dynamic-tool-selection`
- Dynamically selecting tools middleware: `https://docs.langchain.com/oss/python/langchain/middleware/custom#dynamically-selecting-tools`
- MCP: `https://docs.langchain.com/oss/python/langchain/mcp`
- Deep Agents Skills: `https://docs.langchain.com/oss/python/deepagents/skills`
