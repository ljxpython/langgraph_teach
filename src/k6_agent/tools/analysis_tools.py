"""K6 result analysis tools.

This module provides tools for parsing and analyzing K6 test results,
including metrics extraction, statistical analysis, and bottleneck detection.
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from statistics import mean, median, stdev

from langchain_core.tools import tool
from pydantic import BaseModel, Field


@dataclass
class MetricSummary:
    """Summary statistics for a metric."""
    name: str
    count: int = 0
    min_value: float = 0.0
    max_value: float = 0.0
    avg_value: float = 0.0
    med_value: float = 0.0
    p90_value: float = 0.0
    p95_value: float = 0.0
    p99_value: float = 0.0
    std_dev: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "count": self.count,
            "min": self.min_value,
            "max": self.max_value,
            "avg": self.avg_value,
            "med": self.med_value,
            "p90": self.p90_value,
            "p95": self.p95_value,
            "p99": self.p99_value,
            "std_dev": self.std_dev,
        }


@dataclass
class TestResult:
    """Parsed K6 test result."""
    test_name: str
    start_time: str
    end_time: str
    duration_seconds: float
    vus_max: int
    iterations_total: int
    iterations_per_second: float
    http_reqs_total: int
    http_reqs_per_second: float
    http_req_duration: MetricSummary
    http_req_failed_rate: float
    data_received_bytes: int
    data_sent_bytes: int
    checks_passed: int
    checks_failed: int
    thresholds_passed: List[str] = field(default_factory=list)
    thresholds_failed: List[str] = field(default_factory=list)
    custom_metrics: Dict[str, MetricSummary] = field(default_factory=dict)
# type: ignore  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002ZG05SVVRPT06YWFkY2VhMGE=
    
    @property
    def passed(self) -> bool:
        """Check if test passed all thresholds."""
        return len(self.thresholds_failed) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "vus_max": self.vus_max,
            "iterations": {
                "total": self.iterations_total,
                "per_second": self.iterations_per_second,
            },
            "http_requests": {
                "total": self.http_reqs_total,
                "per_second": self.http_reqs_per_second,
                "duration": self.http_req_duration.to_dict(),
                "failed_rate": self.http_req_failed_rate,
            },
            "data": {
                "received_bytes": self.data_received_bytes,
                "sent_bytes": self.data_sent_bytes,
            },
            "checks": {
                "passed": self.checks_passed,
                "failed": self.checks_failed,
            },
            "thresholds": {
                "passed": self.thresholds_passed,
                "failed": self.thresholds_failed,
            },
            "passed": self.passed,
        }


class ResultParserInput(BaseModel):
    """Input schema for result parsing."""
    result_path: str = Field(description="Path to K6 JSON result file")

# fmt: off  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002ZG05SVVRPT06YWFkY2VhMGE=

class MetricsAnalyzerInput(BaseModel):
    """Input schema for metrics analysis."""
    result_path: str = Field(description="Path to K6 JSON result file")
    focus_metrics: Optional[List[str]] = Field(
        default=None,
        description="Specific metrics to analyze"
    )


def parse_k6_summary(summary_data: Dict[str, Any]) -> TestResult:
    """Parse K6 summary JSON into TestResult."""
    metrics = summary_data.get("metrics", {})
    
    # Parse http_req_duration
    duration_data = metrics.get("http_req_duration", {}).get("values", {})
    http_req_duration = MetricSummary(
        name="http_req_duration",
        count=int(duration_data.get("count", 0)),
        min_value=duration_data.get("min", 0),
        max_value=duration_data.get("max", 0),
        avg_value=duration_data.get("avg", 0),
        med_value=duration_data.get("med", 0),
        p90_value=duration_data.get("p(90)", 0),
        p95_value=duration_data.get("p(95)", 0),
        p99_value=duration_data.get("p(99)", 0),
    )
    
    # Parse other metrics
    iterations = metrics.get("iterations", {}).get("values", {})
    http_reqs = metrics.get("http_reqs", {}).get("values", {})
    http_req_failed = metrics.get("http_req_failed", {}).get("values", {})
    data_received = metrics.get("data_received", {}).get("values", {})
    data_sent = metrics.get("data_sent", {}).get("values", {})
    checks = metrics.get("checks", {}).get("values", {})
    vus_max = metrics.get("vus_max", {}).get("values", {})
    
    # Parse thresholds
    thresholds_passed = []
    thresholds_failed = []
    for name, threshold in summary_data.get("thresholds", {}).items():
        if threshold.get("ok", True):
            thresholds_passed.append(name)
        else:
            thresholds_failed.append(name)
    
    return TestResult(
        test_name=summary_data.get("test_name", "unknown"),
        start_time=summary_data.get("start_time", ""),
        end_time=summary_data.get("end_time", ""),
        duration_seconds=summary_data.get("duration", 0),
        vus_max=int(vus_max.get("max", 0)),
        iterations_total=int(iterations.get("count", 0)),
        iterations_per_second=iterations.get("rate", 0),
        http_reqs_total=int(http_reqs.get("count", 0)),
        http_reqs_per_second=http_reqs.get("rate", 0),
        http_req_duration=http_req_duration,
        http_req_failed_rate=http_req_failed.get("rate", 0),
        data_received_bytes=int(data_received.get("count", 0)),
        data_sent_bytes=int(data_sent.get("count", 0)),
        checks_passed=int(checks.get("passes", 0)),
        checks_failed=int(checks.get("fails", 0)),
        thresholds_passed=thresholds_passed,
        thresholds_failed=thresholds_failed,
    )


def create_result_parser_tool():
    """Create a K6 result parser tool."""

    @tool(args_schema=ResultParserInput)
    def parse_k6_results(result_path: str) -> str:
        """Parse K6 test results from JSON file.

        Extracts key metrics and provides a structured summary of the test results.

        Args:
            result_path: Path to the K6 JSON result file.

        Returns:
            Formatted summary of test results.
        """
        try:
            path = Path(result_path)
            if not path.exists():
                return f"❌ Result file not found: {result_path}"

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            result = parse_k6_summary(data)

            status = "✅ PASSED" if result.passed else "❌ FAILED"

            return f"""# K6 Test Results Summary

