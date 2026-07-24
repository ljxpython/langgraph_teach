from __future__ import annotations

from pathlib import Path


def main() -> None:
    skill_dir = Path(__file__).resolve().parents[1]
    paths = [
        skill_dir / "references" / "resource-map.md",
        skill_dir / "assets" / "report-template.md",
    ]
    for path in paths:
        print(path.relative_to(skill_dir))


if __name__ == "__main__":
    main()
