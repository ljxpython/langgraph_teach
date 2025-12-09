"""MCP Chart Generator for K6 Performance Testing.

This module provides the main MCPChartGenerator class that uses
AntV MCP Chart Server for professional chart generation.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from k6_agent.utils.chart_generator import (
    ChartType, ChartSpec, TestResult, Colors, MCP_CHART_SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)


class MCPChartGenerator:
    """Professional chart generation using MCP Chart Server.
    
    This class provides intelligent chart generation for K6 performance
    test results using the AntV MCP Chart Server with LangChain integration.
    
    Example:
        >>> generator = MCPChartGenerator(llm=my_llm)
        >>> charts = generator.generate_all_charts(results, output_dir="./charts")
    """
    
    def __init__(
        self,
        llm=None,
        use_mcp_client: bool = True,
        render_images: bool = True,
        mcp_server_command: str = "npx",
        mcp_server_args: Optional[List[str]] = None,
    ):
        """Initialize the MCP chart generator.
        
        Args:
            llm: Language model for chart generation agent.
            use_mcp_client: Whether to use MCP client.
            render_images: Whether to render charts as images.
            mcp_server_command: Command to start MCP server.
            mcp_server_args: Arguments for MCP server.
        """
        self.llm = llm
        self.use_mcp_client = use_mcp_client
        self.render_images = render_images
        self.mcp_server_command = mcp_server_command
        self.mcp_server_args = mcp_server_args or ["-y", "@antv/mcp-server-chart"]
        
        self.agent = None
        self.mcp_tools = None
        self.renderer = None
        
        if self.use_mcp_client and self.llm:
            self._initialize_mcp_agent()
        
        if self.render_images:
            self._initialize_renderer()
    
    def _initialize_mcp_agent(self):
        """Initialize MCP chart generation agent."""
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
            from langchain.agents import create_agent
            
            mcp_client = MultiServerMCPClient({
                "mcp-server-chart": {
                    "command": self.mcp_server_command,
                    "args": self.mcp_server_args,
                    "transport": "stdio",
                }
            })
            
            self.mcp_tools = asyncio.run(mcp_client.get_tools())
# pylint: disable  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002TXpKTFZRPT06ZTJlNGI4MDQ=
            
            self.agent = create_agent(
                self.llm,
                tools=self.mcp_tools,
                system_prompt=MCP_CHART_SYSTEM_PROMPT,
                name="K6ChartAgent"
            )
            
            logger.info("MCP chart agent initialized successfully")
            
        except ImportError as e:
            logger.warning(f"MCP dependencies not available: {e}")
            self.use_mcp_client = False
        except Exception as e:
            logger.warning(f"Failed to initialize MCP agent: {e}")
            self.use_mcp_client = False
    
    def _initialize_renderer(self):
        """Initialize fallback image renderer."""
        try:
            from k6_agent.utils.image_renderer import ImageRenderer
            self.renderer = ImageRenderer(backend="matplotlib")
            logger.info("Image renderer initialized")
        except ImportError:
            logger.debug("Image renderer not available")
    
    def generate_response_time_chart(
        self,
        results: List[TestResult],
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate response time trend chart with percentiles.
        
        Args:
            results: List of test results.
            output_path: Optional path to save chart.
            
        Returns:
            Chart specification and generation result.
        """
        spec = ChartSpec(
            type=ChartType.LINE,
            title="Response Time Trend Analysis - Multi-Percentile View",
            description="Response time analysis showing avg, median, P95, P99",
            x_axis={
                "type": "category",
                "data": [r.test_name for r in results],
                "name": "Test Scenario",
                "axisLabel": {"rotate": 45, "interval": 0},
            },
            y_axis={
                "type": "value",
                "name": "Response Time (ms)",
                "axisLabel": {"formatter": "{value} ms"},
            },
            series=[
                {
                    "name": "Average (Mean)",
                    "data": [r.avg_response_time for r in results],
                    "type": "line",
                    "smooth": True,
                    "lineStyle": {"width": 2},
                    "itemStyle": {"color": Colors.PRIMARY},
                    "markPoint": {
                        "data": [{"type": "max", "name": "Max"}, {"type": "min", "name": "Min"}]
                    },
                },
                {
                    "name": "P50 (Median)",
                    "data": [r.p50_response_time for r in results],
                    "type": "line",
                    "smooth": True,
                    "lineStyle": {"width": 2, "type": "dashed"},
                    "itemStyle": {"color": Colors.SUCCESS},
                },
                {
                    "name": "P95",
                    "data": [r.p95_response_time for r in results],
                    "type": "line",
                    "smooth": True,
                    "lineStyle": {"width": 2},
                    "itemStyle": {"color": Colors.WARNING},
                },
                {
                    "name": "P99",
                    "data": [r.p99_response_time for r in results],
                    "type": "line",
                    "smooth": True,
                    "lineStyle": {"width": 2},
                    "itemStyle": {"color": Colors.ERROR},
                },
            ],
            tooltip={"trigger": "axis", "axisPointer": {"type": "cross"}},
            legend={
                "data": ["Average (Mean)", "P50 (Median)", "P95", "P99"],
                "top": "bottom",
            },
            grid={"left": "3%", "right": "4%", "bottom": "15%", "containLabel": True},
        )
