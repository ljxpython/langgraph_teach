from __future__ import annotations


def consolidate_memory(existing: str, observations: list[str]) -> str:
    lines = [line.rstrip() for line in existing.splitlines()]
    existing_items = {line.removeprefix("- ").strip() for line in lines if line.startswith("- ")}

    for observation in observations:
        if observation not in existing_items:
            lines.append(f"- {observation}")
            existing_items.add(observation)

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    existing = "# User Memory\n\n## Preferences\n\n- Prefers Python examples\n"
    updated = consolidate_memory(
        existing,
        [
            "Prefers Python examples",
            "Likes short runnable scripts",
        ],
    )

    assert updated.count("Prefers Python examples") == 1
    assert "- Likes short runnable scripts" in updated
    print("background consolidation ok")


if __name__ == "__main__":
    main()
