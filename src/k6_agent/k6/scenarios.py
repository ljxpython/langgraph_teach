"""K6 scenarios and executors for performance testing.

This module provides data classes and utilities for defining K6 test scenarios
with modern executors, following K6 v0.27+ best practices.

Executor Types:
- shared-iterations: Fixed iterations shared among VUs
- per-vu-iterations: Fixed iterations per VU
- constant-vus: Constant number of VUs for a duration
- ramping-vus: Variable VUs with stages
- constant-arrival-rate: Constant iteration rate
- ramping-arrival-rate: Variable iteration rate with stages
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Union


class ExecutorType(str, Enum):
    """K6 executor types."""
    SHARED_ITERATIONS = "shared-iterations"
    PER_VU_ITERATIONS = "per-vu-iterations"
    CONSTANT_VUS = "constant-vus"
    RAMPING_VUS = "ramping-vus"
    CONSTANT_ARRIVAL_RATE = "constant-arrival-rate"
    RAMPING_ARRIVAL_RATE = "ramping-arrival-rate"
    EXTERNALLY_CONTROLLED = "externally-controlled"
# pragma: no cover  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002TlZaUFVBPT06NmVkNzQ3YTE=


class MetricType(str, Enum):
    """K6 custom metric types."""
    COUNTER = "Counter"
    GAUGE = "Gauge"
    RATE = "Rate"
    TREND = "Trend"


@dataclass
class Stage:
    """Ramping stage definition.
    
    Attributes:
        duration: Stage duration (e.g., "30s", "1m", "5m").
        target: Target VU count or rate at end of stage.
    """
    duration: str
    target: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {"duration": self.duration, "target": self.target}


@dataclass
class Threshold:
    """K6 threshold definition.
    
    Attributes:
        metric: Metric name (e.g., "http_req_duration", "errors").
        conditions: List of threshold conditions.
        abort_on_fail: Abort test if threshold fails.
    """
    metric: str
    conditions: List[str]
    abort_on_fail: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        if self.abort_on_fail:
            return [{"threshold": c, "abortOnFail": True} for c in self.conditions]
        return self.conditions


@dataclass
class CustomMetric:
    """Custom metric definition.
    
    Attributes:
        name: Metric name.
        metric_type: Type of metric (Counter, Gauge, Rate, Trend).
        description: Optional description.
    """
    name: str
    metric_type: MetricType
    description: Optional[str] = None
    
    def to_import(self) -> str:
        return f"import {{ {self.metric_type.value} }} from 'k6/metrics';"
    
    def to_declaration(self) -> str:
        desc = f"// {self.description}" if self.description else ""
        return f"const {self.name} = new {self.metric_type.value}('{self.name}'); {desc}"


@dataclass
class TestData:
    """Test data configuration.
    
    Attributes:
        file_path: Path to data file (CSV or JSON).
        variable_name: Variable name for SharedArray.
        is_csv: Whether the file is CSV format.
    """
    file_path: str
    variable_name: str
    is_csv: bool = True
    
    def to_import(self) -> str:
        return "import { SharedArray } from 'k6/data';"
    
    def to_declaration(self) -> str:
        if self.is_csv:
            return f"""const {self.variable_name} = new SharedArray('{self.variable_name}', function() {{
  return open('{self.file_path}').split('\\n').slice(1).map(line => {{
    const parts = line.split(',');
    return {{ /* map CSV columns */ }};
  }});
}});"""
        return f"""const {self.variable_name} = new SharedArray('{self.variable_name}', function() {{
  return JSON.parse(open('{self.file_path}'));
}});"""

# fmt: off  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002TlZaUFVBPT06NmVkNzQ3YTE=

@dataclass
class K6Scenario:
    """K6 scenario definition.
    
    Attributes:
        name: Scenario name.
        executor: Executor type.
        vus: Number of virtual users (for VU-based executors).
        duration: Test duration (for duration-based executors).
        iterations: Number of iterations (for iteration-based executors).
        stages: Ramping stages (for ramping executors).
        rate: Iteration rate (for arrival-rate executors).
        time_unit: Time unit for rate (default: "1s").
        pre_allocated_vus: Pre-allocated VUs for arrival-rate executors.
        max_vus: Maximum VUs for arrival-rate executors.
        start_time: Scenario start time offset.
        graceful_stop: Graceful stop duration.
        exec: Function to execute (default: "default").
        env: Environment variables for this scenario.
        tags: Tags for this scenario.
    """
    name: str
    executor: ExecutorType
    vus: Optional[int] = None
    duration: Optional[str] = None
    iterations: Optional[int] = None
    stages: Optional[List[Stage]] = None
    rate: Optional[int] = None
    time_unit: str = "1s"
    pre_allocated_vus: Optional[int] = None
    max_vus: Optional[int] = None
    start_time: Optional[str] = None
    graceful_stop: Optional[str] = None
    exec: str = "default"
    env: Optional[Dict[str, str]] = None
    tags: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to K6 options format."""
        result: Dict[str, Any] = {"executor": self.executor.value}

        if self.vus is not None:
            result["vus"] = self.vus
        if self.duration is not None:
            result["duration"] = self.duration
        if self.iterations is not None:
            result["iterations"] = self.iterations
        if self.stages is not None:
            result["stages"] = [s.to_dict() for s in self.stages]
        if self.rate is not None:
            result["rate"] = self.rate
            result["timeUnit"] = self.time_unit
        if self.pre_allocated_vus is not None:
            result["preAllocatedVUs"] = self.pre_allocated_vus
        if self.max_vus is not None:
            result["maxVUs"] = self.max_vus
        if self.start_time is not None:
            result["startTime"] = self.start_time
        if self.graceful_stop is not None:
            result["gracefulStop"] = self.graceful_stop
        if self.exec != "default":
            result["exec"] = self.exec
        if self.env:
            result["env"] = self.env
        if self.tags:
            result["tags"] = self.tags

        return result


