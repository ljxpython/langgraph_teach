from __future__ import annotations

import base64
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from deepagents.middleware import FilesystemMiddleware
from langchain.messages import HumanMessage

from deepagent_src.llms import get_gpt_model

SOURCE_IMAGE = (
    Path(__file__).resolve().parents[2]
    / "anything_chat_rag/parser_output/旅行日记2/docling/images/image_0.png"
)


def copy_airport_image(path: Path) -> None:
    assert SOURCE_IMAGE.is_file(), SOURCE_IMAGE
    path.write_bytes(SOURCE_IMAGE.read_bytes())


def tool_call_names(messages: list[Any]) -> list[str]:
    names: list[str] = []
    for message in messages:
        for call in getattr(message, "tool_calls", None) or []:
            names.append(call.get("name", ""))
    return names


def matches_airport_scene(text: str) -> bool:
    normalized = text.lower()
    return (
        "airasia" in normalized
        and "red" in normalized
        and any(word in normalized for word in ("board", "queue", "line"))
    )


def direct_image_answer() -> str:
    image_b64 = base64.b64encode(SOURCE_IMAGE.read_bytes()).decode()
    response = get_gpt_model().invoke(
        [
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": (
                            "Inspect this image in one English sentence: name the airline "
                            "printed on the aircraft, state the aircraft's dominant color, "
                            "and describe what the people are doing."
                        ),
                    },
                    {"type": "image", "base64": image_b64, "mime_type": "image/png"},
                ]
            )
        ]
    )
    return response.text


def tool_image_block_types(messages: list[Any]) -> list[str]:
    return [
        block.get("type", "")
        for message in messages
        if getattr(message, "type", "") == "tool" and getattr(message, "name", "") == "read_file"
        for block in message.content_blocks
    ]


def main() -> None:
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

    direct_text = direct_image_answer()
    assert matches_airport_scene(direct_text), direct_text
    print("direct_image:", direct_text)

    with TemporaryDirectory(prefix="deepagents-multimodal-") as tmp:
        image_path = Path(tmp, "airport.png")
        copy_airport_image(image_path)
        backend = LocalShellBackend(root_dir=tmp, virtual_mode=True)
        agent = create_deep_agent(
            model=get_gpt_model(disable_tool_streaming=True),
            backend=backend,
            subagents=[],
            middleware=[FilesystemMiddleware(backend=backend, tools=["read_file"])],
            system_prompt=(
                "You are a multimodal teaching assistant. "
                "You must call read_file on /airport.png before answering. "
                "Inspect the image and answer in one English sentence: name the airline "
                "printed on the aircraft, state the aircraft's dominant color, and "
                "describe what the people are doing."
            ),
        )

        state = agent.invoke(
            {
                "messages": [
                    HumanMessage(content="Inspect the scene in /airport.png.")
                ]
            }
        )
        final_text = state["messages"][-1].text
        calls = tool_call_names(state["messages"])
        image_blocks = tool_image_block_types(state["messages"])

        print("tool_calls:", ", ".join(calls))
        print("read_file_blocks:", ", ".join(image_blocks))
        print("final:", final_text)

        assert "read_file" in calls, calls
        assert "image" in image_blocks, image_blocks
        print("tool_result_vision_supported:", matches_airport_scene(final_text))
        print("multimodal capability probe complete")


if __name__ == "__main__":
    main()
