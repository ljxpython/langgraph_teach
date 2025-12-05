# LangGraph API 中断处理分析

## 问题描述

当使用 LangGraph API 运行带有 `interrupt_on` 配置的 agent 时，界面显示工具调用信息后，用户输入 "approve" 等文本会导致工具调用被取消，提示：

```
Tool call write_file with id call_00_41rPTD5hzRerNhGq2OiNILq7 was cancelled - another message came in before it could be completed.
```

## 根本原因

### 1. 中断机制的工作原理

根据代码分析，LangGraph 的 Human-in-the-Loop (HITL) 中断机制工作流程如下：

1. **中断发生**：当 agent 调用被标记为需要中断的工具时，会生成一个 `Interrupt` 对象
2. **中断数据结构**：
   ```python
   # 中断对象包含
   interrupt_obj.id  # 中断ID
   interrupt_obj.value  # HITLRequest 对象
   
   # HITLRequest 结构
   {
       "action_requests": [
           {
               "name": "write_file",
               "args": {...},
               "description": "写入文件"
           }
       ]
   }
   ```

3. **恢复执行**：需要使用 `Command(resume=...)` 来恢复，而不是发送普通消息

### 2. 正确的恢复方式

从 `deepagents_v2/deepagents-cli/deepagents_cli/execution.py` 可以看到正确的处理方式：

```python
# 收集中断信息
pending_interrupts: dict[str, HITLRequest] = {}

# 构建响应
hitl_response: dict[str, HITLResponse] = {}
for interrupt_id, hitl_request in pending_interrupts.items():
    decisions = []
    for action_request in hitl_request["action_requests"]:
        # 批准
        decisions.append({"type": "approve"})
        # 或拒绝
        # decisions.append({"type": "reject", "message": "拒绝原因"})
        # 或编辑
        # decisions.append({"type": "edit", "args": {...}})
    
    hitl_response[interrupt_id] = {"decisions": decisions}

# 使用 Command 恢复
stream_input = Command(resume=hitl_response)
agent.astream(stream_input, config=config)
```

## LangGraph API 的正确使用方式

### 方式 1: 使用 SDK (Python)

```python
from langgraph_sdk import get_client

client = get_client(url=DEPLOYMENT_URL)
thread_id = "your-thread-id"
assistant_id = "agent"

# 1. 首次运行，触发中断
result = await client.runs.wait(
    thread_id,
    assistant_id,
    input={"messages": [{"role": "user", "content": "写入文件"}]}
)

# 2. 获取状态，查看中断信息
state = await client.threads.get_state(thread_id)
# state 中包含 interrupts 信息

# 3. 构建 resume 响应
# 注意：需要根据实际的 interrupt 结构构建
resume_value = {
    "<interrupt_id>": {
        "decisions": [
            {"type": "approve"}  # 或 "reject" 或 "edit"
        ]
    }
}

# 4. 使用 Command 恢复
await client.runs.wait(
    thread_id,
    assistant_id,
    input=None,  # 注意：input 为 None
    command={"resume": resume_value}
)
```

### 方式 2: 使用 HTTP API

```bash
# 1. 创建 thread
curl -X POST \
  <DEPLOYMENT_URL>/threads \
  -H 'Content-Type: application/json' \
  -d '{}'

# 2. 运行直到中断
curl -X POST \
  <DEPLOYMENT_URL>/threads/<THREAD_ID>/runs/wait \
  -H 'Content-Type: application/json' \
  -d '{
    "assistant_id": "agent",
    "input": {"messages": [{"role": "user", "content": "写入文件"}]}
  }'

# 3. 获取状态查看中断
curl -X GET \
  <DEPLOYMENT_URL>/threads/<THREAD_ID>/state

# 4. 恢复执行
curl -X POST \
  <DEPLOYMENT_URL>/threads/<THREAD_ID>/runs/wait \
  -H 'Content-Type: application/json' \
  -d '{
    "assistant_id": "agent",
    "command": {
      "resume": {
        "<interrupt_id>": {
          "decisions": [{"type": "approve"}]
        }
      }
    }
  }'
```

## 为什么直接输入 "approve" 不起作用？

1. **消息 vs Command**：
   - 输入 "approve" 会被当作新的用户消息添加到对话中
   - 这会触发新的 agent 运行，而不是恢复之前的中断
   - 之前的工具调用会被取消

