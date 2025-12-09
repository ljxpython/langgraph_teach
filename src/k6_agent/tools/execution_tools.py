"""K6 test execution tools.

This module provides tools for executing K6 performance tests
with proper configuration and monitoring.
"""
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件

import subprocess
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
# fmt: off  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002UWxSdlFRPT06ZjY5YjY3OWY=

from langchain_core.tools import tool
from pydantic import BaseModel, Field


def _get_workspace_root() -> str:
    """Get the K6 workspace root directory.

    This returns the root directory used by DeepAgents FilesystemBackend.
    It checks the K6_WORKSPACE_DIR environment variable first, then falls back
    to ./k6_workspace in the current working directory.

    Returns:
        Absolute path to the workspace root.
    """
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


class K6RunInput(BaseModel):
    """Input schema for K6 test execution."""
    script_path: str = Field(description="Path to the K6 script to execute")
    output_path: Optional[str] = Field(
        default=None,
        description="Path for JSON output file"
    )
    vus: Optional[int] = Field(default=None, description="Override VUs")
    duration: Optional[str] = Field(default=None, description="Override duration")
    env_vars: Optional[Dict[str, str]] = Field(
        default=None,
        description="Environment variables for the test"
    )
    tags: Optional[Dict[str, str]] = Field(
        default=None,
        description="Tags for the test run"
    )


class K6CloudInput(BaseModel):
    """Input schema for K6 Cloud execution."""
    script_path: str = Field(description="Path to the K6 script")
    project_id: Optional[str] = Field(
        default=None,
        description="K6 Cloud project ID"
    )


def create_k6_run_tool():
    """Create a K6 local execution tool."""

    @tool(args_schema=K6RunInput)
    def run_k6_test(
        script_path: str,
        output_path: Optional[str] = None,
        vus: Optional[int] = None,
        duration: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        """Execute a K6 performance test locally.

        Runs the specified K6 script with optional overrides for VUs,
        duration, and environment variables.

        Args:
            script_path: Path to the K6 script to execute. Use virtual paths
                starting with '/' (e.g., /k6_scripts/test.js).
            output_path: Optional path for JSON output. Use virtual paths.
            vus: Optional VU count override.
            duration: Optional duration override.
            env_vars: Optional environment variables.
            tags: Optional tags for the test run.

        Returns:
            Test execution summary with key metrics.
        """
        # Resolve virtual paths to actual filesystem paths
        actual_script_path = _resolve_virtual_path(script_path)
        actual_script_path = os.path.normpath(actual_script_path)

        # Check if script file exists
        if not os.path.exists(actual_script_path):
            workspace_root = _get_workspace_root()
            return f"""❌ Script file not found: {script_path}
Resolved to: {actual_script_path}
Workspace root: {workspace_root}

Make sure the script file exists in the workspace. Use virtual paths like:
- /k6_scripts/script_name.js  ->  {workspace_root}/k6_scripts/script_name.js
- /<filename>.js              ->  {workspace_root}/<filename>.js

TIP: Use 'write_file' tool to create the script in the workspace first.
"""

        # Resolve and normalize output path if provided
        actual_output_path = None
        if output_path:
            actual_output_path = _resolve_virtual_path(output_path)
            actual_output_path = os.path.normpath(actual_output_path)
            # Ensure output directory exists
            output_dir = os.path.dirname(actual_output_path)
            if output_dir and not os.path.isdir(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except FileExistsError:
                    # Directory was created by another process, ignore
                    pass
# pylint: disable  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002UWxSdlFRPT06ZjY5YjY3OWY=

        # Build command
        cmd = ["k6", "run"]
# fmt: off  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002UWxSdlFRPT06ZjY5YjY3OWY=

        # Add output options
        if actual_output_path:
            cmd.extend(["--out", f"json={actual_output_path}"])

        # Add overrides
        if vus:
            cmd.extend(["--vus", str(vus)])
        if duration:
            cmd.extend(["--duration", duration])

        # Add tags
        if tags:
            for key, value in tags.items():
                cmd.extend(["--tag", f"{key}={value}"])

        # Add script path
        cmd.append(actual_script_path)

        # Prepare environment
        env = None
        if env_vars:
            env = os.environ.copy()
            env.update(env_vars)

        try:
            # Execute test
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                timeout=3600,  # 1 hour timeout
            )

            # Parse output
            output = result.stdout + result.stderr

            if result.returncode == 0:
                return f"""✅ Test completed successfully

**Command:** {' '.join(cmd)}

**Output:**
```
{output[-2000:]}
```

**Output file:** {output_path or 'Not saved'}
"""
            else:
                return f"""❌ Test failed with exit code {result.returncode}

**Command:** {' '.join(cmd)}

**Error:**
```
{output[-2000:]}
```
"""
        except FileNotFoundError:
            return "❌ K6 binary not found. Please install K6: https://grafana.com/docs/k6/latest/set-up/install-k6/"
        except subprocess.TimeoutExpired:
            return "❌ Test execution timed out after 1 hour."
        except Exception as e:
            return f"❌ Execution error: {str(e)}"

    return run_k6_test


def create_k6_cloud_tool():
    """Create a K6 Cloud execution tool."""
    
    @tool(args_schema=K6CloudInput)
    def run_k6_cloud(
        script_path: str,
        project_id: Optional[str] = None,
    ) -> str:
        """Execute a K6 test on K6 Cloud.
        
        Uploads and runs the script on K6 Cloud for distributed testing.
        Requires K6_CLOUD_TOKEN environment variable.
        
        Args:
            script_path: Path to the K6 script.
            project_id: Optional K6 Cloud project ID.
            
        Returns:
            Cloud test URL and status.
        """
        import os
        
        if not os.getenv("K6_CLOUD_TOKEN"):
            return "❌ K6_CLOUD_TOKEN environment variable not set."
        
        cmd = ["k6", "cloud"]
        
        if project_id:
            cmd.extend(["--project-id", project_id])
        
        cmd.append(script_path)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=60,  # Cloud upload timeout
            )

            output = result.stdout + result.stderr

            if result.returncode == 0:
                return f"""✅ Test uploaded to K6 Cloud

{output}
"""
            else:
                return f"""❌ Cloud upload failed

{output}
"""
        except Exception as e:
            return f"❌ Cloud execution error: {str(e)}"
    
    return run_k6_cloud
# pylint: disable  My80OmFIVnBZMlhtblk3a3ZiUG1yS002UWxSdlFRPT06ZjY5YjY3OWY=

