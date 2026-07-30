from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory

from deepagents.backends import LocalShellBackend


@dataclass
class ThreadSandboxRegistry:
    root_dir: Path
    sandboxes: dict[str, LocalShellBackend] = field(default_factory=dict)

    def get_or_create(self, thread_id: str) -> LocalShellBackend:
        if not thread_id:
            raise ValueError("thread_id is required")
        if thread_id not in self.sandboxes:
            workspace = self.root_dir / f"thread-{thread_id}"
            workspace.mkdir(parents=True, exist_ok=True)
            self.sandboxes[thread_id] = LocalShellBackend(
                root_dir=workspace,
                virtual_mode=True,
                env={"PATH": "/usr/bin:/bin"},
                timeout=5,
            )
        return self.sandboxes[thread_id]


def read_text(backend: LocalShellBackend, path: str) -> str:
    result = backend.read(path)
    if result.error:
        raise AssertionError(result.error)
    return result.file_data["content"]


def main() -> None:
    with TemporaryDirectory(prefix="deepagents-sandbox-lifecycle-") as tmp:
        registry = ThreadSandboxRegistry(Path(tmp))
        alpha_first = registry.get_or_create("alpha")
        alpha_second = registry.get_or_create("alpha")
        beta = registry.get_or_create("beta")

        assert alpha_first is alpha_second
        assert alpha_first is not beta
        assert alpha_first.id == alpha_second.id
        assert alpha_first.id != beta.id

        alpha_first.write("/note.txt", "created by alpha")
        beta.write("/note.txt", "created by beta")

        alpha_pwd = alpha_second.execute("pwd")
        beta_pwd = beta.execute("pwd")
        assert alpha_pwd.exit_code == 0, alpha_pwd.output
        assert beta_pwd.exit_code == 0, beta_pwd.output
        assert "thread-alpha" in alpha_pwd.output
        assert "thread-beta" in beta_pwd.output

        assert read_text(alpha_second, "/note.txt") == "created by alpha"
        assert read_text(beta, "/note.txt") == "created by beta"

        print(f"alpha backend id: {alpha_first.id}")
        print(f"beta backend id: {beta.id}")
        print("thread-scoped sandbox lifecycle ok")


if __name__ == "__main__":
    main()
