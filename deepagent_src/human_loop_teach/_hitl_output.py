from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from deepagent_src.agent_output import pretty_print_messages


def print_graph_output(result: Any) -> None:
    value = getattr(result, "value", result)
    messages = value.get("messages", []) if isinstance(value, dict) else []
    if messages:
        pretty_print_messages(messages)
    print_interrupts(result)


def print_interrupts(result: Any) -> None:
    interrupts = getattr(result, "interrupts", ())
    if not interrupts:
        return
    print("\n--- interrupts ---")
    for interrupt in interrupts:
        value = interrupt.value
        for action in value.get("action_requests", []):
            print(f"tool={action['name']} args={action['args']}")
        for config in value.get("review_configs", []):
            print(
                f"review={config['action_name']} decisions={config['allowed_decisions']}"
            )


def require_interrupt(result: Any) -> dict[str, Any]:
    interrupts = getattr(result, "interrupts", ())
    assert interrupts, "expected a human-in-the-loop interrupt"
    return interrupts[0].value


def tool_messages(result: Any, *, name: str | None = None) -> list[str]:
    value = getattr(result, "value", result)
    messages = value.get("messages", []) if isinstance(value, dict) else []
    outputs = []
    for message in messages:
        if message.__class__.__name__ != "ToolMessage":
            continue
        if name is not None and getattr(message, "name", None) != name:
            continue
        outputs.append(str(message.content))
    return outputs
