# 20 Generative UI

## 它是什么

Generative UI 让 Agent 输出一个描述组件树的 JSON spec，前端再从开发者定义的组件白名单中组合真实界面。模型不生成任意 JSX 或 HTML；catalog 决定它能用哪些组件及每个组件允许哪些 props。

本章使用官方 `json-render`：

```text
用户描述 -> Agent tool call -> JSON spec -> catalog/registry -> React UI
```

## 与 Structured Output 的区别

第 16 章的结构化输出对应一个固定的 `LearningPlanView`。Generative UI 的输出则包含 `root` 和 `elements`，Agent 可以在白名单范围内选择组件、层级与排列方式。

| 方案 | 前端渲染方式 | 灵活度 | 安全边界 |
| --- | --- | --- | --- |
| Structured Output | 固定领域组件 | 中 | 领域 schema |
| Generative UI | catalog 中组合组件树 | 高 | catalog + props schema |

## 定义 catalog

catalog 是组件协议，不是组件实现。本章只开放 `Card`、`Stack`、`Metric` 和 `List`：

```tsx
const catalog = defineCatalog(schema, {
  components: {
    Metric: {
      description: "展示一个指标名称和值",
      props: z.object({ label: z.string(), value: z.string() }),
    },
  },
  actions: {},
});
```

catalog 越小，模型越容易生成稳定结果。不要把整个设计系统一次性全塞进去。

## 定义 registry

registry 把 catalog 名称映射为真实 React 组件：

```tsx
const { registry } = defineRegistry(catalog, {
  components: {
    Metric: ({ props }) => (
      <article>
        <span>{props.label}</span>
        <strong>{props.value}</strong>
      </article>
    ),
  },
});
```

服务端只能选择 `Metric`，不能发送脚本、事件处理器或任意组件实现。

## Spec 格式

后端通过展示型 `render_ui` tool call 返回扁平组件树：

```json
{
  "root": "dashboard",
  "elements": {
    "dashboard": {
      "type": "Card",
      "props": { "title": "Agent 运行概览" },
      "children": ["runs"]
    },
    "runs": {
      "type": "Metric",
      "props": { "label": "今日运行", "value": "24" },
      "children": []
    }
  }
}
```

`root` 指向根元素；`children` 保存子元素 ID。扁平结构便于流式追加和局部更新。

## 安全渲染

流式 tool arguments 可能暂时缺少 `type` 或 `props`。渲染前只保留完整元素，并确认根元素存在：

```tsx
const elements = Object.fromEntries(
  Object.entries(raw.elements).filter(
    ([, element]) => element?.type && element?.props != null,
  ),
);

<JSONUIProvider registry={registry}>
  <Renderer spec={{ root: raw.root, elements }} registry={registry} loading={stream.isLoading} />
</JSONUIProvider>
```

`JSONUIProvider` 提供 state、visibility、validation 和 actions 上下文；即使本章没有 actions，也保持官方完整运行环境。

## 运行与预期

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，进入 `20 Generative UI`：

1. 输入界面描述并点击“生成”。
2. 后端返回 `render_ui` tool call。
3. 右侧使用真实 `json-render` Renderer 展示卡片、两个指标和步骤列表。
4. 用户输入会成为界面说明，证明 UI spec 来自本轮请求。

最小后端测试：

```bash
uv run python -m unittest deepagent_src.frontend_teach.tests.test_generative_ui
```

## 常见误区

- Generative UI 不是让模型返回任意 HTML、JSX 或 JavaScript。
- catalog 是安全边界，网络数据仍需运行时校验。
- 展示型 `render_ui` tool call 不应连接 `ToolNode`。
- 流式 spec 可能不完整，不能看到 `root` 就立即渲染所有元素。
- actions 会触发真实副作用；加入 actions 时必须白名单、校验参数并处理确认。
- 不要开放几十个用途重叠的组件，小而明确的 catalog 更稳定。

## 下一章

第 21 章学习 Frontend Integrations Overview：梳理预构建聊天 UI、组件库和当前自定义前端之间的选择边界。

## 官方资料

- Generative UI: `https://docs.langchain.com/oss/python/langchain/frontend/generative-ui`
- json-render: `https://json-render.dev`