2. **正确的做法**：
   - 不应该发送新消息
   - 应该使用 `Command(resume=...)` 结构
   - 需要提供正确的中断ID和决策结构

## 界面实现建议

如果要在 Web 界面实现 approve/edit/reject 功能，需要：

1. **检测中断状态**：
   ```javascript
   // 监听 stream 中的 updates
   for await (const chunk of stream) {
       if (chunk.event === 'updates' && chunk.data.__interrupt__) {
           // 显示批准/拒绝按钮
           const interrupts = chunk.data.__interrupt__;
           // 保存 interrupt_id 和 action_requests
       }
   }
   ```

2. **构建恢复请求**：
   ```javascript
   // 用户点击 approve 按钮时
   const resumePayload = {
       [interruptId]: {
           decisions: [{ type: 'approve' }]
       }
   };
   
   // 发送恢复请求
   await client.runs.create(threadId, assistantId, {
       command: { resume: resumePayload }
   });
   ```

3. **不要发送普通消息**：
   - 批准/拒绝操作不应该通过发送消息实现
   - 必须使用 Command 结构

## 完整的 Web 界面实现示例

### 前端代码示例 (JavaScript/TypeScript)

```javascript
// 1. 启动 agent 运行并监听中断
async function runAgentWithInterrupt(threadId, assistantId, userMessage) {
    const client = new Client({ apiUrl: DEPLOYMENT_URL });

    // 存储中断信息
    let pendingInterrupts = {};

    // 使用 stream 模式监听
    const stream = client.runs.stream(
        threadId,
        assistantId,
        {
            input: { messages: [{ role: "user", content: userMessage }] },
            streamMode: ["messages", "updates"]
        }
    );

    for await (const chunk of stream) {
        // 监听 updates 流中的中断
        if (chunk.event === "updates" && chunk.data.__interrupt__) {
            const interrupts = chunk.data.__interrupt__;

            // 保存所有中断信息
            for (const interrupt of interrupts) {
                pendingInterrupts[interrupt.id] = interrupt.value;

                // 显示中断信息给用户
                displayInterruptUI(interrupt);
            }
        }

        // 处理消息流
        if (chunk.event === "messages") {
            displayMessage(chunk.data);
        }
    }

    return pendingInterrupts;
}

// 2. 显示批准/拒绝/编辑界面
function displayInterruptUI(interrupt) {
    const actionRequests = interrupt.value.action_requests;

    for (const actionRequest of actionRequests) {
        const { name, args, description } = actionRequest;

        // 显示工具调用信息
        console.log(`工具: ${name}`);
        console.log(`描述: ${description}`);
        console.log(`参数:`, args);

        // 创建按钮
        createApprovalButtons(interrupt.id, actionRequest);
    }
}

// 3. 处理用户决策
async function handleUserDecision(interruptId, decision, editedArgs = null) {
    const client = new Client({ apiUrl: DEPLOYMENT_URL });

    // 构建决策对象
    let decisionObj;
    if (decision === 'approve') {
        decisionObj = { type: 'approve' };
    } else if (decision === 'reject') {
        decisionObj = { type: 'reject', message: '用户拒绝了此操作' };
    } else if (decision === 'edit' && editedArgs) {
        decisionObj = { type: 'edit', args: editedArgs };
    }

    // 构建 resume 响应
    const resumePayload = {
        [interruptId]: {
            decisions: [decisionObj]
        }
    };

    // 使用 Command 恢复执行
    const stream = client.runs.stream(
        threadId,
        assistantId,
        {
            command: { resume: resumePayload },
            streamMode: ["messages", "updates"]
        }
    );

    // 继续处理流
    for await (const chunk of stream) {
        if (chunk.event === "messages") {
            displayMessage(chunk.data);
        }
    }
}

// 4. 按钮点击处理
function createApprovalButtons(interruptId, actionRequest) {
    // Approve 按钮
    const approveBtn = document.createElement('button');
    approveBtn.textContent = 'Approve';
    approveBtn.onclick = () => handleUserDecision(interruptId, 'approve');

    // Reject 按钮
    const rejectBtn = document.createElement('button');
    rejectBtn.textContent = 'Reject';
    rejectBtn.onclick = () => handleUserDecision(interruptId, 'reject');

    // Edit 按钮
    const editBtn = document.createElement('button');
    editBtn.textContent = 'Edit';
    editBtn.onclick = () => {
        // 显示编辑界面
        const editedArgs = showEditDialog(actionRequest.args);
        handleUserDecision(interruptId, 'edit', editedArgs);
    };

    // 添加到界面
    document.body.appendChild(approveBtn);
    document.body.appendChild(rejectBtn);
    document.body.appendChild(editBtn);
}
```

