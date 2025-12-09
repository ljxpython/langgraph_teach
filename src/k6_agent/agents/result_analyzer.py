"""Result Analyzer Sub-Agent for K6 Performance Testing.

This module provides the result analyzer sub-agent that specializes
in analyzing K6 test results and identifying performance issues.
"""
# pragma: no cover  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002VmpkdVNRPT06MWM0YjYxNmQ=

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceIssue:
    """Identified performance issue."""
    severity: str  # critical, warning, info
    category: str  # response_time, error_rate, throughput, etc.
    description: str
    metric: str
    value: float
    threshold: Optional[float] = None
    recommendation: Optional[str] = None


@dataclass
class AnalysisResult:
    """Result of performance analysis."""
    test_passed: bool
    summary: str
    issues: List[PerformanceIssue] = field(default_factory=list)
    metrics_summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class ResultAnalyzerAgent:
    """Sub-agent specialized in performance result analysis.
    
    This agent provides:
    - Metrics analysis and interpretation
    - Performance issue detection
    - Bottleneck identification
    - Actionable recommendations
    
    Example:
        >>> analyzer = ResultAnalyzerAgent()
        >>> result = analyzer.analyze_results("./results/load_test.json")
        >>> print(result.summary)
    """
    
    def __init__(
        self,
        knowledge_client: Optional[Any] = None,
        enable_knowledge_retrieval: bool = True,
    ):
        """Initialize the result analyzer agent.
        
        Args:
            knowledge_client: Optional knowledge base client.
            enable_knowledge_retrieval: Enable knowledge retrieval.
        """
        self.knowledge_client = knowledge_client
        self.enable_knowledge_retrieval = enable_knowledge_retrieval
        
        # Default thresholds for issue detection
        self.thresholds = {
            "response_time_p95_ms": 500,
            "response_time_p99_ms": 1000,
            "error_rate_percent": 1.0,
            "throughput_variance_percent": 20.0,
        }
    
    def analyze_results(self, result_path: str) -> AnalysisResult:
        """Analyze K6 test results.
        
        Args:
            result_path: Path to the K6 JSON result file.
            
        Returns:
            AnalysisResult with findings and recommendations.
        """
        path = Path(result_path)
        if not path.exists():
            return AnalysisResult(
                test_passed=False,
                summary=f"Result file not found: {result_path}",
            )
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return AnalysisResult(
                test_passed=False,
                summary=f"Invalid JSON in result file: {result_path}",
            )
# fmt: off  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002VmpkdVNRPT06MWM0YjYxNmQ=
        
        issues = []
        recommendations = []
        
        # Analyze metrics
        metrics = data.get("metrics", {})
        
        # Check response time
        http_req_duration = metrics.get("http_req_duration", {}).get("values", {})
        p95 = http_req_duration.get("p(95)", 0)
        p99 = http_req_duration.get("p(99)", 0)
        
        if p95 > self.thresholds["response_time_p95_ms"]:
            issues.append(PerformanceIssue(
                severity="warning",
                category="response_time",
                description=f"P95 response time ({p95:.2f}ms) exceeds threshold",
                metric="http_req_duration.p95",
                value=p95,
                threshold=self.thresholds["response_time_p95_ms"],
                recommendation="Consider optimizing slow endpoints or increasing server resources",
            ))
        
        if p99 > self.thresholds["response_time_p99_ms"]:
            issues.append(PerformanceIssue(
                severity="critical",
                category="response_time",
                description=f"P99 response time ({p99:.2f}ms) exceeds threshold",
                metric="http_req_duration.p99",
                value=p99,
                threshold=self.thresholds["response_time_p99_ms"],
                recommendation="Investigate outlier requests and potential bottlenecks",
            ))
        
        # Check error rate
        http_req_failed = metrics.get("http_req_failed", {}).get("values", {})
        error_rate = http_req_failed.get("rate", 0) * 100
        
        if error_rate > self.thresholds["error_rate_percent"]:
            issues.append(PerformanceIssue(
                severity="critical",
                category="error_rate",
                description=f"Error rate ({error_rate:.2f}%) exceeds threshold",
                metric="http_req_failed.rate",
                value=error_rate,
                threshold=self.thresholds["error_rate_percent"],
                recommendation="Investigate error responses and server logs",
            ))
# noqa  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002VmpkdVNRPT06MWM0YjYxNmQ=
        
        # Check thresholds
        thresholds = data.get("thresholds", {})
        failed_thresholds = [
            name for name, t in thresholds.items() 
            if not t.get("ok", True)
        ]
        
        test_passed = len(failed_thresholds) == 0 and not any(
            i.severity == "critical" for i in issues
        )
# noqa  My80OmFIVnBZMlhtblk3a3ZiUG1yS002VmpkdVNRPT06MWM0YjYxNmQ=
        
        # Generate summary
        summary = self._generate_summary(data, issues, test_passed)
        
        # Generate recommendations
        for issue in issues:
            if issue.recommendation:
                recommendations.append(issue.recommendation)
        
        return AnalysisResult(
            test_passed=test_passed,
            summary=summary,
            issues=issues,
            metrics_summary={
                "response_time_p95": p95,
                "response_time_p99": p99,
                "error_rate": error_rate,
            },
            recommendations=recommendations,
        )
    
    def _generate_summary(
        self,
        data: Dict[str, Any],
        issues: List[PerformanceIssue],
        passed: bool,
    ) -> str:
        """Generate analysis summary."""
        status = "✅ PASSED" if passed else "❌ FAILED"
        critical = sum(1 for i in issues if i.severity == "critical")
        warnings = sum(1 for i in issues if i.severity == "warning")
        
        return f"""Test Status: {status}
Issues Found: {len(issues)} ({critical} critical, {warnings} warnings)
"""

