"""Configuration management for K6 Performance Testing Agent.

This module provides comprehensive configuration management with:
- Environment-based configuration
- K6 runtime settings
- Monitoring and reporting options
- Knowledge base integration settings
"""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
import os
import tempfile
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# pragma: no cover  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002Tms5eVZBPT06OWY0ZDgyYmY=


class Environment(str, Enum):
    """Deployment environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class K6Config:
    """K6 runtime configuration.
    
    Attributes:
        binary_path: Path to K6 binary (default: "k6" from PATH).
        scripts_dir: Directory for generated K6 scripts.
        results_dir: Directory for test results.
        default_vus: Default number of virtual users.
        default_duration: Default test duration.
        default_iterations: Default number of iterations.
        env_vars: Environment variables for K6 execution.
        tags: Default tags for test runs.
        no_connection_reuse: Disable connection reuse.
        no_vu_connection_reuse: Disable VU connection reuse.
        batch: Batch size for batch requests.
        batch_per_host: Batch size per host.
        insecure_skip_tls_verify: Skip TLS verification.
        user_agent: Custom user agent string.
    """
    binary_path: str = field(default_factory=lambda: os.getenv("K6_BINARY_PATH", "k6"))
    scripts_dir: Path = field(default_factory=lambda: Path(os.getenv("K6_SCRIPTS_DIR", "./k6_scripts")))
    results_dir: Path = field(default_factory=lambda: Path(os.getenv("K6_RESULTS_DIR", "./k6_results")))
    default_vus: int = field(default_factory=lambda: int(os.getenv("K6_DEFAULT_VUS", "10")))
    default_duration: str = field(default_factory=lambda: os.getenv("K6_DEFAULT_DURATION", "30s"))
    default_iterations: Optional[int] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    no_connection_reuse: bool = False
    no_vu_connection_reuse: bool = False
    batch: int = field(default_factory=lambda: int(os.getenv("K6_BATCH_SIZE", "20")))
    batch_per_host: int = field(default_factory=lambda: int(os.getenv("K6_BATCH_PER_HOST", "6")))
    insecure_skip_tls_verify: bool = False
    user_agent: Optional[str] = None
    
    def __post_init__(self):
        """Ensure directories exist."""
        self.scripts_dir = Path(self.scripts_dir)
        self.results_dir = Path(self.results_dir)
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration.
    
    Attributes:
        enable_prometheus: Enable Prometheus metrics export.
        prometheus_port: Port for Prometheus metrics.
        enable_influxdb: Enable InfluxDB output.
        influxdb_url: InfluxDB connection URL.
        enable_datadog: Enable Datadog integration.
        datadog_api_key: Datadog API key.
        enable_cloud: Enable K6 Cloud integration.
        cloud_token: K6 Cloud API token.
        cloud_project_id: K6 Cloud project ID.
    """
    enable_prometheus: bool = field(default_factory=lambda: os.getenv("K6_PROMETHEUS_ENABLED", "false").lower() == "true")
    prometheus_port: int = field(default_factory=lambda: int(os.getenv("K6_PROMETHEUS_PORT", "6565")))
    enable_influxdb: bool = field(default_factory=lambda: os.getenv("K6_INFLUXDB_ENABLED", "false").lower() == "true")
    influxdb_url: Optional[str] = field(default_factory=lambda: os.getenv("K6_INFLUXDB_URL"))
    enable_datadog: bool = field(default_factory=lambda: os.getenv("K6_DATADOG_ENABLED", "false").lower() == "true")
    datadog_api_key: Optional[str] = field(default_factory=lambda: os.getenv("K6_DATADOG_API_KEY"))
    enable_cloud: bool = field(default_factory=lambda: os.getenv("K6_CLOUD_ENABLED", "false").lower() == "true")
    cloud_token: Optional[str] = field(default_factory=lambda: os.getenv("K6_CLOUD_TOKEN"))
    cloud_project_id: Optional[str] = field(default_factory=lambda: os.getenv("K6_CLOUD_PROJECT_ID"))
# noqa  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002Tms5eVZBPT06OWY0ZDgyYmY=