### Python SDK 完整示例

```python
import asyncio
from langgraph_sdk import get_client

async def run_with_interrupt_handling():
    client = get_client(url="http://localhost:8123")

    # 创建 thread
    thread = await client.threads.create()
    thread_id = thread["thread_id"]
    assistant_id = "agent"

    # 1. 首次运行，触发中断
    print("发送用户消息...")
    pending_interrupts = {}

    async for chunk in client.runs.stream(
        thread_id,
        assistant_id,
        input={"messages": [{"role": "user", "content": "写入文件 test.txt"}]},
        stream_mode=["messages", "updates"]
    ):
        # 检查中断
        if chunk.event == "updates" and "__interrupt__" in chunk.data:
            interrupts = chunk.data["__interrupt__"]
            for interrupt in interrupts:
                interrupt_id = interrupt["id"]
                interrupt_value = interrupt["value"]
                pending_interrupts[interrupt_id] = interrupt_value

                # 显示中断信息
                print(f"\n⚠️  中断发生 (ID: {interrupt_id})")
                for action_req in interrupt_value["action_requests"]:
                    print(f"  工具: {action_req['name']}")
                    print(f"  描述: {action_req.get('description', 'N/A')}")
                    print(f"  参数: {action_req['args']}")

        # 显示消息
        if chunk.event == "messages":
            print(f"消息: {chunk.data}")

    # 2. 处理中断 - 用户决策
    if pending_interrupts:
        print("\n请选择操作:")
        print("1. Approve (批准)")
        print("2. Reject (拒绝)")
        print("3. Edit (编辑)")

        choice = input("输入选择 (1/2/3): ").strip()

        # 构建 resume 响应
        resume_payload = {}
        for interrupt_id, interrupt_value in pending_interrupts.items():
            decisions = []

            if choice == "1":
                # 批准所有操作
                for _ in interrupt_value["action_requests"]:
                    decisions.append({"type": "approve"})
            elif choice == "2":
                # 拒绝所有操作
                for _ in interrupt_value["action_requests"]:
                    decisions.append({
                        "type": "reject",
                        "message": "用户拒绝了此操作"
                    })
            elif choice == "3":
                # 编辑操作
                for action_req in interrupt_value["action_requests"]:
                    print(f"\n编辑参数 (当前: {action_req['args']})")
                    # 这里可以让用户输入新参数
                    new_args = action_req['args']  # 简化示例
                    decisions.append({
                        "type": "edit",
                        "args": new_args
                    })

            resume_payload[interrupt_id] = {"decisions": decisions}

        # 3. 使用 Command 恢复执行
        print("\n恢复执行...")
        async for chunk in client.runs.stream(
            thread_id,
            assistant_id,
            command={"resume": resume_payload},
            stream_mode=["messages", "updates"]
        ):
            if chunk.event == "messages":
                print(f"消息: {chunk.data}")

# 运行
asyncio.run(run_with_interrupt_handling())
```

## 关键要点总结

1. **不要发送普通消息**：输入 "approve" 作为消息会被当作新的用户输入，导致之前的工具调用被取消

2. **使用 Command 结构**：必须使用 `command: { resume: {...} }` 来恢复中断

3. **正确的数据结构**：
   ```python
   {
       "<interrupt_id>": {
           "decisions": [
               {"type": "approve"},  # 或
               {"type": "reject", "message": "原因"},  # 或
               {"type": "edit", "args": {...}}
           ]
       }
   }
   ```

4. **从 stream 获取中断信息**：监听 `stream_mode=["updates"]`，检查 `__interrupt__` 字段

5. **保存 interrupt_id**：每个中断都有唯一的 ID，恢复时必须使用正确的 ID

## 参考资料

- [LangGraph Human-in-the-Loop 文档](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
- [LangGraph Server API 文档](https://docs.langchain.com/langsmith/add-human-in-the-loop)
- DeepAgents CLI 实现：`deepagents_v2/deepagents-cli/deepagents_cli/execution.py`
- LangGraph API Schema: `langgraph_api_danwen/schema.py`

