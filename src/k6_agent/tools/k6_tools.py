"""K6 script generation tools.

This module provides tools for generating K6 performance test scripts
with modern scenarios, executors, and best practices.
"""
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from k6_agent.k6.scenarios import (
    K6Options,
    K6Scenario,
    ExecutorType,
    Stage,
    CustomMetric,
    MetricType,
    TestData,
    Threshold,
)

# type: ignore  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002ZUd3eWJBPT06ZWIzZTkyMWM=

class HttpMethod(str, Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class ApiEndpoint:
    """API endpoint definition.
    
    Attributes:
        name: Endpoint name for grouping.
        url: Endpoint URL (can include ${} variables).
        method: HTTP method.
        headers: Request headers.
        body: Request body (for POST/PUT/PATCH).
        params: URL parameters.
        checks: Response checks to perform.
        weight: Relative weight for random selection.
    """
    name: str
    url: str
    method: HttpMethod = HttpMethod.GET
    headers: Optional[Dict[str, str]] = None
    body: Optional[str] = None
    params: Optional[Dict[str, str]] = None
    checks: Optional[Dict[str, str]] = None
    weight: int = 1
    
    def to_k6_request(self) -> str:
        """Generate K6 request code."""
        lines = []
        
        # Build params object
        params_parts = []
        if self.headers:
            headers_json = json.dumps(self.headers)
            params_parts.append(f"headers: {headers_json}")
        if self.params:
            params_json = json.dumps(self.params)
            params_parts.append(f"tags: {params_json}")
        
        params_str = ""
        if params_parts:
            params_str = ", { " + ", ".join(params_parts) + " }"
        
        # Generate request
        if self.method == HttpMethod.GET:
            lines.append(f"const res = http.get(`{self.url}`{params_str});")
        elif self.method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH]:
            body = self.body or "{}"
            method = self.method.value.lower()
            lines.append(f"const res = http.{method}(`{self.url}`, {body}{params_str});")
        elif self.method == HttpMethod.DELETE:
            lines.append(f"const res = http.del(`{self.url}`{params_str});")
        else:
            lines.append(f"const res = http.request('{self.method.value}', `{self.url}`{params_str});")
        
        # Generate checks
        if self.checks:
            checks_json = json.dumps(self.checks, indent=4)
            # Convert check expressions to functions
            checks_code = checks_json.replace('"(r) =>', '(r) =>').replace('}"', '}')
            lines.append(f"check(res, {checks_code});")
        else:
            lines.append("check(res, { 'status is 200': (r) => r.status === 200 });")
        
        return "\n    ".join(lines)


@dataclass
class K6ScriptGenerator:
    """K6 script generator with modern best practices.
    
    This class generates complete K6 scripts with:
    - Modern scenarios and executors
    - Proper imports and structure
    - Custom metrics and thresholds
    - Data parameterization support
    - Comprehensive checks
    """
    
    base_url: str
    endpoints: List[ApiEndpoint] = field(default_factory=list)
    options: Optional[K6Options] = None
    custom_metrics: List[CustomMetric] = field(default_factory=list)
    test_data: Optional[TestData] = None
    setup_code: Optional[str] = None
    teardown_code: Optional[str] = None
# noqa  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002ZUd3eWJBPT06ZWIzZTkyMWM=
    
    def add_endpoint(self, endpoint: ApiEndpoint) -> "K6ScriptGenerator":
        """Add an endpoint to test."""
        self.endpoints.append(endpoint)
        return self
    
    def add_custom_metric(self, metric: CustomMetric) -> "K6ScriptGenerator":
        """Add a custom metric."""
        self.custom_metrics.append(metric)
        return self
    
    def set_options(self, options: K6Options) -> "K6ScriptGenerator":
        """Set test options."""
        self.options = options
        return self
    
    def set_test_data(self, test_data: TestData) -> "K6ScriptGenerator":
        """Set test data configuration."""
        self.test_data = test_data
        return self

    def generate(self) -> str:
        """Generate complete K6 script."""
        sections = []

        # Imports
        sections.append(self._generate_imports())

        # Custom metrics
        if self.custom_metrics:
            sections.append(self._generate_custom_metrics())

        # Test data
        if self.test_data:
            sections.append(self.test_data.to_declaration())

        # Options
        if self.options:
            sections.append(self.options.to_javascript())

        # Setup function
        if self.setup_code:
            sections.append(f"""
export function setup() {{
{self.setup_code}
}}""")

        # Main function
        sections.append(self._generate_main_function())

        # Teardown function
        if self.teardown_code:
            sections.append(f"""
export function teardown(data) {{
{self.teardown_code}
}}""")

        return "\n\n".join(sections)

    def _generate_imports(self) -> str:
        """Generate import statements."""
        imports = [
            "import http from 'k6/http';",
            "import { check, group, sleep } from 'k6';",
        ]

        # Add metric imports
        metric_types = set(m.metric_type for m in self.custom_metrics)
        if metric_types:
            types_str = ", ".join(t.value for t in metric_types)
            imports.append(f"import {{ {types_str} }} from 'k6/metrics';")
