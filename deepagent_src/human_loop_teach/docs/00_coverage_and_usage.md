# 00 覆盖清单与常用程度

## 覆盖表

| 知识点 | 覆盖方式 | 常用程度 | 说明 |
| --- | --- | --- | --- |
| `interrupt_on=True` | 01 章真实脚本 | 高 | 默认允许 approve/edit/reject/respond |
| `checkpointer` 必需 | 01-07 章真实脚本 | 高 | 没有 checkpoint 无法暂停后恢复 |
| 同一 `thread_id` 恢复 | 01-07 章真实脚本 | 高 | 首次 invoke 和 resume 必须同 config |
| `approve` | 01 章真实脚本 | 高 | 按原参数执行工具 |
| `reject` | 02/03/04/07 章真实脚本 | 高 | 跳过工具，给模型错误/拒绝反馈 |
| `edit` | 02/07 章真实脚本 | 中高 | 人类修改工具参数后执行 |
| `respond` | 02 章真实脚本 | 中低 | 用人类回复作为合成工具结果，适合 ask-user |
| `allowed_decisions` | 02 章真实脚本 | 高 | 按工具风险限制可选决策 |
| 条件中断 `when` | 03 章真实脚本 | 中 | 按参数只中断高风险调用 |
| 多工具批量审批 | 04 章真实脚本 | 中 | 一个 interrupt 里多个 action，决策顺序必须对应 |
| subagent interrupt | 05 章真实脚本 | 中 | 子 Agent 中断由父 Agent 调用结果接住 |
| 文件系统权限中断 | 06 章真实脚本 | 中 | `FilesystemPermission(mode="interrupt")` |
| tool 内直接 `interrupt()` | 文档说明 | 低到中 | 适合自定义工具内部复杂审批，本教程不单独跑 |
| PatchToolCallsMiddleware | 文档说明 | 中低 | 中断/取消时修复消息历史，通常无需手动操作 |

## 最常用主线

生产里最常见的是这条：

```text
敏感工具 -> interrupt_on 配置 allowed_decisions
-> checkpointer + thread_id
-> 首次 invoke 返回 interrupts
-> UI/CLI 展示 action_requests
-> 人类 approve/reject/edit
-> Command(resume={decisions: [...]})
```

优先掌握 01、02、03。04 是批量情况，05/06 是进阶边界，07 是综合。

## 哪些不常用

`respond` 不常用，除非工具本来就是问人类问题。别拿 `respond` 拒绝删除、发邮件这类副作用工具；应该用 `reject`。

tool 内直接 `interrupt()` 也不是入门主线。它适合工具内部自己判断风险、发起审批，或者你在 CompiledSubAgent 里有自定义审批工具。

## 安全边界

本教程的 `remove_file`、`delete_record`、`notify_email` 都只是返回字符串，不做真实删除、真实数据库修改、真实发邮件。文件系统章节用 Deep Agents 虚拟文件系统，不会写真实系统路径。

