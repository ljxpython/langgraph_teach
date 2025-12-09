"""Report and Chart Generation Tools for K6 Performance Testing.

This module provides tools for generating professional performance reports
and charts using MCPChartGenerator and ReportGeneratorAgent.
"""
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件

import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def _get_workspace_root() -> str:
    """Get the K6 workspace root directory."""
    workspace_dir = os.getenv("K6_WORKSPACE_DIR", "./k6_workspace")
    workspace_path = Path(workspace_dir)
    if not workspace_path.is_absolute():
        workspace_path = Path(os.getcwd()) / workspace_path
    return str(workspace_path.resolve())


def _resolve_virtual_path(virtual_path: str) -> str:
    """Resolve a virtual path to an actual filesystem path."""
    if os.path.isabs(virtual_path) and not virtual_path.startswith('/'):
        return virtual_path
    workspace_root = _get_workspace_root()
    rel_path = virtual_path.lstrip('/')
    rel_path = rel_path.replace('/', os.sep)
    return os.path.join(workspace_root, rel_path)


class ChartGenerationInput(BaseModel):
    """Input schema for chart generation."""
    result_path: str = Field(
        description="Path to K6 JSON result file (virtual path like /k6_results/test.json)"
    )
    output_dir: str = Field(
        default="/k6_reports/charts",
        description="Output directory for charts (virtual path)"
    )
    test_name: str = Field(
        default="Performance Test",
        description="Name of the test for chart titles"
    )
    chart_types: Optional[List[str]] = Field(
        default=None,
        description="Specific chart types to generate (response_time, throughput, error_rate, success_rate, radar, boxplot). If None, generates all."
    )


class ReportGenerationInput(BaseModel):
    """Input schema for report generation."""
    result_path: str = Field(
        description="Path to K6 JSON result file (virtual path like /k6_results/test.json)"
    )
    output_path: str = Field(
        default="/k6_reports/report.html",
        description="Output path for HTML report (virtual path)"
    )
    title: str = Field(
        default="K6 Performance Test Report",
        description="Report title"
    )
    include_charts: bool = Field(
        default=True,
        description="Whether to include charts in the report"
    )
# noqa  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002VGxkeFpRPT06NDA0N2QzNmY=


def create_chart_generation_tool(llm=None):
    """Create a chart generation tool using MCPChartGenerator.
    
    Args:
        llm: Optional LLM for MCP agent chart generation.
    """
    
    @tool(args_schema=ChartGenerationInput)
    def generate_performance_charts(
        result_path: str,
        output_dir: str = "/k6_reports/charts",
        test_name: str = "Performance Test",
        chart_types: Optional[List[str]] = None,
    ) -> str:
        """Generate professional performance charts from K6 test results.
        
        Creates visualizations including:
        - Response time trend with percentiles (P50, P95, P99)
        - Throughput analysis (requests/second)
        - Error rate analysis with severity coloring
        - Success rate pie chart
        - Multi-dimensional radar chart
        - Response time boxplot distribution
        
        Args:
            result_path: Virtual path to K6 JSON result file.
            output_dir: Virtual path for output charts directory.
            test_name: Name for chart titles.
            chart_types: Specific charts to generate, or None for all.
            
        Returns:
            Summary of generated charts with paths.
        """
        try:
            from k6_agent.utils import MCPChartGenerator, TestResult
            
            # Resolve paths
            actual_result_path = _resolve_virtual_path(result_path)
            actual_output_dir = _resolve_virtual_path(output_dir)
            
            # Check result file exists
            if not os.path.exists(actual_result_path):
                return f"""❌ Result file not found: {result_path}
Resolved to: {actual_result_path}

Make sure the K6 test has been run and results saved."""
            
            # Load K6 results
            with open(actual_result_path, 'r', encoding='utf-8') as f:
                k6_data = json.load(f)
            
            # Parse test result
            result = TestResult.from_k6_json(k6_data, test_name)
            
            # Create output directory
            os.makedirs(actual_output_dir, exist_ok=True)
            
            # Initialize chart generator
            chart_gen = MCPChartGenerator(llm=llm, use_mcp_client=bool(llm))
            
            # Generate charts
            output_path = Path(actual_output_dir)
            charts = {}
            
            if chart_types is None or "response_time" in chart_types:
                charts["response_time"] = chart_gen.generate_response_time_chart(
                    [result], output_path / "response_time.json"
                )
            if chart_types is None or "throughput" in chart_types:
                charts["throughput"] = chart_gen.generate_throughput_chart(
                    [result], output_path / "throughput.json"
                )
            if chart_types is None or "error_rate" in chart_types:
                charts["error_rate"] = chart_gen.generate_error_rate_chart(
                    [result], output_path / "error_rate.json"
                )
            if chart_types is None or "success_rate" in chart_types:
                charts["success_rate"] = chart_gen.generate_success_rate_pie(
                    [result], output_path / "success_rate.json"
                )
# pragma: no cover  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002VGxkeFpRPT06NDA0N2QzNmY=
            
            # Build summary
            chart_files = [f"{output_dir}/{name}.json" for name in charts.keys()]
            
            return f"""✅ Charts generated successfully!

**Test:** {test_name}
**Source:** {result_path}
**Output Directory:** {output_dir}

**Generated Charts ({len(charts)}):**
{chr(10).join(f'  - {name}: {charts[name].get("status", "unknown")}' for name in charts)}

**Chart Files:**
{chr(10).join(f'  - {f}' for f in chart_files)}

**Key Metrics:**
  - Avg Response Time: {result.avg_response_time:.2f}ms
  - P95 Response Time: {result.p95_response_time:.2f}ms
  - Throughput: {result.requests_per_second:.2f} req/s
  - Success Rate: {result.success_rate:.2f}%
"""
            
        except Exception as e:
            logger.error(f"Chart generation error: {e}")
            return f"❌ Chart generation failed: {str(e)}"

    return generate_performance_charts