# fmt: off  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002TXpKTFZRPT06ZTJlNGI4MDQ=
        
        return self._generate_chart(spec, output_path)

    def generate_throughput_chart(
        self,
        results: List[TestResult],
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate throughput analysis chart with data transfer metrics."""
        max_throughput = max([r.requests_per_second for r in results]) if results else 0

        spec = ChartSpec(
            type=ChartType.BAR,
            title="Throughput Performance Analysis",
            description="Requests per second and data transfer rates",
            x_axis={
                "type": "category",
                "data": [r.test_name for r in results],
                "name": "Test Scenario",
                "axisLabel": {"rotate": 45, "interval": 0},
            },
            y_axis=[
                {"type": "value", "name": "Requests/Second", "position": "left"},
                {"type": "value", "name": "Data Transfer (B/s)", "position": "right"},
            ],
            series=[
                {
                    "name": "Requests/Second",
                    "data": [r.requests_per_second for r in results],
                    "type": "bar",
                    "yAxisIndex": 0,
                    "itemStyle": {"color": Colors.PRIMARY},
                    "label": {"show": True, "position": "top", "formatter": "{c} req/s"},
                    "markLine": {
                        "data": [
                            {"type": "average", "name": "Avg"},
                            {"yAxis": max_throughput * 0.8, "name": "80% Target",
                             "lineStyle": {"type": "dashed", "color": Colors.SUCCESS}},
                        ]
                    },
                },
                {
                    "name": "Data Received/s",
                    "data": [r.data_received_per_second for r in results],
                    "type": "line",
                    "yAxisIndex": 1,
                    "smooth": True,
                    "itemStyle": {"color": Colors.SUCCESS},
                },
                {
                    "name": "Data Sent/s",
                    "data": [r.data_sent_per_second for r in results],
                    "type": "line",
                    "yAxisIndex": 1,
                    "smooth": True,
                    "itemStyle": {"color": Colors.WARNING},
                    "lineStyle": {"type": "dashed"},
                },
            ],
            tooltip={"trigger": "axis", "axisPointer": {"type": "shadow"}},
            legend={"data": ["Requests/Second", "Data Received/s", "Data Sent/s"], "top": "bottom"},
            grid={"left": "3%", "right": "4%", "bottom": "15%", "containLabel": True},
        )

        return self._generate_chart(spec, output_path)

    def generate_error_rate_chart(
        self,
        results: List[TestResult],
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate error rate analysis chart with severity coloring."""
        error_rates = [100 - r.success_rate for r in results]
        success_rates = [r.success_rate for r in results]

        # Color based on severity
        def get_color(error_rate: float) -> str:
            if error_rate == 0:
                return Colors.SUCCESS
            elif error_rate < 1:
                return Colors.WARNING
            elif error_rate < 5:
                return Colors.ERROR
            else:
                return Colors.CRITICAL

        spec = ChartSpec(
            type=ChartType.BAR,
            title="Error Rate Analysis",
            description="Success vs failure distribution with severity levels",
            x_axis={
                "type": "category",
                "data": [r.test_name for r in results],
                "name": "Test Scenario",
                "axisLabel": {"rotate": 45, "interval": 0},
            },
            y_axis={"type": "value", "name": "Rate (%)", "max": 100},
            series=[
                {
                    "name": "Error Rate",
                    "data": [
                        {"value": rate, "itemStyle": {"color": get_color(rate)}}
                        for rate in error_rates
                    ],
                    "type": "bar",
                    "label": {"show": True, "position": "top", "formatter": "{c}%"},
                    "markLine": {
                        "data": [
                            {"yAxis": 1, "name": "1% Warning",
                             "lineStyle": {"type": "dashed", "color": Colors.WARNING}},
                            {"yAxis": 5, "name": "5% Critical",
                             "lineStyle": {"type": "dashed", "color": Colors.ERROR}},
                        ]
                    },
                },
                {
                    "name": "Success Rate",
                    "data": success_rates,
                    "type": "line",
                    "smooth": True,
                    "itemStyle": {"color": Colors.SUCCESS},
                },
            ],
            tooltip={"trigger": "axis"},
            legend={"data": ["Error Rate", "Success Rate"], "top": "bottom"},
            grid={"left": "3%", "right": "4%", "bottom": "15%", "containLabel": True},
        )

        return self._generate_chart(spec, output_path)

    def generate_success_rate_pie(
        self,
        results: List[TestResult],
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate overall success rate pie chart."""
        total_requests = sum(r.total_requests for r in results)
        total_failed = sum(r.failed_requests for r in results)
        total_success = total_requests - total_failed

        success_pct = (total_success / total_requests * 100) if total_requests > 0 else 0

        spec = ChartSpec(
            type=ChartType.PIE,
            title=f"Overall Success Rate - {success_pct:.2f}%",
            description=f"Total: {total_requests:,} | Success: {total_success:,} | Failed: {total_failed:,}",
            series=[{
                "name": "Request Status",
                "type": "pie",
                "radius": ["40%", "70%"],
                "center": ["50%", "50%"],
                "avoidLabelOverlap": True,
                "itemStyle": {"borderRadius": 10},
                "data": [
                    {
                        "value": total_success,
                        "name": "Successful",
                        "itemStyle": {"color": Colors.SUCCESS, "borderColor": "#fff", "borderWidth": 2},
                    },
                    {
                        "value": total_failed,
                        "name": "Failed",
                        "itemStyle": {"color": Colors.ERROR, "borderColor": "#fff", "borderWidth": 2},
                    },
                ],
            }],
            tooltip={"trigger": "item", "formatter": "{b}<br/>Count: {c}<br/>Percentage: {d}%"},
            legend={"orient": "vertical", "left": "left"},
        )

        return self._generate_chart(spec, output_path)

    def generate_radar_chart(
        self,
        results: List[TestResult],
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate multi-dimensional performance comparison radar chart."""
        if not results:
            return {"status": "error", "message": "No results provided"}

        def normalize(value, max_val):
            return (value / max_val * 100) if max_val > 0 else 0

        def inverse_normalize(value, max_val):
            if max_val == 0:
                return 100
            return max(0, min(100, 100 - (value / max_val * 100)))

        max_throughput = max([r.requests_per_second for r in results])
        max_avg_rt = max([r.avg_response_time for r in results])
        max_p95_rt = max([r.p95_response_time for r in results])
        max_p99_rt = max([r.p99_response_time for r in results])

        spec = ChartSpec(
            type=ChartType.RADAR,
            title="Multi-Dimensional Performance Comparison",
            description="Comprehensive performance metrics comparison",
            extra={
                "radar": {
                    "indicator": [
                        {"name": "Throughput", "max": 100},
                        {"name": "Success Rate", "max": 100},
                        {"name": "Response Speed", "max": 100},
                        {"name": "Stability (P95)", "max": 100},
                        {"name": "Reliability (P99)", "max": 100},
                    ],
                    "shape": "polygon",
                    "splitNumber": 5,
                },
            },
            series=[{
                "name": "Performance Metrics",
                "type": "radar",
                "data": [
                    {
                        "value": [
                            normalize(r.requests_per_second, max_throughput),
                            r.success_rate,
                            inverse_normalize(r.avg_response_time, max_avg_rt),
                            inverse_normalize(r.p95_response_time, max_p95_rt),
                            inverse_normalize(r.p99_response_time, max_p99_rt),
                        ],
                        "name": r.test_name,
                    }
                    for r in results[:5]
                ],
            }],
            tooltip={"trigger": "item"},
            legend={"data": [r.test_name for r in results[:5]], "top": "bottom"},
        )

        return self._generate_chart(spec, output_path)

    def generate_boxplot_chart(
        self,
        results: List[TestResult],
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate response time distribution boxplot."""
        boxplot_data = []
        for r in results:
            boxplot_data.append([
                r.min_response_time,
                r.p50_response_time * 0.5,
                r.p50_response_time,
                (r.p50_response_time + r.p95_response_time) / 2,
                r.max_response_time,
            ])

        spec = ChartSpec(
            type=ChartType.BOXPLOT,
            title="Response Time Statistical Distribution",
            description="Distribution showing median, quartiles, and outliers",
            x_axis={
                "type": "category",
                "data": [r.test_name for r in results],
                "name": "Test Scenario",
                "axisLabel": {"rotate": 45, "interval": 0},
            },
            y_axis={
                "type": "value",
                "name": "Response Time (ms)",
            },
            series=[{
                "name": "Response Time Distribution",
                "type": "boxplot",
                "data": boxplot_data,
                "itemStyle": {"color": Colors.PRIMARY, "borderColor": "#4c51bf"},
            }],
            tooltip={"trigger": "item"},
            grid={"left": "3%", "right": "4%", "bottom": "15%", "containLabel": True},
        )

        return self._generate_chart(spec, output_path)

    def _generate_chart(
        self,
        spec: ChartSpec,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate chart using MCP agent or return specification.

        Args:
            spec: Chart specification.
            output_path: Optional path to save chart.

        Returns:
            Generated chart data or specification.
        """
        try:
            chart_dict = spec.to_dict()
            result = {
                "status": "success",
                "message": "Chart specification generated",
                "chart_spec": chart_dict,
            }
# noqa  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002TXpKTFZRPT06ZTJlNGI4MDQ=

            # Use MCP agent if available
            if self.agent and self.use_mcp_client:
                try:
                    prompt = f"""Generate a professional {spec.type.value} chart:
Title: {spec.title}
Description: {spec.description}
Specification: {json.dumps(chart_dict, indent=2)}

Use the appropriate MCP Chart Server tool (generate_{spec.type.value}_chart)."""

                    agent_result = self.agent.invoke({
                        "input": prompt,
                        "chart_spec": json.dumps(chart_dict),
                    })

                    if agent_result:
                        result["agent_generated"] = True
                        result["agent_result"] = agent_result
                        if isinstance(agent_result, dict) and "output" in agent_result:
                            result["chart_url"] = agent_result.get("output")
                        logger.info(f"Chart generated by agent: {spec.title}")

                except Exception as e:
                    logger.debug(f"Agent generation failed: {e}")
                    result["agent_error"] = str(e)

            # Save chart specification
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

                result["saved_path"] = str(output_path)
                logger.info(f"Chart saved: {output_path}")
# pylint: disable  My80OmFIVnBZMlhtblk3a3ZiUG1yS002TXpKTFZRPT06ZTJlNGI4MDQ=

                # Render as image if available
                if self.renderer:
                    try:
                        render_dir = output_path.parent / "rendered"
                        render_result = self.renderer.render_chart(
                            chart_dict, output_dir=render_dir, formats=["png", "html"]
                        )
                        if render_result.get("status") == "success":
                            result["rendered_files"] = render_result.get("files", {})
                    except Exception as e:
                        logger.debug(f"Image rendering failed: {e}")

            return result

        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            return {"status": "error", "message": str(e), "chart_spec": spec.to_dict()}

    def generate_all_charts(
        self,
        results: List[TestResult],
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Generate all performance charts.

        Args:
            results: List of test results.
            output_dir: Optional directory to save charts.

        Returns:
            Dictionary of all generated charts.
        """
        charts = {}

        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating chart suite for {len(results)} test result(s)")

        # Core charts
        charts["response_time"] = self.generate_response_time_chart(
            results, output_dir / "01_response_time.json" if output_dir else None
        )
        charts["throughput"] = self.generate_throughput_chart(
            results, output_dir / "02_throughput.json" if output_dir else None
        )
        charts["error_rate"] = self.generate_error_rate_chart(
            results, output_dir / "03_error_rate.json" if output_dir else None
        )
        charts["success_rate"] = self.generate_success_rate_pie(
            results, output_dir / "04_success_rate.json" if output_dir else None
        )

        # Advanced charts for multiple scenarios
        if len(results) > 1:
            charts["radar"] = self.generate_radar_chart(
                results, output_dir / "05_performance_radar.json" if output_dir else None
            )
            charts["boxplot"] = self.generate_boxplot_chart(
                results, output_dir / "06_response_boxplot.json" if output_dir else None
            )

        # Metadata
        import time
        charts["_metadata"] = {
            "total_charts": len([k for k in charts if not k.startswith("_")]),
            "test_scenarios": len(results),
            "chart_types": [k for k in charts if not k.startswith("_")],
            "generation_timestamp": time.time(),
        }

        logger.info(f"Generated {charts['_metadata']['total_charts']} charts")
        return charts

    def get_status(self) -> Dict[str, Any]:
        """Get chart generator status."""
        return {
            "mcp_enabled": self.use_mcp_client,
            "agent_initialized": self.agent is not None,
            "has_llm": self.llm is not None,
            "render_images": self.render_images,
            "renderer_initialized": self.renderer is not None,
            "available_chart_types": [t.value for t in ChartType],
        }
