# 04 Sandbox

## 它是什么

Sandbox 前端不是单纯聊天框，而是文件树、代码/变更视图和 Agent 对话组成的 IDE。`useStream` 负责运行 Agent，自定义 HTTP API 负责浏览文件；两条链路必须通过同一个 `thread_id` 解析到同一个 workspace。

## 本章架构

```text
React IDE
  ├─ useStream(threadId) -> sandbox_agent -> FilesystemBackend
  └─ GET /sandbox/{threadId}/* -> FastAPI -> 同一个 workspace
```

本章把每个 thread 映射到：

```text
frontend_teach/sandbox_workspaces/<thread-id>/
```

初始文件为 `/README.md` 和 `/src/app.py`。Agent 先读取 `app.py`，再调用 `edit_file` 修改它，并用 `write_file` 创建 `/CHANGELOG.md`。前端检测文件修改工具完成后立即刷新文件，而不是等整个 run 结束。

## 关键代码

Agent 和 API 共享同一个 workspace 解析函数：

```python
def sandbox_backend(_runtime):
    thread_id = get_config()["configurable"]["thread_id"]
    return FilesystemBackend(
        root_dir=workspace_path_for_thread(thread_id),
        virtual_mode=True,
    )
```

`workspace_path_for_thread` 只校验并计算路径，不在 LangGraph 事件循环里执行同步磁盘 I/O；初始文件由同步 FastAPI 路由首次读取 workspace 时播种。

前端持久化 thread ID：

```ts
const stream = useStream({
  apiUrl: "http://localhost:2024",
  assistantId: "sandbox_agent",
  threadId,
  onThreadId: updateThreadId,
});
```

文件浏览不经过聊天消息，而是直接调用：

```text
GET /sandbox/{threadId}/tree
GET /sandbox/{threadId}/file?filePath=/src/app.py
```

## 运行

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，选择 `04 Sandbox`，提交默认请求。预期现象：

1. 左侧显示 thread workspace 文件树。
2. 中间显示 `/src/app.py` 源码。
3. Agent 调用 `read_file`、`edit_file` 和 `write_file`。
4. 修改完成后文件树出现 `/CHANGELOG.md`，变更文件显示 `M`。
5. 点击变更文件默认进入 Before/After 对照视图。

## 安全边界

本章是本地教学实现，不是生产 sandbox。`FilesystemBackend(virtual_mode=True)` 会阻止 `..`、`~` 和逃离根目录的文件路径，但没有容器、进程、网络或资源隔离；因此示例不开放 `execute`。

生产环境应使用 LangSmith Sandbox、Docker、VM 或其他实现 `SandboxBackendProtocol` 的隔离环境，并把 sandbox ID 存到 thread metadata。不要把 API key、`.env` 或宿主机凭证上传进 sandbox。

## Diff 边界

教学 UI 使用原生 Before/After 双栏，不增加依赖。生产 React 应按官方建议使用 `@pierre/diffs` 渲染真正的 unified diff、行级增删统计和语法高亮。

## 常见误区

- `stream.values.files` 不等于外部 sandbox 文件系统；生产 sandbox 文件要通过 provider 文件 API或自定义 HTTP 路由读取。
- 不能让 Agent backend 和文件 API 各自维护一份内存映射，thread metadata 或统一解析函数才是单一事实来源。
- 不要只在 run 结束后刷新文件。监听 `write_file`、`edit_file`、`delete`、`execute` 的完成消息并立即刷新。
- 自定义 CORS 中间件会覆盖全部 LangGraph 路由；只允许 `GET` 会导致 `POST /threads` 的预检失败。

## 官方资料

- Deep Agents Frontend Sandbox: `https://docs.langchain.com/oss/python/deepagents/frontend/sandbox`
- Deep Agents Sandboxes: `https://docs.langchain.com/oss/python/deepagents/sandboxes`
- Going to production: `https://docs.langchain.com/oss/python/deepagents/going-to-production`