@dataclass
class ReportConfig:
    """Report generation configuration.
    
    Attributes:
        reports_dir: Directory for generated reports.
        charts_dir: Directory for generated charts.
        template_dir: Directory for report templates.
        default_format: Default report format (html, pdf, json).
        include_charts: Include charts in reports.
        include_raw_data: Include raw data in reports.
        chart_width: Default chart width in pixels.
        chart_height: Default chart height in pixels.
    """
    reports_dir: Path = field(default_factory=lambda: Path(os.getenv("K6_REPORTS_DIR", "./k6_reports")))
    charts_dir: Path = field(default_factory=lambda: Path(os.getenv("K6_CHARTS_DIR", "./k6_charts")))
    template_dir: Optional[Path] = None
    default_format: str = field(default_factory=lambda: os.getenv("K6_REPORT_FORMAT", "html"))
    include_charts: bool = field(default_factory=lambda: os.getenv("K6_INCLUDE_CHARTS", "true").lower() == "true")
    include_raw_data: bool = field(default_factory=lambda: os.getenv("K6_INCLUDE_RAW_DATA", "false").lower() == "true")
    chart_width: int = field(default_factory=lambda: int(os.getenv("K6_CHART_WIDTH", "800")))
    chart_height: int = field(default_factory=lambda: int(os.getenv("K6_CHART_HEIGHT", "400")))
    
    def __post_init__(self):
        """Ensure directories exist."""
        self.reports_dir = Path(self.reports_dir)
        self.charts_dir = Path(self.charts_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.charts_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class KnowledgeConfig:
    """Knowledge base integration configuration.

    Attributes:
        enabled: Enable knowledge base integration.
        api_url: URL of the RAG knowledge base API.
        api_key: Optional API key for authentication.
        default_mode: Default query mode (mix, local, global, hybrid, naive).
        top_k: Default number of entities/relationships to retrieve.
        chunk_top_k: Default number of text chunks to retrieve.
        timeout: Request timeout in seconds.
        cache_enabled: Enable response caching.
        cache_ttl: Cache TTL in seconds.
    """
    enabled: bool = field(default_factory=lambda: os.getenv("KNOWLEDGE_ENABLED", "true").lower() == "true")
    api_url: str = field(default_factory=lambda: os.getenv("KNOWLEDGE_API_URL", "http://localhost:8000"))
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("KNOWLEDGE_API_KEY"))
    default_mode: str = field(default_factory=lambda: os.getenv("KNOWLEDGE_DEFAULT_MODE", "mix"))
    top_k: int = field(default_factory=lambda: int(os.getenv("KNOWLEDGE_TOP_K", "10")))
    chunk_top_k: int = field(default_factory=lambda: int(os.getenv("KNOWLEDGE_CHUNK_TOP_K", "5")))
    timeout: float = field(default_factory=lambda: float(os.getenv("KNOWLEDGE_TIMEOUT", "30.0")))
    cache_enabled: bool = field(default_factory=lambda: os.getenv("KNOWLEDGE_CACHE_ENABLED", "true").lower() == "true")
    cache_ttl: int = field(default_factory=lambda: int(os.getenv("KNOWLEDGE_CACHE_TTL", "3600")))


