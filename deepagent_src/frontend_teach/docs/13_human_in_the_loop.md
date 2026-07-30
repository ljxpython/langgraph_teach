# 13 Human-in-the-loop

## 它是什么

第 05 章使用 middleware 生成通用 approve/edit/reject 卡片。本章处理另一类需求：工具自己通过 `interrupt()` 描述业务表单，前端按 `form_type` 渲染字段，并把用户决定恢复给同一个工具调用。

## 自定义 interrupt 表单

后端 payload 是前后端约定的 JSON，不受通用 `HITLRequest` 结构限制：

```python
decision = interrupt({
    "form_type": "refund_approval",
    "title": "审核退款申请",
    "context": {
        "order_id": order_id,
        "amount": amount,
        "reason": reason,
    },
    "fields": [
        {"name": "amount", "label": "退款金额", "type": "currency"},
        {"name": "note", "label": "审核备注", "type": "textarea"},
    ],
})
```

`interrupt()` 的返回值就是前端恢复时提交的 decision。工具必须验证这个值，不能因为它来自自家前端就默认可信。

## 前端按类型渲染

```tsx
const card = stream.interrupt?.value as RefundReviewCard | undefined;

return card?.form_type === "refund_approval"
  ? <RefundReviewForm card={card} onResolve={resolveReview} />
  : null;
```

每种业务表单使用稳定的 `form_type`。不要让前端根据标题或工具描述猜组件类型，那种字符串匹配迟早把页面搞崩。

## 原子恢复并保留已决卡片

普通 `respond(decision)` 会清除 interrupt，待审表单随即消失。可以在恢复的同一条命令中追加一条带卡片元数据的消息：

```tsx
const resolvedCard = { ...card, resolved: true, decision };
const cardMessage = new AIMessage({
  content: decision.approved ? "退款审核已批准。" : "退款审核已拒绝。",
  response_metadata: { review_card: resolvedCard },
});

await stream.respond(decision, {
  interruptId: stream.interrupt.id,
  update: { messages: [cardMessage] },
});
```

这对应一个 `Command(resume=decision, update={...})`：恢复值与 state 更新进入同一个 checkpoint。前端先乐观显示卡片，服务端回显同 ID 消息后再完成对账，因此不会先消失再闪回来。

### 当前本地版本的兼容处理

浏览器实测表明，`@langchain/react@1.0.29` 会正确发送上述 `input.respond.update`，但当前最新 Python `langgraph-api@0.9.1` 接收后没有把 update 写入 checkpoint。页面当时能看到乐观卡片，刷新后却会消失。

本项目因此让前端只恢复 decision，后端在恢复后的最终消息中回写已决卡片：

```python
AIMessage(
    content=f"退款审核流程完成：{result}",
    response_metadata={"review_card": resolved_card},
)
```

页面提交 decision 时先用本地 `recentCard` 乐观显示；若恢复失败就立即撤销。后端最终消息负责 checkpoint 持久化，刷新或其他客户端通过 hydration 读取同一张卡片。服务端支持 `input.respond.update` 后，应删除这两段兼容逻辑，改回上面的单命令原子写法。

## 运行与预期

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，进入 `13 Human-in-the-loop`：

1. 提交退款原因后，右侧出现订单、金额和审核备注表单。
2. 金额不是正数时，前端阻止批准。
3. Approve 会把调整后的金额交回工具；Decline 不执行批准分支。
4. interrupt 清空，Agent 输出最终结果。
5. 已决卡片保留在消息历史中，并标记 `approved` 或 `declined`。

后端验证：

```bash
uv run python -m unittest deepagent_src.frontend_teach.tests.test_custom_hitl
```

## 与第 05 章的边界

| 方案 | 适用场景 | Payload |
| --- | --- | --- |
| middleware 通用审批 | 多个工具统一 approve/edit/reject | `action_requests + review_configs` |
| 工具内自定义 interrupt | 退款、订票、内容审核等专用表单 | 业务自定义 JSON |

## 常见误区

- 不要在 interrupt 前执行退款、发信等副作用；恢复后才允许进入真实操作。
- 不要只在组件本地保存已决卡片；刷新页面后会丢失审计记录。
- `respond` 表示给工具一个恢复值，不等于 middleware 的 `reject` decision。
- 必须校验金额、枚举和文本长度；前端校验只改善体验，后端校验才是安全边界。
- 长时间等待审批的线程需要持久 checkpointer、超时策略和审计日志。

## 下一章

第 14 章学习 Branching Chat：从历史 checkpoint 分叉对话，而不是覆盖原线程。

## 官方资料

- Human-in-the-loop: `https://docs.langchain.com/oss/python/langchain/frontend/human-in-the-loop`