# pragma: no cover  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002ZUd3eWJBPT06ZWIzZTkyMWM=

        # Add data import
        if self.test_data:
            imports.append(self.test_data.to_import())

        return "\n".join(imports)

    def _generate_custom_metrics(self) -> str:
        """Generate custom metric declarations."""
        return "\n".join(m.to_declaration() for m in self.custom_metrics)

    def _generate_main_function(self) -> str:
        """Generate main test function."""
        lines = ["export default function(data) {"]

        # Add base URL constant
        lines.append(f"  const BASE_URL = '{self.base_url}';")
        lines.append("")

        # Generate endpoint groups
        for endpoint in self.endpoints:
            lines.append(f"  group('{endpoint.name}', function() {{")
            lines.append(f"    {endpoint.to_k6_request()}")
            lines.append("  });")
            lines.append("")

        # Add sleep between iterations
        lines.append("  sleep(1);")
        lines.append("}")

        return "\n".join(lines)

    def save(self, path: Path) -> Path:
        """Save script to file."""
        script = self.generate()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(script, encoding="utf-8")
        return path


# ============================================================================
# LangChain Tool Factories
# ============================================================================

class ScriptGenerationInput(BaseModel):
    """Input schema for K6 script generation."""
    base_url: str = Field(description="Base URL of the API to test")
    endpoints: List[Dict[str, Any]] = Field(
        description="List of endpoint configurations with name, url, method, etc."
    )
    test_type: str = Field(
        default="load",
        description="Type of test: smoke, load, stress, spike, soak, breakpoint"
    )
    vus: Optional[int] = Field(default=None, description="Number of virtual users")
    duration: Optional[str] = Field(default=None, description="Test duration")


class ScriptValidationInput(BaseModel):
    """Input schema for K6 script validation."""
    script_path: str = Field(description="Path to the K6 script to validate")


def create_k6_script_tool():
    """Create a K6 script generation tool."""

    @tool(args_schema=ScriptGenerationInput)
    def generate_k6_script(
        base_url: str,
        endpoints: List[Dict[str, Any]],
        test_type: str = "load",
        vus: Optional[int] = None,
        duration: Optional[str] = None,
    ) -> str:
        """Generate a K6 performance test script.

        Creates a complete K6 script with modern scenarios, proper structure,
        and best practices for the specified test type.

        Args:
            base_url: Base URL of the API to test.
            endpoints: List of endpoint configurations.
            test_type: Type of test (smoke, load, stress, spike, soak, breakpoint).
            vus: Optional number of virtual users.
            duration: Optional test duration.

        Returns:
            Generated K6 script as a string.
        """
        from k6_agent.k6.scenarios import (
            create_smoke_test_options,
            create_load_test_options,
            create_stress_test_options,
            create_spike_test_options,
            create_soak_test_options,
            create_breakpoint_test_options,
        )

        # Create options based on test type
        options_factory = {
            "smoke": create_smoke_test_options,
            "load": create_load_test_options,
            "stress": create_stress_test_options,
            "spike": create_spike_test_options,
            "soak": create_soak_test_options,
            "breakpoint": create_breakpoint_test_options,
        }
