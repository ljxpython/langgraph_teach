"""Report Generator Sub-Agent for K6 Performance Testing.

This module provides the report generator sub-agent that specializes
in creating professional performance test reports with MCP chart integration.
"""
# pragma: no cover  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002YVc5VFF3PT06ZGE2N2MxMzE=

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    title: str = "K6 Performance Test Report"
    include_charts: bool = True
    include_raw_data: bool = False
    format: str = "html"  # html, pdf, json
    template: Optional[str] = None
    theme: str = "professional"  # professional, minimal, dark


class ReportGeneratorAgent:
    """Sub-agent specialized in professional report generation.

    This agent creates comprehensive performance reports with:
    - Executive summary with key metrics
    - Detailed metrics analysis tables
    - MCP-generated charts and visualizations
    - Performance insights and recommendations
    - Threshold compliance status

    Example:
        >>> from k6_agent.utils import MCPChartGenerator
        >>> chart_gen = MCPChartGenerator(llm=my_llm)
        >>> generator = ReportGeneratorAgent(chart_generator=chart_gen)
        >>> report_path = generator.generate_report(
        ...     result_path="./results/load_test.json",
        ...     output_path="./reports/load_test.html",
        ... )
    """

    def __init__(
        self,
        output_dir: Path = Path("./reports"),
        chart_generator: Optional[Any] = None,
        llm: Optional[Any] = None,
    ):
        """Initialize the report generator agent.

        Args:
            output_dir: Directory for generated reports.
            chart_generator: Optional MCPChartGenerator instance.
            llm: Optional LLM for chart generation if chart_generator not provided.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize chart generator
        if chart_generator:
            self.chart_generator = chart_generator
        elif llm:
            from k6_agent.utils import MCPChartGenerator
            self.chart_generator = MCPChartGenerator(llm=llm)
        else:
            self.chart_generator = None
    
    def generate_report(
        self,
        result_path: str,
        output_path: Optional[str] = None,
        config: Optional[ReportConfig] = None,
        analysis_result: Optional[Any] = None,
    ) -> Path:
        """Generate a performance test report.
        
        Args:
            result_path: Path to K6 JSON result file.
            output_path: Optional output path for report.
            config: Optional report configuration.
            analysis_result: Optional pre-computed analysis result.
            
        Returns:
            Path to the generated report.
        """
        config = config or ReportConfig()
        
        # Load result data
        with open(result_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Generate report based on format
        if config.format == "html":
            return self._generate_html_report(data, output_path, config, analysis_result)
        elif config.format == "json":
            return self._generate_json_report(data, output_path, config, analysis_result)
        else:
            raise ValueError(f"Unsupported format: {config.format}")
    
    def _generate_html_report(
        self,
        data: Dict[str, Any],
        output_path: Optional[str],
        config: ReportConfig,
        analysis_result: Optional[Any],
    ) -> Path:
        """Generate professional HTML report with charts."""
        metrics = data.get("metrics", {})
        thresholds = data.get("thresholds", {})

        # Extract key metrics
        http_req_duration = metrics.get("http_req_duration", {}).get("values", {})
        http_reqs = metrics.get("http_reqs", {}).get("values", {})
        http_req_failed = metrics.get("http_req_failed", {}).get("values", {})
        data_received = metrics.get("data_received", {}).get("values", {})
        data_sent = metrics.get("data_sent", {}).get("values", {})
# type: ignore  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002YVc5VFF3PT06ZGE2N2MxMzE=

        # Calculate derived metrics
        total_requests = int(http_reqs.get("count", 0))
        error_rate = http_req_failed.get("rate", 0) * 100
        success_rate = 100 - error_rate

        # Check threshold status
        failed_thresholds = [k for k, v in thresholds.items() if not v.get("ok", True)]
        test_passed = len(failed_thresholds) == 0 and error_rate < 5
        status_class = "passed" if test_passed else "failed"
        status_text = "✅ PASSED" if test_passed else "❌ FAILED"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.title}</title>
    <style>
        :root {{
            --primary: #667eea;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        header {{
            background: linear-gradient(135deg, var(--primary) 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }}
        header .container {{ display: flex; justify-content: space-between; align-items: center; }}
        h1 {{ font-size: 1.75rem; font-weight: 600; }}
        .timestamp {{ opacity: 0.9; font-size: 0.875rem; }}
        .status {{
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 1rem;
        }}
        .status.passed {{ background: var(--success); }}
        .status.failed {{ background: var(--error); }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
        .card {{
            background: var(--card-bg);
            border-radius: 0.75rem;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid var(--border);
        }}
        .card h3 {{ font-size: 0.875rem; color: var(--text-muted); margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        .card .value {{ font-size: 2rem; font-weight: 700; color: var(--primary); }}
        .card .unit {{ font-size: 0.875rem; color: var(--text-muted); }}
        .card.success .value {{ color: var(--success); }}
        .card.warning .value {{ color: var(--warning); }}
        .card.error .value {{ color: var(--error); }}
        section {{ margin-bottom: 2rem; }}
        section h2 {{ font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid var(--primary); }}
        table {{ width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 0.5rem; overflow: hidden; }}
        th, td {{ padding: 0.875rem 1rem; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ background: var(--bg); font-weight: 600; color: var(--text-muted); text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; }}
        tr:last-child td {{ border-bottom: none; }}
        tr:hover {{ background: var(--bg); }}
        .metric-label {{ font-weight: 500; }}
        .metric-value {{ font-family: 'SF Mono', 'Consolas', monospace; }}
        footer {{ text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.875rem; }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div>
                <h1>📊 {config.title}</h1>
                <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <span class="status {status_class}">{status_text}</span>
        </div>
    </header>

    <main class="container">
        <section>
            <h2>📈 Key Metrics</h2>
            <div class="grid">
                <div class="card">
                    <h3>Total Requests</h3>
                    <div class="value">{total_requests:,}</div>
                </div>
                <div class="card">
                    <h3>Throughput</h3>
                    <div class="value">{http_reqs.get('rate', 0):.2f}</div>
                    <div class="unit">requests/sec</div>
                </div>
                <div class="card {'success' if success_rate >= 99 else 'warning' if success_rate >= 95 else 'error'}">
                    <h3>Success Rate</h3>
                    <div class="value">{success_rate:.2f}%</div>
                </div>
                <div class="card {'success' if error_rate < 1 else 'warning' if error_rate < 5 else 'error'}">
                    <h3>Error Rate</h3>
                    <div class="value">{error_rate:.2f}%</div>
                </div>
            </div>
        </section>

        <section>
            <h2>⏱️ Response Time Analysis</h2>
            <div class="card">
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Value</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td class="metric-label">Average</td><td class="metric-value">{http_req_duration.get('avg', 0):.2f} ms</td><td>Mean response time</td></tr>
                        <tr><td class="metric-label">Median (P50)</td><td class="metric-value">{http_req_duration.get('med', 0):.2f} ms</td><td>50th percentile</td></tr>
                        <tr><td class="metric-label">P90</td><td class="metric-value">{http_req_duration.get('p(90)', 0):.2f} ms</td><td>90th percentile</td></tr>
                        <tr><td class="metric-label">P95</td><td class="metric-value">{http_req_duration.get('p(95)', 0):.2f} ms</td><td>95th percentile (SLA target)</td></tr>
                        <tr><td class="metric-label">P99</td><td class="metric-value">{http_req_duration.get('p(99)', 0):.2f} ms</td><td>99th percentile</td></tr>
                        <tr><td class="metric-label">Minimum</td><td class="metric-value">{http_req_duration.get('min', 0):.2f} ms</td><td>Fastest response</td></tr>
                        <tr><td class="metric-label">Maximum</td><td class="metric-value">{http_req_duration.get('max', 0):.2f} ms</td><td>Slowest response</td></tr>
                    </tbody>
                </table>
            </div>
        </section>

        <section>
            <h2>📦 Data Transfer</h2>
            <div class="grid">
                <div class="card">
                    <h3>Data Received</h3>
                    <div class="value">{data_received.get('count', 0) / 1024 / 1024:.2f}</div>
                    <div class="unit">MB total ({data_received.get('rate', 0) / 1024:.2f} KB/s)</div>
                </div>
                <div class="card">
                    <h3>Data Sent</h3>
                    <div class="value">{data_sent.get('count', 0) / 1024 / 1024:.2f}</div>
                    <div class="unit">MB total ({data_sent.get('rate', 0) / 1024:.2f} KB/s)</div>
                </div>
            </div>
        </section>

        {self._generate_threshold_section(thresholds)}
    </main>

    <footer>
        <p>Generated by K6 Agent - AI-Powered Performance Testing Platform</p>
    </footer>
</body>
</html>"""

        if output_path:
            path = Path(output_path)
        else:
            path = self.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")

        # Generate charts if chart generator available
        if config.include_charts and self.chart_generator:
            self._generate_charts_for_report(data, path.parent)

        return path

    def _generate_threshold_section(self, thresholds: Dict[str, Any]) -> str:
        """Generate thresholds section HTML."""
        if not thresholds:
            return ""
