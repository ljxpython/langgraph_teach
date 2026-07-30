# 09 Custom Stream Channels

## 它是什么

Custom Stream Channel 是服务端向前端主动推送结构化领域事件的独立通道。它解决了进度、指标、来源等数据既不应伪装成聊天消息、也不值得写进长期 graph state 的问题。

本章复用第 08 章的确定性图。`ExecutionProgressTransformer` 观察每个 `values` 协议事件中新增的 `execution_steps`，然后推送独立 payload：

```python
class ExecutionProgressTransformer(StreamTransformer):
    def init(self) -> dict[str, StreamChannel]:
        return {"executionProgress": self.channel}

    def process(self, event: ProtocolEvent) -> bool:
        for step in new_steps:
            self.channel.push({
                "name": "execution-progress",
                "payload": {"kind": "node_complete", **step},
            })
        return True
```

图编译时注册 transformer：

```python
custom_stream_channels = builder.compile(
    transformers=[ExecutionProgressTransformer],
)
```

## 前端读取

`useExtension` 读取最新一条、已经解包的 payload，适合状态徽章或进度面板：

```tsx
const latest = useExtension<ExecutionProgressEvent>(stream, "execution-progress");
```

`useChannel` 读取有限长度的原始事件历史，适合审计日志或本章的节点卡列表：

```tsx
const rawEvents = useChannel(stream, ["custom:execution-progress"], undefined, {
  bufferSize: 10,
  replay: true,
});
const history = rawEvents.map((event) => {
  const data = event.params?.data;
  return data?.payload?.payload ?? data?.payload ?? data;
});
```

注意名称差异：`useExtension` 传裸名称 `execution-progress`；`useChannel` 传完整协议 channel id `custom:execution-progress`。

当前项目的 `@langchain/react==1.0.29` 会让 `useExtension` 识别 `{name, payload}` 包装。`StreamChannel` 在 `langgraph==1.2.9` 不会自动添加这层包装，因此本章明确推送它；`useChannel` 的历史解析同时兼容裸 payload 和包装 payload。

## 运行

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，进入 `09 Custom Channels` 并提交默认请求。预期右侧依次显示 `classify`、`analyze`、`synthesize` 三个事件，左侧 `Latest payload` 最终显示 `synthesize`。

## 常见误区

- 不要把进度事件拼接到 AIMessage 文本里；那会混淆会话内容与 UI 协议。
- 不要为一次性事件滥用 graph state；state 用于可恢复的业务结果，channel 用于流式投影。
- `useChannel` 返回的是原始协议事件；当前 Agent Server 会额外包装一次，所以 payload 位于 `event.params.data.payload.payload`、`event.params.data.payload` 或 `event.params.data`。只要最新值时优先用 `useExtension`。
- 本章使用 LangGraph v3 streaming protocol；当前版本会给出 beta 警告，这是官方 API 的实验性标记，不是运行失败。

## 下一章

第 10 章回到 LangChain Frontend：Markdown messages，处理模型回答中的 Markdown、代码块和安全渲染边界。

## 官方资料

- Custom stream channels: `https://docs.langchain.com/oss/python/langgraph/frontend/custom-stream-channels`
