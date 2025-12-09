"""K6 integration layer for performance testing.

This module provides K6-specific components including:
- Scenario and executor definitions
- Protocol handlers (HTTP, WebSocket, gRPC)
- Browser testing support
- Output integrations
"""
from k6_agent.k6.scenarios import (
    K6Options,
    K6Scenario,
    ExecutorType,
    Stage,
    CustomMetric,
    MetricType,
    TestData,
    Threshold,
    create_smoke_test_options,
    create_load_test_options,
    create_stress_test_options,
    create_spike_test_options,
    create_soak_test_options,
    create_breakpoint_test_options,
)
# noqa  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002TjBnMFp3PT06NTQ1ZDI3NGQ=

__all__ = [
    # Core types
    "K6Options",
    "K6Scenario",
    "ExecutorType",
    "Stage",
    "CustomMetric",
    "MetricType",
    "TestData",
    "Threshold",
    # Factory functions
    "create_smoke_test_options",
    "create_load_test_options",
    "create_stress_test_options",
    "create_spike_test_options",
    "create_soak_test_options",
    "create_breakpoint_test_options",
]

# fmt: off  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002TjBnMFp3PT06NTQ1ZDI3NGQ=
