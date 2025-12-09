"""MCP Chart Generation for K6 Performance Testing.

This module provides professional chart generation using MCP Chart Server
(AntV) with intelligent agent capabilities for K6 performance test reports.
"""
# noqa  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002VjBwUWR3PT06NTdkMmUwODg=

import asyncio
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

logger = logging.getLogger(__name__)


class ChartType(str, Enum):
    """Supported chart types for performance visualization."""
    LINE = "line"
    AREA = "area"
    BAR = "bar"
    COLUMN = "column"
    PIE = "pie"
    DUAL_AXES = "dual_axes"
    HISTOGRAM = "histogram"
    BOXPLOT = "boxplot"
    SCATTER = "scatter"
    VIOLIN = "violin"
    RADAR = "radar"
    FUNNEL = "funnel"
    SANKEY = "sankey"
    TREEMAP = "treemap"
    WORD_CLOUD = "word_cloud"
# pragma: no cover  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002VjBwUWR3PT06NTdkMmUwODg=


# Performance color scheme
class Colors:
    """Color constants for performance charts."""
    PRIMARY = "#667eea"      # Blue - neutral metrics
    SUCCESS = "#10b981"      # Green - success/good performance
    WARNING = "#f59e0b"      # Yellow/Orange - warnings/thresholds
    ERROR = "#ef4444"        # Red - errors/poor performance
    CRITICAL = "#991b1b"     # Dark Red - critical issues
    SECONDARY = "#8b5cf6"    # Purple - secondary metrics
    INFO = "#06b6d4"         # Cyan - informational


@dataclass
class TestResult:
    """K6 test result data for chart generation."""
    test_name: str
    avg_response_time: float = 0.0
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    p50_response_time: float = 0.0
    p90_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    requests_per_second: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0
    success_rate: float = 100.0
    data_received_per_second: float = 0.0
    data_sent_per_second: float = 0.0
    vus: int = 0
    duration: str = ""
    
    @classmethod
    def from_k6_json(cls, data: Dict[str, Any], test_name: str = "Test") -> "TestResult":
        """Create TestResult from K6 JSON output."""
        metrics = data.get("metrics", {})
        
        http_req_duration = metrics.get("http_req_duration", {}).get("values", {})
        http_reqs = metrics.get("http_reqs", {}).get("values", {})
        http_req_failed = metrics.get("http_req_failed", {}).get("values", {})
        data_received = metrics.get("data_received", {}).get("values", {})
        data_sent = metrics.get("data_sent", {}).get("values", {})
        
        total_requests = int(http_reqs.get("count", 0))
        failed_rate = http_req_failed.get("rate", 0)
        failed_requests = int(total_requests * failed_rate)
        
        return cls(
            test_name=test_name,
            avg_response_time=http_req_duration.get("avg", 0),
            min_response_time=http_req_duration.get("min", 0),
            max_response_time=http_req_duration.get("max", 0),
            p50_response_time=http_req_duration.get("med", 0),
            p90_response_time=http_req_duration.get("p(90)", 0),
            p95_response_time=http_req_duration.get("p(95)", 0),
            p99_response_time=http_req_duration.get("p(99)", 0),
            requests_per_second=http_reqs.get("rate", 0),
            total_requests=total_requests,
            failed_requests=failed_requests,
            success_rate=(1 - failed_rate) * 100,
            data_received_per_second=data_received.get("rate", 0),
            data_sent_per_second=data_sent.get("rate", 0),
        )

# pragma: no cover  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002VjBwUWR3PT06NTdkMmUwODg=

@dataclass
class ChartSpec:
    """Chart specification for generation."""
    type: ChartType
    title: str
    description: str = ""
    x_axis: Optional[Dict[str, Any]] = None
    y_axis: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    series: List[Dict[str, Any]] = field(default_factory=list)
    tooltip: Optional[Dict[str, Any]] = None
    legend: Optional[Dict[str, Any]] = None
    grid: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = field(default_factory=dict)
# pragma: no cover  My80OmFIVnBZMlhtblk3a3ZiUG1yS002VjBwUWR3PT06NTdkMmUwODg=
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP/ECharts."""
        spec = {
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "series": self.series,
        }
        if self.x_axis:
            spec["xAxis"] = self.x_axis
        if self.y_axis:
            spec["yAxis"] = self.y_axis
        if self.tooltip:
            spec["tooltip"] = self.tooltip
        if self.legend:
            spec["legend"] = self.legend
        if self.grid:
            spec["grid"] = self.grid
        spec.update(self.extra)
        return spec


# MCP Chart Server System Prompt
MCP_CHART_SYSTEM_PROMPT = """You are an expert performance testing visualization agent specialized in creating comprehensive,
professional, and insightful charts for performance test reports using AntV MCP Chart Server.

## Your Core Responsibilities:

1. **Generate Professional Performance Charts**: Create high-quality, publication-ready charts that clearly
   communicate performance metrics and trends.

2. **Deep Performance Data Analysis**: Understand and interpret performance testing metrics including:
   - Response time distributions (avg, min, max, p50, p95, p99)
   - Throughput metrics (requests/second, data transfer rates)
   - Error rates and success rates
   - Virtual user (VU) load patterns
   - Time-series performance trends

3. **Intelligent Chart Type Selection**: Choose the most effective visualization for each metric:
   - **Line Charts**: Response time trends, throughput over time, VU ramp patterns
   - **Area Charts**: Cumulative metrics, stacked performance indicators
   - **Bar/Column Charts**: Comparative analysis across test scenarios, error rate comparisons
   - **Dual-Axis Charts**: Correlating different metrics (e.g., throughput vs response time)
   - **Pie Charts**: Success/failure distributions, request type breakdowns
   - **Histogram Charts**: Response time distributions, latency buckets
   - **Boxplot Charts**: Statistical distribution of response times, outlier detection
   - **Scatter Charts**: Correlation analysis (e.g., load vs response time)
   - **Radar Charts**: Multi-dimensional performance comparison

## Chart Design Best Practices:

### Visual Excellence:
- Use clear, descriptive titles that explain what the chart shows
- Label all axes with units (ms, req/s, %, etc.)
- Include comprehensive legends for multi-series charts
- Add interactive tooltips with detailed metric information
- Use color schemes that are accessible and meaningful:
  * Green (#10b981) for success/good performance
  * Red (#ef4444) for errors/poor performance
  * Blue (#667eea) for neutral metrics
  * Yellow/Orange (#f59e0b) for warnings/thresholds

### Performance-Specific Insights:
- Highlight threshold violations
- Mark performance degradation points
- Show percentile lines (P95, P99) for SLA compliance
- Indicate load test phases (ramp-up, steady-state, ramp-down)

## Available AntV Chart Types:
- generate_line_chart: Trends over time
- generate_area_chart: Cumulative trends
- generate_bar_chart / generate_column_chart: Categorical comparisons
- generate_dual_axes_chart: Multi-metric correlation
- generate_pie_chart: Proportional distributions
- generate_histogram_chart: Frequency distributions
- generate_boxplot_chart: Statistical distributions
- generate_scatter_chart: Correlation analysis
- generate_radar_chart: Multi-dimensional comparisons

Always prioritize clarity, accuracy, and actionable insights in your visualizations."""

