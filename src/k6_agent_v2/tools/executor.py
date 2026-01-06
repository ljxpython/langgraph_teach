"""K6脚本执行工具."""
import json
import os
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.tools import StructuredTool, BaseTool

from k6_agent.config import K6Config, DEFAULT_CONFIG


def _resolve_virtual_path(virtual_path: str, workspace_root: str) -> Path:
    """将虚拟路径解析为实际文件系统路径.

    虚拟路径以 / 开头，例如 /k6_scripts/test.js
    映射到 {workspace_root}/k6_scripts/test.js

    Args:
        virtual_path: 虚拟路径（以 / 开头）
        workspace_root: 工作空间根目录

    Returns:
        实际文件系统路径
    """
    # 移除开头的 /
    relative_path = virtual_path.lstrip("/")
    return Path(workspace_root).resolve() / relative_path


def _to_virtual_path(scripts_dir: str, script_name: str) -> str:
    """生成虚拟路径.

    Args:
        scripts_dir: 虚拟脚本目录（如 /k6_scripts）
        script_name: 脚本名称

    Returns:
        虚拟路径（如 /k6_scripts/test.js）
    """
    # 确保目录以 / 开头
    if not scripts_dir.startswith("/"):
        scripts_dir = "/" + scripts_dir
    # 移除末尾的 /
    scripts_dir = scripts_dir.rstrip("/")
    return f"{scripts_dir}/{script_name}"


def create_script_save_tool(config: K6Config | None = None) -> BaseTool:
    """创建K6脚本保存工具.

    Args:
        config: K6配置

    Returns:
        脚本保存工具
    """
    cfg = config or DEFAULT_CONFIG

    def save_k6_script(script_content: str, script_name: str = "") -> str:
        """保存K6测试脚本到文件.

        Args:
            script_content: K6脚本内容
            script_name: 脚本名称（可选，默认自动生成）

        Returns:
            保存的脚本虚拟路径（以 / 开头）
        """
        # 生成脚本名称
        if not script_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            script_name = f"test_{timestamp}.js"
        elif not script_name.endswith(".js"):
            script_name = f"{script_name}.js"

        # 生成虚拟路径
        virtual_path = _to_virtual_path(cfg.scripts_dir, script_name)

        # 解析为实际路径
        actual_path = _resolve_virtual_path(virtual_path, cfg.workspace_root)

        # 确保目录存在
        actual_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存脚本
        actual_path.write_text(script_content, encoding="utf-8")

        # 返回虚拟路径（用于 deepagents 的文件系统工具）
        return virtual_path

    return StructuredTool.from_function(
        name="save_k6_script",
        func=save_k6_script,
        description="保存K6测试脚本到文件。参数：script_content(脚本内容), script_name(可选，脚本名称)。返回虚拟路径(如 /k6_scripts/test.js)",
    )


def create_k6_executor_tool(config: K6Config | None = None) -> BaseTool:
    """创建K6脚本执行工具.

    Args:
        config: K6配置

    Returns:
        K6执行工具
    """
    cfg = config or DEFAULT_CONFIG

    def run_k6_script(script_path: str, output_format: str = "json") -> str:
        """执行K6测试脚本.

        Args:
            script_path: K6脚本虚拟路径（以 / 开头，如 /k6_scripts/test.js）
            output_format: 输出格式 (json/text)

        Returns:
            测试结果（JSON格式或文本）
        """
        # 将虚拟路径解析为实际路径
        actual_script_path = _resolve_virtual_path(script_path, cfg.workspace_root)

        # 确保结果目录存在（实际路径）
        result_name = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}.json"
        virtual_result_path = _to_virtual_path(cfg.results_dir, result_name)
        actual_result_path = _resolve_virtual_path(virtual_result_path, cfg.workspace_root)
        actual_result_path.parent.mkdir(parents=True, exist_ok=True)

        # 构建K6命令（使用实际路径）
        cmd = [
            cfg.k6_binary,
            "run",
            str(actual_script_path),
            "--out", f"json={actual_result_path}",
        ]

        try:
            # 执行K6
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10分钟超时
            )

            # 解析结果（返回虚拟路径）
            output = {
                "success": result.returncode == 0,
                "script_path": script_path,  # 虚拟路径
                "result_file": virtual_result_path,  # 虚拟路径
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
            }

            # 如果有结果文件，读取并解析
            if actual_result_path.exists():
                output["metrics"] = _parse_k6_json_output(actual_result_path)

            return json.dumps(output, ensure_ascii=False, indent=2)

        except subprocess.TimeoutExpired:
            return json.dumps({
                "success": False,
                "error": "K6执行超时（>10分钟）",
                "script_path": script_path,
            }, ensure_ascii=False)
        except FileNotFoundError:
            return json.dumps({
                "success": False,
                "error": f"K6未安装或路径错误: {cfg.k6_binary}",
                "script_path": script_path,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "script_path": script_path,
            }, ensure_ascii=False)
    
    return StructuredTool.from_function(
        name="run_k6_script",
        func=run_k6_script,
        description="执行K6性能测试脚本。参数：script_path(脚本路径), output_format(可选，输出格式)",
    )


def _parse_k6_json_output(result_file: Path) -> dict[str, Any]:
    """解析K6 JSON输出文件.
    
    Args:
        result_file: K6输出的JSON文件路径
        
    Returns:
        解析后的指标数据
    """
    metrics = {
        "http_req_duration": {"values": []},
        "http_reqs": {"count": 0},
        "http_req_failed": {"rate": 0},
        "vus": {"max": 0},
        "iterations": {"count": 0},
    }
# pylint: disable
    
    try:
        with open(result_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    metric_type = data.get("type")
                    metric_name = data.get("metric")
                    
                    if metric_type == "Point":
                        value = data.get("data", {}).get("value", 0)
                        
                        if metric_name == "http_req_duration":
                            metrics["http_req_duration"]["values"].append(value)
                        elif metric_name == "http_reqs":
                            metrics["http_reqs"]["count"] += 1
                        elif metric_name == "vus":
                            metrics["vus"]["max"] = max(metrics["vus"]["max"], value)
                        elif metric_name == "iterations":
                            metrics["iterations"]["count"] += 1
                            
                except json.JSONDecodeError:
                    continue
        
        # 计算统计值
        durations = metrics["http_req_duration"]["values"]
        if durations:
            durations.sort()
            metrics["http_req_duration"]["avg"] = sum(durations) / len(durations)
            metrics["http_req_duration"]["min"] = durations[0]
            metrics["http_req_duration"]["max"] = durations[-1]
            metrics["http_req_duration"]["p90"] = durations[int(len(durations) * 0.9)]
            metrics["http_req_duration"]["p95"] = durations[int(len(durations) * 0.95)]
            metrics["http_req_duration"]["p99"] = durations[int(len(durations) * 0.99)]
            # 移除原始值以减少数据量
            del metrics["http_req_duration"]["values"]
            
    except Exception as e:
        metrics["parse_error"] = str(e)
    
    return metrics