@dataclass
class K6AgentConfig:
    """Main configuration for K6 Performance Testing Agent.

    This is the primary configuration class that aggregates all sub-configurations
    and provides environment-based configuration loading.

    Attributes:
        environment: Deployment environment.
        k6: K6 runtime configuration.
        monitoring: Monitoring and observability settings.
        report: Report generation settings.
        knowledge: Knowledge base integration settings.
        debug: Enable debug mode.
        log_level: Logging level.
        workspace_dir: Base workspace directory.
        max_concurrent_tests: Maximum concurrent test executions.
        test_timeout: Maximum test execution time in seconds.
        enable_longterm_memory: Enable cross-session memory.

    Example:
        >>> config = K6AgentConfig.from_env()
        >>> config = K6AgentConfig(
        ...     environment=Environment.PRODUCTION,
        ...     k6=K6Config(default_vus=100),
        ...     knowledge=KnowledgeConfig(api_url="http://rag.example.com"),
        ... )
    """
    environment: Environment = Environment.DEVELOPMENT
    k6: K6Config = field(default_factory=K6Config)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    knowledge: KnowledgeConfig = field(default_factory=KnowledgeConfig)
    debug: bool = False
    log_level: str = "INFO"
    workspace_dir: Path = field(default_factory=lambda: Path("./k6_workspace"))
    max_concurrent_tests: int = 5
    test_timeout: int = 3600
    enable_longterm_memory: bool = False

    def __post_init__(self):
        """Initialize workspace directory."""
        self.workspace_dir = Path(self.workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
# type: ignore  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002Tms5eVZBPT06OWY0ZDgyYmY=

    @classmethod
    def from_env(cls) -> "K6AgentConfig":
        """Create configuration from environment variables.

        Environment variables:
            K6_AGENT_ENV: Environment (development, staging, production)
            K6_AGENT_DEBUG: Enable debug mode
            K6_AGENT_LOG_LEVEL: Logging level
            K6_BINARY_PATH: Path to K6 binary
            K6_SCRIPTS_DIR: Directory for K6 scripts
            K6_RESULTS_DIR: Directory for test results
            K6_REPORTS_DIR: Directory for reports
            K6_DEFAULT_VUS: Default virtual users
            K6_DEFAULT_DURATION: Default test duration
            KNOWLEDGE_API_URL: Knowledge base API URL
            KNOWLEDGE_API_KEY: Knowledge base API key
            K6_CLOUD_TOKEN: K6 Cloud API token

        Returns:
            K6AgentConfig instance configured from environment.
        """
        env_str = os.getenv("K6_AGENT_ENV", "development").lower()
        environment = Environment(env_str) if env_str in [e.value for e in Environment] else Environment.DEVELOPMENT

        k6 = K6Config(
            binary_path=os.getenv("K6_BINARY_PATH", "k6"),
            scripts_dir=Path(os.getenv("K6_SCRIPTS_DIR", "./k6_scripts")),
            results_dir=Path(os.getenv("K6_RESULTS_DIR", "./k6_results")),
            default_vus=int(os.getenv("K6_DEFAULT_VUS", "10")),
            default_duration=os.getenv("K6_DEFAULT_DURATION", "30s"),
        )

        monitoring = MonitoringConfig(
            enable_cloud=bool(os.getenv("K6_CLOUD_TOKEN")),
            cloud_token=os.getenv("K6_CLOUD_TOKEN"),
            cloud_project_id=os.getenv("K6_CLOUD_PROJECT_ID"),
        )

        report = ReportConfig(
            reports_dir=Path(os.getenv("K6_REPORTS_DIR", "./k6_reports")),
            charts_dir=Path(os.getenv("K6_CHARTS_DIR", "./k6_charts")),
        )

        knowledge = KnowledgeConfig(
            enabled=os.getenv("KNOWLEDGE_ENABLED", "true").lower() == "true",
            api_url=os.getenv("KNOWLEDGE_API_URL", "http://localhost:8000"),
            api_key=os.getenv("KNOWLEDGE_API_KEY"),
        )

        return cls(
            environment=environment,
            k6=k6,
            monitoring=monitoring,
            report=report,
            knowledge=knowledge,
            debug=os.getenv("K6_AGENT_DEBUG", "false").lower() == "true",
            log_level=os.getenv("K6_AGENT_LOG_LEVEL", "INFO"),
            workspace_dir=Path(os.getenv("K6_WORKSPACE_DIR", "./k6_workspace")),
            enable_longterm_memory=os.getenv("K6_LONGTERM_MEMORY", "false").lower() == "true",
        )

    def get_script_path(self, script_name: str) -> Path:
        """Get full path for a K6 script."""
        return self.k6.scripts_dir / f"{script_name}.js"

    def get_result_path(self, test_name: str, extension: str = "json") -> Path:
        """Get full path for a test result file."""
        return self.k6.results_dir / f"{test_name}.{extension}"

    def get_report_path(self, report_name: str) -> Path:
        """Get full path for a report file."""
        return self.report.reports_dir / f"{report_name}.{self.report.default_format}"

    def get_chart_path(self, chart_name: str, extension: str = "png") -> Path:
        """Get full path for a chart file."""
        return self.report.charts_dir / f"{chart_name}.{extension}"

    def get_temp_script_path(self, script_name: str) -> Path:
        """Get a cross-platform temporary path for a K6 script.

        This uses the system's temp directory which works on both
        Windows and Unix systems.

        Args:
            script_name: Name of the script file (without extension).

        Returns:
            Full path to the temp script file.
        """
        # Use configured scripts_dir if it exists, otherwise use system temp
        if self.k6.scripts_dir.exists():
            return self.k6.scripts_dir / f"{script_name}.js"
        else:
            temp_dir = Path(tempfile.gettempdir()) / "k6_scripts"
            temp_dir.mkdir(parents=True, exist_ok=True)
            return temp_dir / f"{script_name}.js"

    @staticmethod
    def get_platform_temp_dir() -> Path:
        """Get platform-specific temporary directory for K6 scripts.

        Returns:
            Path to temp directory that works on Windows and Unix.
        """
        temp_dir = Path(tempfile.gettempdir()) / "k6_scripts"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir
# type: ignore  My80OmFIVnBZMlhtblk3a3ZiUG1yS002Tms5eVZBPT06OWY0ZDgyYmY=