# noqa  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002YVc5VFF3PT06ZGE2N2MxMzE=

        rows = ""
        for name, result in thresholds.items():
            ok = result.get("ok", True)
            status = "✅" if ok else "❌"
            status_class = "success" if ok else "error"
            rows += f'<tr><td class="metric-label">{name}</td><td class="metric-value card {status_class}"><span class="value">{status}</span></td></tr>'

        return f"""
        <section>
            <h2>🎯 Threshold Compliance</h2>
            <div class="card">
                <table>
                    <thead>
                        <tr><th>Threshold</th><th>Status</th></tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </section>"""

    def _generate_charts_for_report(self, data: Dict[str, Any], output_dir: Path):
        """Generate charts for the report."""
        try:
            from k6_agent.utils import TestResult

            result = TestResult.from_k6_json(data, "Test Result")
            charts_dir = output_dir / "charts"
            self.chart_generator.generate_all_charts([result], charts_dir)
            logger.info(f"Charts generated in {charts_dir}")
        except Exception as e:
            logger.warning(f"Failed to generate charts: {e}")
    
    def _generate_json_report(
        self,
        data: Dict[str, Any],
        output_path: Optional[str],
        config: ReportConfig,
        analysis_result: Optional[Any],
    ) -> Path:
        """Generate JSON report."""
        report = {
            "title": config.title,
            "generated_at": datetime.now().isoformat(),
            "metrics": data.get("metrics", {}),
            "thresholds": data.get("thresholds", {}),
        }
        
        if output_path:
            path = Path(output_path)
        else:
            path = self.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
# pylint: disable  My80OmFIVnBZMlhtblk3a3ZiUG1yS002YVc5VFF3PT06ZGE2N2MxMzE=
        
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        
        return path

