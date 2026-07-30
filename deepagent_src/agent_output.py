from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from langchain_core.messages import BaseMessage


def pretty_print_messages(messages: Sequence[BaseMessage]) -> None:
    for message in messages:
        message.pretty_print()


def invoke_and_pretty_print(
    graph: Any,
    inputs: dict[str, Any],
    config: dict[str, Any] | None = None,
    *,
    context: Any | None = None,
) -> dict[str, Any]:
    if context is None:
        state = graph.invoke(inputs, config)
    else:
        state = graph.invoke(inputs, config, context=context)
    pretty_print_messages(state["messages"])
    return state


def stream_values_and_pretty_print(
    graph: Any,
    inputs: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    final_state: dict[str, Any] = {}
    seen = 0

    for chunk in graph.stream(inputs, config, stream_mode="values"):
        messages = chunk.get("messages", [])
        for message in messages[seen:]:
            message.pretty_print()
        seen = len(messages)
        final_state = chunk

    return final_state


def stream_updates(
    graph: Any,
    inputs: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    final_chunk: dict[str, Any] = {}

    for chunk in graph.stream(inputs, config, stream_mode="updates"):
        print(chunk)
        final_chunk = chunk

    return final_chunk


def _message_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "".join(parts)
    return ""


def _tool_call_summary(message: BaseMessage) -> str:
    tool_calls = getattr(message, "tool_calls", None) or []
    tool_call_chunks = getattr(message, "tool_call_chunks", None) or []
    items = []
    for call in tool_calls:
        name = call.get("name", "tool")
        args = call.get("args", {})
        items.append(f"{name}({json.dumps(args, ensure_ascii=False, sort_keys=True)})")
    if not items:
        for chunk in tool_call_chunks:
            name = chunk.get("name", "tool")
            args = chunk.get("args", "")
            items.append(f"{name}({args})")
    return " | ".join(items)


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _message_debug_lines(message: BaseMessage) -> list[str]:
    lines = [f"class={type(message).__name__} type={message.type}"]

    for attr in ("id", "name", "tool_call_id"):
        value = getattr(message, attr, None)
        if value:
            lines.append(f"{attr}={value}")

    text = _message_text(message)
    if text:
        lines.append(f"content={text}")
    elif message.content:
        lines.append(f"content={_json_dump(message.content)}")

    for attr in (
        "tool_calls",
        "invalid_tool_calls",
        "tool_call_chunks",
        "usage_metadata",
        "response_metadata",
        "additional_kwargs",
    ):
        value = getattr(message, attr, None)
        if value:
            lines.append(f"{attr}={_json_dump(value)}")

    return lines


def _print_message_debug(message: BaseMessage, *, node: str | None = None) -> None:
    source = f" node={node}" if node else ""
    print(f"- message{source}")
    for line in _message_debug_lines(message):
        print(f"  {line}")


def _print_update_debug(node: str, payload: Any) -> None:
    print(f"\n--- update from {node} ---")
    if not isinstance(payload, dict):
        print(payload)
        return

    messages = payload.get("messages", [])
    for message in messages:
        _print_message_debug(message, node=node)

    rest = {key: value for key, value in payload.items() if key != "messages"}
    if rest:
        print(_json_dump(rest))


class _StreamMessagePrinter:
    def __init__(self) -> None:
        self._current_node: str | None = None
        self._printed_text = False

    def print_inputs(self, inputs: dict[str, Any]) -> None:
        messages = inputs.get("messages", [])
        if not messages:
            return
        print("\n--- input ---")
        pretty_print_messages(messages)

    def print_message(self, message: BaseMessage, metadata: dict[str, Any]) -> None:
        node = metadata.get("langgraph_node", "unknown")
        text = _message_text(message)
        tool_summary = _tool_call_summary(message)

        if text:
            if self._current_node != node:
                self.close()
                print(f"\n--- message from {node} ---")
                self._current_node = node
            print(text, end="", flush=True)
            if tool_summary:
                print()
                print(f"[tool calls] {tool_summary}")
            self._printed_text = True
            return

        if tool_summary:
            self.close()
            print(f"\n--- message from {node} ---")
            print(f"[tool calls] {tool_summary}")
            return

        if message.type.endswith("Chunk"):
            return

        self.close()
        print(f"\n--- message from {node} ---")
        message.pretty_print()

    def close(self) -> None:
        if self._printed_text:
            print()
            self._printed_text = False


def stream_messages(
    graph: Any,
    inputs: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> None:
    printer = _StreamMessagePrinter()
    printer.print_inputs(inputs)
    for message, metadata in graph.stream(inputs, config, stream_mode="messages"):
        printer.print_message(message, metadata)
    printer.close()


def stream_messages_and_updates(
    graph: Any,
    inputs: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> None:
    printer = _StreamMessagePrinter()
    printer.print_inputs(inputs)
    for mode, chunk in graph.stream(inputs, config, stream_mode=["updates", "messages"]):
        if mode == "updates":
            printer.close()
            for node, payload in chunk.items():
                messages = payload.get("messages", []) if isinstance(payload, dict) else []
                if node == "model":
                    continue
                if messages:
                    print(f"\n--- update:{node} ---")
                    pretty_print_messages(messages)
                    continue
                print(f"\n--- update:{node} ---\n{payload}")
            continue

        message, metadata = chunk
        printer.print_message(message, metadata)
    printer.close()


def stream_debug_trace(
    graph: Any,
    inputs: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> None:
    printer = _StreamMessagePrinter()
    input_messages = inputs.get("messages", [])
    if input_messages:
        print("\n--- input ---")
        for message in input_messages:
            _print_message_debug(message)

    for mode, chunk in graph.stream(inputs, config, stream_mode=["updates", "messages"]):
        if mode == "updates":
            printer.close()
            for node, payload in chunk.items():
                _print_update_debug(node, payload)
            continue

        message, metadata = chunk
        printer.print_message(message, metadata)
    printer.close()


def stream_events(
    graph: Any,
    inputs: dict[str, Any],
    config: dict[str, Any] | None = None,
    *,
    version: str = "v2",
) -> None:
    for event in graph.stream_events(inputs, config, version=version):
        print(event)
