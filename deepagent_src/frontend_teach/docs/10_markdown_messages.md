# 10 Markdown Messages

## 它是什么

模型天然会输出标题、列表、表格和代码块。Markdown renderer 把 `useStream` 累积到 AI message 的文本转换成 React 元素，让结构可读，同时不把模型文本直接注入 HTML。

## 最小实现

React 官方示例推荐 `react-markdown + remark-gfm`：

```tsx
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function Markdown({ children }: { children: string }) {
  return <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>;
}
```

本教程只让 AI 消息进入 Markdown renderer，用户消息仍按纯文本渲染：

```tsx
const isAI = type === "ai" || type === "AIMessage";
return isAI ? <Markdown>{message.text}</Markdown> : <div>{message.text}</div>;
```

`remark-gfm` 增加表格、删除线、任务列表和自动链接。`react-markdown` 生成 React element tree，不使用 `dangerouslySetInnerHTML`；本章也不启用 `rehype-raw`，因此模型返回的 `<script>` 不会执行。

## 流式行为

`useStream` 在 token 到达时持续更新 `msg.text`，React 会重新调用 Markdown renderer。普通聊天消息直接全量重解析即可，只有超过约 50 KB 且出现卡顿时才考虑按帧节流。

## 运行

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，进入 `10 Markdown Messages` 并发送默认请求。预期看到标题、GFM 列表、表格、代码块和引用；页面不存在 `script` 元素，`window.markdownXss` 也未被设置。

## 常见误区

- 不要用正则手写 Markdown parser。
- 不要把模型输出直接交给 `dangerouslySetInnerHTML`。
- React 使用 `react-markdown` 时不需要 DOMPurify；如果启用 raw HTML 插件，安全模型就变了，必须重新设计白名单与净化。
- 表格和代码块必须允许自身横向滚动，不能撑破聊天布局。

## 下一章

第 11 章学习 Tool Calling：把模型的工具请求和工具结果渲染成可追踪的调用卡片。

## 官方资料

- Markdown messages: `https://docs.langchain.com/oss/python/langchain/frontend/markdown-messages`
