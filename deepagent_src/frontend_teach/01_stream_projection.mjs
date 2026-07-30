import assert from "node:assert/strict";

const stream = {
  messages: [
    {
      id: "m1",
      type: "human",
      text: "研究 Deep Agents 前端概述",
    },
    {
      id: "m2",
      type: "ai",
      text: "我会委派 researcher 收集资料。",
      tool_calls: [{ id: "call_researcher", name: "task" }],
    },
  ],
  subagents: new Map([
    [
      "call_researcher",
      {
        id: "call_researcher",
        name: "researcher",
        status: "running",
        task: "收集 frontend overview 资料",
      },
    ],
  ]),
  values: {
    todos: [
      { text: "理解 useStream", status: "done" },
      { text: "渲染 subagent 状态", status: "running" },
    ],
  },
};

function subagentsForMessage(message, subagents) {
  return (message.tool_calls ?? [])
    .map((toolCall) => subagents.get(toolCall.id))
    .filter(Boolean);
}

function projectDeepAgentStream(stream) {
  return {
    coordinatorMessages: stream.messages.map((message) => message.text),
    visibleSubagents: stream.messages.flatMap((message) =>
      subagentsForMessage(message, stream.subagents),
    ),
    todos: stream.values?.todos ?? [],
  };
}

const view = projectDeepAgentStream(stream);

console.log(JSON.stringify(view, null, 2));

assert.equal(view.coordinatorMessages.length, 2);
assert.equal(view.visibleSubagents[0].name, "researcher");
assert.equal(view.todos[1].status, "running");