**Status:** {status}
**Duration:** {result.duration_seconds:.1f}s
**Max VUs:** {result.vus_max}

## Performance Metrics

| Metric | Value |
|--------|-------|
| Total Requests | {result.http_reqs_total:,} |
| Requests/sec | {result.http_reqs_per_second:.2f} |
| Avg Response Time | {result.http_req_duration.avg_value:.2f}ms |
| P95 Response Time | {result.http_req_duration.p95_value:.2f}ms |
| P99 Response Time | {result.http_req_duration.p99_value:.2f}ms |
| Error Rate | {result.http_req_failed_rate * 100:.2f}% |

## Checks
- Passed: {result.checks_passed}
- Failed: {result.checks_failed}

## Thresholds
- Passed: {len(result.thresholds_passed)}
- Failed: {len(result.thresholds_failed)}

{f"**Failed Thresholds:** {', '.join(result.thresholds_failed)}" if result.thresholds_failed else ""}
"""
        except json.JSONDecodeError:
            return f"❌ Invalid JSON in result file: {result_path}"
        except Exception as e:
            return f"❌ Error parsing results: {str(e)}"

    return parse_k6_results


def create_metrics_analyzer_tool():
    """Create a metrics analysis tool."""

    @tool(args_schema=MetricsAnalyzerInput)
    def analyze_k6_metrics(
        result_path: str,
        focus_metrics: Optional[List[str]] = None,
    ) -> str:
        """Analyze K6 test metrics in detail.

        Provides detailed statistical analysis of test metrics,
        identifies patterns, and suggests potential issues.

        Args:
            result_path: Path to the K6 JSON result file.
            focus_metrics: Optional list of specific metrics to analyze.

        Returns:
            Detailed metrics analysis with insights.
        """
        try:
            path = Path(result_path)
            if not path.exists():
                return f"❌ Result file not found: {result_path}"
# pragma: no cover  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002ZG05SVVRPT06YWFkY2VhMGE=

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            metrics = data.get("metrics", {})
            analysis_parts = ["# Detailed Metrics Analysis\n"]

            # Analyze each metric
            for metric_name, metric_data in metrics.items():
                if focus_metrics and metric_name not in focus_metrics:
                    continue

                values = metric_data.get("values", {})
                metric_type = metric_data.get("type", "unknown")

                analysis_parts.append(f"## {metric_name} ({metric_type})\n")

                if metric_type == "trend":
                    analysis_parts.append(f"""
| Statistic | Value |
|-----------|-------|
| Min | {values.get('min', 0):.2f} |
| Max | {values.get('max', 0):.2f} |
| Avg | {values.get('avg', 0):.2f} |
| Med | {values.get('med', 0):.2f} |
| P90 | {values.get('p(90)', 0):.2f} |
| P95 | {values.get('p(95)', 0):.2f} |
| P99 | {values.get('p(99)', 0):.2f} |
""")
                    # Analyze variance
                    p95 = values.get('p(95)', 0)
                    avg = values.get('avg', 0)
                    if avg > 0 and p95 / avg > 2:
                        analysis_parts.append(
                            "⚠️ **High variance detected:** P95 is more than 2x the average.\n"
                        )

                elif metric_type == "rate":
                    rate = values.get('rate', 0)
                    analysis_parts.append(f"- Rate: {rate * 100:.2f}%\n")
                    if rate > 0.01:
                        analysis_parts.append(
                            f"⚠️ **Elevated rate:** {rate * 100:.2f}% exceeds 1% threshold.\n"
                        )

                elif metric_type == "counter":
                    count = values.get('count', 0)
                    rate = values.get('rate', 0)
                    analysis_parts.append(f"- Count: {count:,}\n")
                    analysis_parts.append(f"- Rate: {rate:.2f}/s\n")

            return "\n".join(analysis_parts)

        except Exception as e:
            return f"❌ Error analyzing metrics: {str(e)}"
# pragma: no cover  My80OmFIVnBZMlhtblk3a3ZiUG1yS002ZG05SVVRPT06YWFkY2VhMGE=

    return analyze_k6_metrics