@dataclass
class K6Options:
    """K6 test options configuration.

    Attributes:
        scenarios: Dictionary of scenario configurations.
        thresholds: Dictionary of threshold configurations.
        no_connection_reuse: Disable connection reuse.
        user_agent: Custom user agent.
        insecure_skip_tls_verify: Skip TLS verification.
        throw: Throw exceptions on failed checks.
        batch: Batch size for batch requests.
        batch_per_host: Batch size per host.
        dns: DNS configuration.
        hosts: Host overrides.
        http_debug: Enable HTTP debug output.
        no_vu_connection_reuse: Disable VU connection reuse.
        block_hostnames: Blocked hostnames.
        discard_response_bodies: Discard response bodies.
        tags: Global tags.
    """
    scenarios: Dict[str, K6Scenario] = field(default_factory=dict)
    thresholds: Dict[str, Threshold] = field(default_factory=dict)
    no_connection_reuse: bool = False
    user_agent: Optional[str] = None
    insecure_skip_tls_verify: bool = False
    throw: bool = False
    batch: int = 20
    batch_per_host: int = 6
    dns: Optional[Dict[str, Any]] = None
    hosts: Optional[Dict[str, str]] = None
    http_debug: Optional[str] = None
    no_vu_connection_reuse: bool = False
    block_hostnames: Optional[List[str]] = None
    discard_response_bodies: bool = False
    tags: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert options to K6 format."""
        result: Dict[str, Any] = {}

        if self.scenarios:
            result["scenarios"] = {
                name: scenario.to_dict()
                for name, scenario in self.scenarios.items()
            }

        if self.thresholds:
            result["thresholds"] = {
                name: threshold.to_dict()
                for name, threshold in self.thresholds.items()
            }

        if self.no_connection_reuse:
            result["noConnectionReuse"] = True
        if self.user_agent:
            result["userAgent"] = self.user_agent
        if self.insecure_skip_tls_verify:
            result["insecureSkipTLSVerify"] = True
        if self.throw:
            result["throw"] = True
        if self.batch != 20:
            result["batch"] = self.batch
        if self.batch_per_host != 6:
            result["batchPerHost"] = self.batch_per_host
        if self.dns:
            result["dns"] = self.dns
        if self.hosts:
            result["hosts"] = self.hosts
        if self.http_debug:
            result["httpDebug"] = self.http_debug
        if self.no_vu_connection_reuse:
            result["noVUConnectionReuse"] = True
        if self.block_hostnames:
            result["blockHostnames"] = self.block_hostnames
        if self.discard_response_bodies:
            result["discardResponseBodies"] = True
        if self.tags:
            result["tags"] = self.tags
# type: ignore  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002TlZaUFVBPT06NmVkNzQ3YTE=

        return result

    def to_javascript(self) -> str:
        """Generate JavaScript export statement."""
        import json
        options_dict = self.to_dict()
        options_json = json.dumps(options_dict, indent=2)
        return f"export const options = {options_json};"


# ============================================================================
# Factory Functions for Common Test Types
# ============================================================================

def create_smoke_test_options(
    vus: int = 3,
    duration: str = "1m",
    thresholds: Optional[Dict[str, List[str]]] = None,
) -> K6Options:
    """Create options for a smoke test.

    Smoke tests verify that the system works under minimal load.

    Args:
        vus: Number of virtual users (default: 1).
        duration: Test duration (default: 1m).
        thresholds: Custom thresholds.

    Returns:
        K6Options configured for smoke testing.
    """
    scenario = K6Scenario(
        name="smoke",
        executor=ExecutorType.CONSTANT_VUS,
        vus=vus,
        duration=duration,
    )

    default_thresholds = {
        "http_req_failed": Threshold("http_req_failed", ["rate<0.01"]),
        "http_req_duration": Threshold("http_req_duration", ["p(95)<500"]),
    }

    if thresholds:
        for metric, conditions in thresholds.items():
            default_thresholds[metric] = Threshold(metric, conditions)

    return K6Options(
        scenarios={"smoke": scenario},
        thresholds=default_thresholds,
    )


def create_load_test_options(
    stages: Optional[List[Stage]] = None,
    thresholds: Optional[Dict[str, List[str]]] = None,
) -> K6Options:
    """Create options for a load test.

    Load tests verify system behavior under expected load.

    Args:
        stages: Ramping stages (default: ramp up, sustain, ramp down).
        thresholds: Custom thresholds.

    Returns:
        K6Options configured for load testing.
    """
    if stages is None:
        stages = [
            Stage(duration="2m", target=50),   # Ramp up
            Stage(duration="5m", target=50),   # Sustain
            Stage(duration="2m", target=0),    # Ramp down
        ]

    scenario = K6Scenario(
        name="load",
        executor=ExecutorType.RAMPING_VUS,
        stages=stages,
    )

    default_thresholds = {
        "http_req_failed": Threshold("http_req_failed", ["rate<0.01"]),
        "http_req_duration": Threshold("http_req_duration", ["p(95)<500", "p(99)<1000"]),
    }

    if thresholds:
        for metric, conditions in thresholds.items():
            default_thresholds[metric] = Threshold(metric, conditions)

    return K6Options(
        scenarios={"load": scenario},
        thresholds=default_thresholds,
    )


def create_stress_test_options(
    max_vus: int = 200,
    thresholds: Optional[Dict[str, List[str]]] = None,
) -> K6Options:
    """Create options for a stress test.

    Stress tests push the system beyond normal capacity.

    Args:
        max_vus: Maximum virtual users to reach.
        thresholds: Custom thresholds.

    Returns:
        K6Options configured for stress testing.
    """
    stages = [
        Stage(duration="2m", target=max_vus // 4),
        Stage(duration="5m", target=max_vus // 4),
        Stage(duration="2m", target=max_vus // 2),
        Stage(duration="5m", target=max_vus // 2),
        Stage(duration="2m", target=max_vus),
        Stage(duration="5m", target=max_vus),
        Stage(duration="2m", target=0),
    ]

    scenario = K6Scenario(
        name="stress",
        executor=ExecutorType.RAMPING_VUS,
        stages=stages,
    )

    default_thresholds = {
        "http_req_failed": Threshold("http_req_failed", ["rate<0.05"]),
        "http_req_duration": Threshold("http_req_duration", ["p(95)<1000"]),
    }

    if thresholds:
        for metric, conditions in thresholds.items():
            default_thresholds[metric] = Threshold(metric, conditions)

    return K6Options(
        scenarios={"stress": scenario},
        thresholds=default_thresholds,
    )


def create_spike_test_options(
    spike_vus: int = 100,
    thresholds: Optional[Dict[str, List[str]]] = None,
) -> K6Options:
    """Create options for a spike test.

    Spike tests verify system behavior under sudden load increases.

    Args:
        spike_vus: Number of VUs during spike.
        thresholds: Custom thresholds.

    Returns:
        K6Options configured for spike testing.
    """
    stages = [
        Stage(duration="10s", target=spike_vus),  # Sudden spike
        Stage(duration="1m", target=spike_vus),   # Stay at spike
        Stage(duration="10s", target=0),          # Quick recovery
    ]

    scenario = K6Scenario(
        name="spike",
        executor=ExecutorType.RAMPING_VUS,
        stages=stages,
    )
# fmt: off  My80OmFIVnBZMlhtblk3a3ZiUG1yS002TlZaUFVBPT06NmVkNzQ3YTE=

    default_thresholds = {
        "http_req_failed": Threshold("http_req_failed", ["rate<0.10"]),
        "http_req_duration": Threshold("http_req_duration", ["p(95)<2000"]),
    }

    if thresholds:
        for metric, conditions in thresholds.items():
            default_thresholds[metric] = Threshold(metric, conditions)

    return K6Options(
        scenarios={"spike": scenario},
        thresholds=default_thresholds,
    )


def create_soak_test_options(
    vus: int = 50,
    duration: str = "2h",
    thresholds: Optional[Dict[str, List[str]]] = None,
) -> K6Options:
    """Create options for a soak test.

    Soak tests verify system stability over extended periods.

    Args:
        vus: Number of virtual users.
        duration: Test duration (default: 2h).
        thresholds: Custom thresholds.

    Returns:
        K6Options configured for soak testing.
    """
    stages = [
        Stage(duration="5m", target=vus),     # Ramp up
        Stage(duration=duration, target=vus), # Sustain
        Stage(duration="5m", target=0),       # Ramp down
    ]

    scenario = K6Scenario(
        name="soak",
        executor=ExecutorType.RAMPING_VUS,
        stages=stages,
    )

    default_thresholds = {
        "http_req_failed": Threshold("http_req_failed", ["rate<0.01"]),
        "http_req_duration": Threshold("http_req_duration", ["p(95)<500"]),
    }

    if thresholds:
        for metric, conditions in thresholds.items():
            default_thresholds[metric] = Threshold(metric, conditions)

    return K6Options(
        scenarios={"soak": scenario},
        thresholds=default_thresholds,
    )


def create_breakpoint_test_options(
    start_vus: int = 10,
    max_vus: int = 500,
    step_duration: str = "2m",
    step_increase: int = 20,
    thresholds: Optional[Dict[str, List[str]]] = None,
) -> K6Options:
    """Create options for a breakpoint test.

    Breakpoint tests find the system's breaking point by gradually increasing load.

    Args:
        start_vus: Starting number of VUs.
        max_vus: Maximum VUs to reach.
        step_duration: Duration of each step.
        step_increase: VU increase per step.
        thresholds: Custom thresholds (with abort_on_fail).

    Returns:
        K6Options configured for breakpoint testing.
    """
    stages = []
    current_vus = start_vus
    while current_vus <= max_vus:
        stages.append(Stage(duration=step_duration, target=current_vus))
        current_vus += step_increase

    scenario = K6Scenario(
        name="breakpoint",
        executor=ExecutorType.RAMPING_VUS,
        stages=stages,
    )

    # Breakpoint tests should abort when thresholds fail
    default_thresholds = {
        "http_req_failed": Threshold("http_req_failed", ["rate<0.10"], abort_on_fail=True),
        "http_req_duration": Threshold("http_req_duration", ["p(95)<3000"], abort_on_fail=True),
    }

    if thresholds:
        for metric, conditions in thresholds.items():
            default_thresholds[metric] = Threshold(metric, conditions, abort_on_fail=True)

    return K6Options(
        scenarios={"breakpoint": scenario},
        thresholds=default_thresholds,
    )

