"""K6性能测试智能体配置."""
import os
from dataclasses import dataclass, field


def _env(key: str, default: str = "") -> str:
    """获取环境变量."""
    return os.environ.get(key, default)


def _env_int(key: str, default: int = 0) -> int:
    """获取整数环境变量."""
    return int(os.environ.get(key, str(default)))


@dataclass
class K6Config:
    """K6智能体配置."""

    # 工作空间根目录（FilesystemBackend 的根目录）
    # 所有虚拟路径都相对于此目录，如 /k6_scripts/test.js 映射到 {workspace_root}/k6_scripts/test.js
    workspace_root: str = field(default_factory=lambda: _env("K6_WORKSPACE_ROOT", "."))

    # MCP 服务配置
    rag_mcp_url: str = field(default_factory=lambda: _env("K6_RAG_MCP_URL", "http://127.0.0.1:8002/sse"))
    chart_mcp_command: str = field(default_factory=lambda: _env("K6_CHART_MCP_COMMAND", "npx"))
    chart_mcp_args: list[str] = field(default_factory=lambda: ["-y", "@antv/mcp-server-chart"])
    login_mcp_url: str = field(default_factory=lambda: _env("K6_LOGIN_MCP_URL", "http://127.0.0.1:8003/sse"))

    # K6 执行配置
    k6_binary: str = field(default_factory=lambda: _env("K6_BINARY", "k6"))
    # 虚拟路径（以 / 开头）
    scripts_dir: str = field(default_factory=lambda: _env("K6_SCRIPTS_DIR", "/k6_scripts"))
    results_dir: str = field(default_factory=lambda: _env("K6_RESULTS_DIR", "/k6_results"))

    # 默认测试参数
    default_vus: int = field(default_factory=lambda: _env_int("K6_DEFAULT_VUS", 10))
    default_duration: str = field(default_factory=lambda: _env("K6_DEFAULT_DURATION", "1m"))
    default_p95_threshold: int = field(default_factory=lambda: _env_int("K6_DEFAULT_P95_THRESHOLD", 500))


# 默认配置实例
DEFAULT_CONFIG = K6Config()

