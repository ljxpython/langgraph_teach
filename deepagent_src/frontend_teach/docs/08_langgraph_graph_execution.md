# 08 LangGraph Graph Execution

## 它是什么

原生 `StateGraph` 由命名节点和边组成，每个节点负责写入特定 state key。顶层图应把要展示的执行步骤明确写入 state；嵌套编译图才通过 `stream.subgraphs` 发现，因此前端可以显示真实执行路径，而不是只等一条最终聊天回复。

## 最小图

本章图固定执行三个节点：

```text
START -> classify -> analyze -> synthesize -> END
```

每个节点同时写入业务 state 和一条 `AIMessage`：

```python
class GraphExecutionState(MessagesState):
    classification: str
    analysis: str
    synthesis: str
    execution_steps: Annotated[list[dict[str, str]], operator.add]


async def analyze_node(state: GraphExecutionState) -> dict:
    analysis = f"分析分类 {state['classification']} 的执行状态与节点输出"
    return {
        "analysis": analysis,
        "execution_steps": [{"name": "analyze", "output": analysis}],
    }
```

这个图是确定性的，不调用模型。目的是隔离并观察 LangGraph 的节点、边、state 合并和流事件。

## 前端读取两类数据

顶层图的执行卡从 state 中的步骤账本读取：

```tsx
const steps = stream.values?.execution_steps ?? [];
```

最终稳定输出从整个 graph state 读取：

```tsx
const synthesis = stream.values?.synthesis;
```

| 数据 | 用途 |
| --- | --- |
| `stream.subgraphs` | 发现嵌套 compiled subgraph 的命名空间与状态 |
| `useMessages(stream, node)` | 读取某一嵌套 subgraph 的 scoped message |
| `stream.values.execution_steps` | 顶层图显式写入的节点执行账本 |
| `stream.values` | graph state 中约定好的业务输出 |

不要用 state key 名去猜消息属于哪个节点。顶层图需要明确的步骤 state；条件分支和嵌套图则使用 scoped message 保持可靠归属。

## 运行

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，进入 `08 Graph Execution`，提交默认请求。预期依次看到 `classify`、`analyze`、`synthesize` 写入步骤账本，且 Graph state 显示三个对应字段。

## 常见误区

- 不要把顶层普通 node 当作 `stream.subgraphs`；该 map 代表嵌套 compiled subgraph。
- 不要把 `stream.messages` 的全局顺序当成节点归属。
- node name 与 state key 可以不同，UI 不应假设它们同名。
- 节点错误应显示在对应卡片，不能只显示一个笼统的聊天错误。

## 下一章

第 09 章学习 Custom Stream Channels：当 state 和 message 都不足以表达进度、表格行或领域事件时，节点如何主动推送自定义数据给前端。

## 官方资料

- LangGraph Frontend Overview: `https://docs.langchain.com/oss/python/langgraph/frontend/overview`
- Graph execution: `https://docs.langchain.com/oss/python/langgraph/frontend/graph-execution`
