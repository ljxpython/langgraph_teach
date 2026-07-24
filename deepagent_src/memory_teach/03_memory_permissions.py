from __future__ import annotations

from deepagents import FilesystemPermission
from deepagents.middleware.filesystem import _check_fs_permission


POLICY_READ_ONLY = [
    FilesystemPermission(
        operations=["write"],
        paths=["/policies/**"],
        mode="deny",
    )
]

PERSONAL_MEMORY_REVIEW = [
    FilesystemPermission(
        operations=["write"],
        paths=["/memories/personal/**"],
        mode="interrupt",
    ),
    FilesystemPermission(
        operations=["write"],
        paths=["/memories/**"],
        mode="allow",
    ),
]


def main() -> None:
    assert _check_fs_permission(POLICY_READ_ONLY, "read", "/policies/AGENTS.md") == "allow"
    assert _check_fs_permission(POLICY_READ_ONLY, "write", "/policies/AGENTS.md") == "deny"
    assert (
        _check_fs_permission(
            PERSONAL_MEMORY_REVIEW,
            "write",
            "/memories/personal/AGENTS.md",
        )
        == "interrupt"
    )
    assert _check_fs_permission(PERSONAL_MEMORY_REVIEW, "write", "/memories/AGENTS.md") == "allow"
    print("memory permissions ok")


if __name__ == "__main__":
    main()
