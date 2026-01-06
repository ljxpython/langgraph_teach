"""K6任务管理 - 异步执行和状态监控."""
import json
import subprocess
import uuid
import threading
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable

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
    relative_path = virtual_path.lstrip("/")
    return Path(workspace_root).resolve() / relative_path


def _to_virtual_path(base_dir: str, filename: str) -> str:
    """生成虚拟路径.

    Args:
        base_dir: 虚拟目录（如 /k6_results）
        filename: 文件名

    Returns:
        虚拟路径（如 /k6_results/result.json）
    """
    if not base_dir.startswith("/"):
        base_dir = "/" + base_dir
    base_dir = base_dir.rstrip("/")
    return f"{base_dir}/{filename}"


class TaskStatus(str, Enum):
    """任务状态."""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class K6Task:
    """K6测试任务."""
    task_id: str
    script_path: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None
    progress: int = 0  # 0-100
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典."""
        return {
            "task_id": self.task_id,
            "script_path": self.script_path,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
        }


class K6TaskManager:
    """K6任务管理器 - 管理异步任务执行和状态."""
    
    def __init__(self, config: K6Config | None = None):
        """初始化任务管理器."""
        self.config = config or DEFAULT_CONFIG
        self._tasks: dict[str, K6Task] = {}
        self._lock = threading.Lock()
        self._on_complete: Callable[[K6Task], None] | None = None
    
    def set_on_complete(self, callback: Callable[[K6Task], None]) -> None:
        """设置任务完成回调."""
        self._on_complete = callback
    
    def submit_task(self, script_path: str) -> str:
        """提交K6执行任务到队列.
        
        Args:
            script_path: K6脚本路径
            
        Returns:
            任务ID
        """
        task_id = f"k6_{uuid.uuid4().hex[:12]}"
        task = K6Task(
            task_id=task_id,
            script_path=script_path,
            created_at=datetime.now().isoformat(),
        )
        
        with self._lock:
            self._tasks[task_id] = task
        
        # 在后台线程执行任务
        thread = threading.Thread(
            target=self._execute_task,
            args=(task_id,),
            daemon=True,
        )
        thread.start()
        
        return task_id
    
    def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """获取任务状态.
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态字典，不存在返回None
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                return task.to_dict()
        return None
    
    def get_all_tasks(self) -> list[dict[str, Any]]:
        """获取所有任务."""
        with self._lock:
            return [t.to_dict() for t in self._tasks.values()]
    
    def get_running_tasks(self) -> list[dict[str, Any]]:
        """获取正在运行的任务."""
        with self._lock:
            return [
                t.to_dict() for t in self._tasks.values()
                if t.status == TaskStatus.RUNNING
            ]
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务（仅限等待中的任务）."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                return True
        return False
    
    def _execute_task(self, task_id: str) -> None:
        """执行K6任务（在后台线程运行）."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status == TaskStatus.CANCELLED:
                return
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now().isoformat()

        try:
            # 将虚拟脚本路径解析为实际路径
            actual_script_path = _resolve_virtual_path(task.script_path, self.config.workspace_root)

            # 生成结果文件的虚拟路径和实际路径
            result_filename = f"result_{task_id}.json"
            virtual_result_path = _to_virtual_path(self.config.results_dir, result_filename)
            actual_result_path = _resolve_virtual_path(virtual_result_path, self.config.workspace_root)

            # 确保结果目录存在
            actual_result_path.parent.mkdir(parents=True, exist_ok=True)

            # 构建K6命令（使用实际路径）
            cmd = [
                self.config.k6_binary,
                "run",
                str(actual_script_path),
                "--out", f"json={actual_result_path}",
            ]

            # 执行K6
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # 模拟进度更新
            self._update_progress(task_id, process)

            # 等待完成
            stdout, stderr = process.communicate(timeout=600)

            # 更新任务状态
            with self._lock:
                task = self._tasks.get(task_id)
                if task:
                    task.completed_at = datetime.now().isoformat()
                    task.progress = 100

                    if process.returncode == 0:
                        task.status = TaskStatus.COMPLETED
                        task.result = {
                            "success": True,
                            "result_file": virtual_result_path,  # 返回虚拟路径
                            "stdout": stdout,
                        }
                        # 解析结果
                        if actual_result_path.exists():
                            task.result["metrics"] = self._parse_results(actual_result_path)
                    else:
                        task.status = TaskStatus.FAILED
                        task.error = stderr
                        task.result = {"success": False, "stderr": stderr}
            
            # 触发完成回调
            if self._on_complete and task:
                self._on_complete(task)
                
        except subprocess.TimeoutExpired:
            with self._lock:
                task = self._tasks.get(task_id)
                if task:
                    task.status = TaskStatus.FAILED
                    task.error = "执行超时（>10分钟）"
                    task.completed_at = datetime.now().isoformat()
        except Exception as e:
            with self._lock:
                task = self._tasks.get(task_id)
                if task:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.completed_at = datetime.now().isoformat()
    
    def _update_progress(self, task_id: str, process: subprocess.Popen) -> None:
        """更新任务进度（模拟）."""
        def update():
            progress = 0
            while process.poll() is None and progress < 95:
                time.sleep(2)
                progress = min(progress + 5, 95)
                with self._lock:
                    task = self._tasks.get(task_id)
                    if task:
                        task.progress = progress
        
        thread = threading.Thread(target=update, daemon=True)
        thread.start()
    
    def _parse_results(self, result_file: Path) -> dict[str, Any]:
        """解析K6结果文件."""
        metrics = {
            "http_req_duration": {"values": []},
            "http_reqs": {"count": 0},
            "vus": {"max": 0},
        }
        
        try:
            with open(result_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if data.get("type") == "Point":
                            metric = data.get("metric")
                            value = data.get("data", {}).get("value", 0)
                            
                            if metric == "http_req_duration":
                                metrics["http_req_duration"]["values"].append(value)
                            elif metric == "http_reqs":
                                metrics["http_reqs"]["count"] += 1
                            elif metric == "vus":
                                metrics["vus"]["max"] = max(metrics["vus"]["max"], value)
                    except:
                        continue
            
            # 计算统计值
            durations = metrics["http_req_duration"]["values"]
            if durations:
                durations.sort()
                metrics["http_req_duration"] = {
                    "avg": sum(durations) / len(durations),
                    "min": durations[0],
                    "max": durations[-1],
                    "p95": durations[int(len(durations) * 0.95)],
                }
        except:
            pass
        
        return metrics


# 全局任务管理器
_task_manager: K6TaskManager | None = None


def get_task_manager(config: K6Config | None = None) -> K6TaskManager:
    """获取全局任务管理器."""
    global _task_manager
    if _task_manager is None:
        _task_manager = K6TaskManager(config)
    return _task_manager


def create_task_tools(config: K6Config | None = None) -> list[BaseTool]:
    """创建任务管理工具."""
    manager = get_task_manager(config)

    def submit_k6_task(script_path: str) -> str:
        """提交K6测试任务到执行队列（异步执行）.

        Args:
            script_path: K6脚本虚拟路径（以 / 开头，如 /k6_scripts/test.js）

        Returns:
            任务ID和状态信息
        """
        task_id = manager.submit_task(script_path)
        return json.dumps({
            "task_id": task_id,
            "status": "pending",
            "message": f"任务已提交，可通过task_id查询状态",
        }, ensure_ascii=False)

    def get_task_status(task_id: str) -> str:
        """查询K6任务执行状态.

        Args:
            task_id: 任务ID

        Returns:
            任务状态详情
        """
        status = manager.get_task_status(task_id)
        if status:
            return json.dumps(status, ensure_ascii=False, indent=2)
        return json.dumps({"error": f"任务不存在: {task_id}"}, ensure_ascii=False)

    def list_all_tasks() -> str:
        """列出所有K6测试任务.

        Returns:
            所有任务列表
        """
        tasks = manager.get_all_tasks()
        return json.dumps(tasks, ensure_ascii=False, indent=2)

    def get_running_tasks() -> str:
        """获取正在执行的K6任务.

        Returns:
            运行中的任务列表
        """
        tasks = manager.get_running_tasks()
        return json.dumps(tasks, ensure_ascii=False, indent=2)

    return [
        StructuredTool.from_function(
            name="submit_k6_task",
            func=submit_k6_task,
            description="提交K6性能测试任务到执行队列（异步执行）。参数：script_path(虚拟路径，如 /k6_scripts/test.js)。立即返回任务ID",
        ),
        StructuredTool.from_function(
            name="get_task_status",
            func=get_task_status,
            description="查询K6任务的执行状态、进度和结果。参数：task_id(任务ID)",
        ),
        StructuredTool.from_function(
            name="list_all_tasks",
            func=list_all_tasks,
            description="列出所有K6测试任务及其状态",
        ),
        StructuredTool.from_function(
            name="get_running_tasks",
            func=get_running_tasks,
            description="获取当前正在执行的K6任务",
        ),
    ]

