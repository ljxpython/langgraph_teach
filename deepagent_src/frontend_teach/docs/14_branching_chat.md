# 14 Branching Chat

## 它是什么

Branching Chat 把对话当作 checkpoint 树，而不是只能向后追加的数组。编辑历史问题或重新生成回答时，前端从目标消息的父 checkpoint 启动新 run，旧路径仍保留在同一线程历史中。

## 读取消息的 fork 点

每条消息的分支信息不在消息正文里。`useMessageMetadata` 按消息 ID 返回它首次出现时对应的父 checkpoint：

```tsx
const metadata = useMessageMetadata(stream, message.id);
const checkpointId = metadata?.parentCheckpointId;
```

必须在渲染单条消息的子组件中调用这个 hook，不能在 `.map()` 回调里条件调用 React hook。

本章的确定性演示图执行极快，本地 Agent Server 偶尔会在前端内容订阅建立前完成运行。页面因此在运行结束后读取一次 `getHistory()`，按消息首次出现的 state 计算父 checkpoint；history 映射还可避免旧消息的实时 metadata 被后续快照覆盖。history 尚未返回时才回退到 `useMessageMetadata`。

## 编辑用户消息

```tsx
stream.submit(
  { messages: [{ type: "human", content: editedText }] },
  { forkFrom: checkpointId },
);
```

这不是修改旧 checkpoint。Agent Server 从父 checkpoint 复制执行上下文，再将编辑后的 HumanMessage 作为新输入执行，因此原问题与原回答仍在历史中。

## 重新生成 AI 回答

```tsx
stream.submit(undefined, { forkFrom: checkpointId });
```

AIMessage 的父 checkpoint 已包含触发它的用户问题，所以 regenerate 不应再次追加 HumanMessage。教学后端每次生成一个不同的六位 variant，便于肉眼确认出现了新分支，不调用真实模型。

## 当前版本签名

当前安装的 `@langchain/react@1.0.29` 类型为：

```ts
forkFrom?: string;
```

因此本项目使用 `{ forkFrom: checkpointId }`。官方页面当前部分代码仍写成 `{ forkFrom: { checkpointId } }`，与本地类型不一致；以项目锁定版本的编译结果为准。

## 运行与预期

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，进入 `14 Branching Chat`：

1. 提交默认问题，得到带 variant 的回答。
2. 点击 HumanMessage 下方“编辑并分叉”，修改问题后创建分支。
3. 新路径显示编辑后的问题和新回答，旧路径仍存在于服务器 history。
4. 点击 AIMessage 下方“重新生成”，同一问题得到不同 variant。

后端最小测试：

```bash
uv run python -m unittest deepagent_src.frontend_teach.tests.test_branching_chat
```

## 与 Time Travel 的区别

| 机制 | 目的 |
| --- | --- |
| Branching Chat | 为用户提供编辑问题、重新生成和多路径对话体验 |
| Time Travel | 面向调试或运维，从 checkpoint 检查状态并重新执行图 |

两者都依赖 checkpoint，但前端交互目标不同。第 18 章会单独处理 Time Travel，不能拿调试界面冒充聊天分支。

## 常见误区

- 不要用数组下标作为 fork 点；只能使用服务端提供的 checkpoint ID。
- 不要覆盖旧消息或删除旧 checkpoint，分支的价值就是保留其他路径。
- Regenerate 不要重复提交用户消息，否则上下文会出现两份相同问题。
- checkpoint history 可能很深，生产 UI 应按需加载，不要一次拉取整个线程。
- 分支仍属于原线程的权限边界，读取 history 时必须验证线程所有权。

## 下一章

第 15 章学习 Reasoning Tokens：把模型推理内容与最终回答分开展示。

## 官方资料

- Branching chat: `https://docs.langchain.com/oss/python/langchain/frontend/branching-chat`