def create_report_generation_tool(llm=None):
    """Create a report generation tool using ReportGeneratorAgent.

    Args:
        llm: Optional LLM for MCP chart generation in reports.
    """

    @tool(args_schema=ReportGenerationInput)
    def generate_performance_report(
        result_path: str,
        output_path: str = "/k6_reports/report.html",
        title: str = "K6 Performance Test Report",
        include_charts: bool = True,
    ) -> str:
        """Generate a comprehensive HTML performance report from K6 test results.

        Creates a professional report including:
        - Executive summary with key metrics
        - Detailed metrics tables
        - Performance charts (if enabled)
        - Threshold compliance status
        - Recommendations based on results

        Args:
            result_path: Virtual path to K6 JSON result file.
            output_path: Virtual path for output HTML report.
            title: Report title.
            include_charts: Whether to include charts.

        Returns:
            Path to generated report and summary.
        """
        try:
            from k6_agent.agents.report_generator import ReportGeneratorAgent
            from k6_agent.utils import MCPChartGenerator
# fmt: off  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002VGxkeFpRPT06NDA0N2QzNmY=

            # Resolve paths
            actual_result_path = _resolve_virtual_path(result_path)
            actual_output_path = _resolve_virtual_path(output_path)

            # Check result file exists
            if not os.path.exists(actual_result_path):
                return f"""❌ Result file not found: {result_path}
Resolved to: {actual_result_path}

Make sure the K6 test has been run and results saved."""

            # Create output directory
            output_dir = Path(actual_output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # Initialize chart generator if charts are requested
            chart_gen = None
            if include_charts and llm:
                chart_gen = MCPChartGenerator(llm=llm, use_mcp_client=True)
            elif include_charts:
                chart_gen = MCPChartGenerator(use_mcp_client=False)

            # Initialize report generator
            report_gen = ReportGeneratorAgent(
                output_dir=output_dir,
                chart_generator=chart_gen,
            )

            # Create report config with title
            from k6_agent.agents.report_generator import ReportConfig
            report_config = ReportConfig(title=title)

            # Generate report
            report_path = report_gen.generate_report(
                result_path=actual_result_path,
                output_path=actual_output_path,
                config=report_config,
            )

            # Get virtual output path for display
            workspace_root = _get_workspace_root()
            virtual_output = output_path
            if report_path:
                rel_path = os.path.relpath(report_path, workspace_root)
                virtual_output = "/" + rel_path.replace(os.sep, "/")

            return f"""✅ Performance report generated successfully!

**Title:** {title}
**Source Data:** {result_path}
**Report Path:** {virtual_output}
**Charts Included:** {"Yes" if include_charts else "No"}

The report includes:
- Executive summary with key performance indicators
- Detailed metrics tables (response times, throughput, errors)
- {"Performance charts and visualizations" if include_charts else "No charts (disabled)"}
- Threshold compliance analysis
- Performance recommendations

Open the HTML file in a browser to view the full report.
"""

        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return f"❌ Report generation failed: {str(e)}"

    return generate_performance_report


def create_quick_summary_tool():
    """Create a quick summary tool for K6 results."""

    class QuickSummaryInput(BaseModel):
        """Input schema for quick summary."""
        result_path: str = Field(
            description="Path to K6 JSON result file (virtual path)"
        )

    @tool(args_schema=QuickSummaryInput)
    def get_test_summary(result_path: str) -> str:
        """Get a quick summary of K6 test results without generating full reports.

        Provides key metrics at a glance:
        - Response time statistics
        - Throughput metrics
        - Error rates
        - Pass/fail status

        Args:
            result_path: Virtual path to K6 JSON result file.

        Returns:
            Quick summary of test results.
        """
        try:
            from k6_agent.utils import TestResult

            actual_path = _resolve_virtual_path(result_path)
# type: ignore  My80OmFIVnBZMlhtblk3a3ZiUG1yS002VGxkeFpRPT06NDA0N2QzNmY=

            if not os.path.exists(actual_path):
                return f"❌ Result file not found: {result_path}"

            with open(actual_path, 'r', encoding='utf-8') as f:
                k6_data = json.load(f)

            result = TestResult.from_k6_json(k6_data, "Test")

            # Determine status
            status = "✅ PASSED" if result.success_rate >= 99 else "⚠️ WARNING" if result.success_rate >= 95 else "❌ FAILED"

            return f"""📊 **Quick Test Summary**

**Status:** {status}

**Response Times:**
  - Average: {result.avg_response_time:.2f}ms
  - P50 (Median): {result.p50_response_time:.2f}ms
  - P95: {result.p95_response_time:.2f}ms
  - P99: {result.p99_response_time:.2f}ms
  - Min: {result.min_response_time:.2f}ms
  - Max: {result.max_response_time:.2f}ms

**Throughput:**
  - Requests/Second: {result.requests_per_second:.2f}
  - Data Received: {result.data_received_per_second:.2f} B/s
  - Data Sent: {result.data_sent_per_second:.2f} B/s

**Reliability:**
  - Total Requests: {result.total_requests:,}
  - Failed Requests: {result.failed_requests:,}
  - Success Rate: {result.success_rate:.2f}%
  - Error Rate: {100 - result.success_rate:.2f}%
"""
        except Exception as e:
            return f"❌ Failed to parse results: {str(e)}"

    return get_test_summary

