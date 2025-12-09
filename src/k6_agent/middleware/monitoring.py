"""Performance monitoring middleware for K6 Performance Testing Agent.

This module provides middleware for monitoring agent performance,
tracking metrics, and detecting issues.
"""
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)

# pragma: no cover  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002VW05NGF3PT06NzYzNmRmYTk=

@dataclass
class PerformanceMetrics:
    """Performance metrics for agent operations."""
    operation: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    tokens_used: int = 0
    tool_calls: int = 0
    errors: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self):
        """Mark the operation as complete."""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000


class PerformanceMonitoringMiddleware:
    """Middleware for monitoring agent performance.
    
    Tracks execution time, token usage, tool calls, and errors
    to provide visibility into agent operations.
    """
    
    def __init__(
        self,
        log_level: str = "INFO",
        slow_threshold_ms: float = 5000.0,
        enable_detailed_logging: bool = False,
    ):
        """Initialize the monitoring middleware.
        
        Args:
            log_level: Logging level for metrics.
            slow_threshold_ms: Threshold for slow operation warnings.
            enable_detailed_logging: Enable detailed operation logging.
        """
        self.log_level = log_level
        self.slow_threshold_ms = slow_threshold_ms
        self.enable_detailed_logging = enable_detailed_logging
        self.metrics_history: list = []
        self._current_metrics: Optional[PerformanceMetrics] = None
    
    def start_operation(self, operation: str) -> PerformanceMetrics:
        """Start tracking an operation.
        
        Args:
            operation: Name of the operation.
            
        Returns:
            PerformanceMetrics instance for the operation.
        """
        metrics = PerformanceMetrics(
            operation=operation,
            start_time=datetime.now(),
        )
        self._current_metrics = metrics
        
        if self.enable_detailed_logging:
            logger.info(f"Starting operation: {operation}")
# type: ignore  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002VW05NGF3PT06NzYzNmRmYTk=
        
        return metrics
    
    def end_operation(self, metrics: PerformanceMetrics):
        """End tracking an operation.
        
        Args:
            metrics: The metrics instance to complete.
        """
        metrics.complete()
        self.metrics_history.append(metrics)
        
        # Log slow operations
        if metrics.duration_ms > self.slow_threshold_ms:
            logger.warning(
                f"Slow operation detected: {metrics.operation} "
                f"took {metrics.duration_ms:.2f}ms"
            )
        elif self.enable_detailed_logging:
            logger.info(
                f"Completed operation: {metrics.operation} "
                f"in {metrics.duration_ms:.2f}ms"
            )
    
    def record_tool_call(self, tool_name: str):
        """Record a tool call.
        
        Args:
            tool_name: Name of the tool called.
        """
        if self._current_metrics:
            self._current_metrics.tool_calls += 1
            if self.enable_detailed_logging:
                logger.debug(f"Tool call: {tool_name}")
# noqa  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002VW05NGF3PT06NzYzNmRmYTk=
    
    def record_error(self, error: str):
        """Record an error.
        
        Args:
            error: Error message.
        """
        if self._current_metrics:
            self._current_metrics.errors += 1
            logger.error(f"Operation error: {error}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all tracked metrics.
        
        Returns:
            Dictionary with metrics summary.
        """
        if not self.metrics_history:
            return {"total_operations": 0}
        
        total_duration = sum(m.duration_ms for m in self.metrics_history)
        total_tool_calls = sum(m.tool_calls for m in self.metrics_history)
        total_errors = sum(m.errors for m in self.metrics_history)
        
        return {
            "total_operations": len(self.metrics_history),
            "total_duration_ms": total_duration,
            "avg_duration_ms": total_duration / len(self.metrics_history),
            "total_tool_calls": total_tool_calls,
            "total_errors": total_errors,
            "slow_operations": sum(
                1 for m in self.metrics_history 
                if m.duration_ms > self.slow_threshold_ms
            ),
        }
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process state through monitoring."""
        return state
# pragma: no cover  My80OmFIVnBZMlhtblk3a3ZiUG1yS002VW05NGF3PT06NzYzNmRmYTk=