# pragma: no cover  My80OmFIVnBZMlhtblk3a3ZiUG1yS002ZUd3eWJBPT06ZWIzZTkyMWM=

        factory = options_factory.get(test_type, create_load_test_options)
        options = factory()

        # Parse endpoints
        parsed_endpoints = []
        for ep in endpoints:
            parsed_endpoints.append(ApiEndpoint(
                name=ep.get("name", "endpoint"),
                url=ep.get("url", "/"),
                method=HttpMethod(ep.get("method", "GET")),
                headers=ep.get("headers"),
                body=ep.get("body"),
                checks=ep.get("checks"),
            ))

        # Generate script
        generator = K6ScriptGenerator(
            base_url=base_url,
            endpoints=parsed_endpoints,
            options=options,
        )

        return generator.generate()

    return generate_k6_script


def _get_workspace_root() -> str:
    """Get the K6 workspace root directory.

    This returns the root directory used by DeepAgents FilesystemBackend.
    It checks the K6_WORKSPACE_DIR environment variable first, then falls back
    to ./k6_workspace in the current working directory.

    Returns:
        Absolute path to the workspace root.
    """
    import os
    from pathlib import Path

    # Check environment variable first (same as K6AgentConfig)
    workspace_dir = os.getenv("K6_WORKSPACE_DIR", "./k6_workspace")
    workspace_path = Path(workspace_dir)

    # Resolve to absolute path
    if not workspace_path.is_absolute():
        workspace_path = Path(os.getcwd()) / workspace_path

    return str(workspace_path.resolve())


def _resolve_virtual_path(virtual_path: str) -> str:
    """Resolve a virtual path to an actual filesystem path.

    Virtual paths start with '/' and are relative to the K6 workspace directory.
    This function converts them to actual filesystem paths that work on all platforms.

    The workspace root is determined by K6_WORKSPACE_DIR environment variable,
    or defaults to ./k6_workspace in the current working directory.

    Args:
        virtual_path: Virtual path starting with '/' (e.g., /k6_scripts/test.js)

    Returns:
        Actual filesystem path.
    """
    import os

    # If already an absolute path (Windows style), return as-is for backwards compatibility
    if os.path.isabs(virtual_path) and not virtual_path.startswith('/'):
        return virtual_path

    # Get workspace root (same as FilesystemBackend uses)
    workspace_root = _get_workspace_root()

    # Strip leading slash and convert to relative path
    rel_path = virtual_path.lstrip('/')

    # Convert forward slashes to platform-specific separator
    rel_path = rel_path.replace('/', os.sep)

    # Resolve relative to workspace root
    return os.path.join(workspace_root, rel_path)


def create_k6_validation_tool():
    """Create a K6 script validation tool."""

    @tool(args_schema=ScriptValidationInput)
    def validate_k6_script(script_path: str) -> str:
        """Validate a K6 script for syntax errors.

        Runs k6 inspect to check the script for errors without executing it.

        Args:
            script_path: Path to the K6 script to validate. Use virtual paths
                starting with '/' (e.g., /k6_scripts/test.js).

        Returns:
            Validation result message.
        """
        import subprocess
        import os

        # Resolve virtual path to actual filesystem path
        actual_path = _resolve_virtual_path(script_path)

        # Normalize path
        actual_path = os.path.normpath(actual_path)

        # Check if file exists
        if not os.path.exists(actual_path):
            workspace_root = _get_workspace_root()
            return f"""❌ Script file not found: {script_path}
Resolved to: {actual_path}
Workspace root: {workspace_root}

Make sure the script file exists in the workspace. Use virtual paths like:
- /k6_scripts/script_name.js  ->  {workspace_root}/k6_scripts/script_name.js
- /<filename>.js              ->  {workspace_root}/<filename>.js

TIP: Use 'write_file' tool to create the script in the workspace first.
"""

        try:
            result = subprocess.run(
                ["k6", "inspect", actual_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30,
            )

            if result.returncode == 0:
                return f"✅ Script validation passed: {script_path}"
            else:
                return f"❌ Script validation failed:\n{result.stderr}"
        except FileNotFoundError:
            return "❌ K6 binary not found. Please install K6: https://grafana.com/docs/k6/latest/set-up/install-k6/"
        except subprocess.TimeoutExpired:
            return "❌ Script validation timed out."
        except Exception as e:
            return f"❌ Validation error: {str(e)}"

    return validate_k6_script

