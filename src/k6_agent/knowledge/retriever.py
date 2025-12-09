"""Knowledge retrieval tools for K6 performance testing agents.

This module provides specialized tools for retrieving knowledge from the RAG
knowledge base in different phases of performance testing:
- Scenario design phase
- Script writing phase
- Result analysis phase
- Bottleneck diagnosis phase

Each tool is optimized for its specific use case with appropriate query modes
and keyword configurations.
"""
from typing import Optional, List, Dict, Any
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from k6_agent.knowledge.client import KnowledgeClient, QueryMode


class KnowledgeRetriever:
    """Knowledge retriever with specialized methods for different testing phases.
    
    This class provides high-level retrieval methods optimized for each phase
    of the performance testing workflow.
    """
    
    def __init__(self, client: KnowledgeClient):
        """Initialize the retriever.
        
        Args:
            client: Knowledge base client instance.
        """
        self.client = client
    
    async def retrieve_scenario_design_knowledge(
        self,
        test_type: str,
        system_description: str,
        requirements: Optional[str] = None,
    ) -> str:
        """Retrieve knowledge for performance scenario design.
        
        Args:
            test_type: Type of test (load, stress, spike, soak, smoke, breakpoint).
            system_description: Description of the system under test.
            requirements: Optional performance requirements or SLOs.
            
        Returns:
            Formatted knowledge context for scenario design.
        """
        query = f"""Performance test scenario design for {test_type} testing.
System: {system_description}
{f'Requirements: {requirements}' if requirements else ''}
Looking for: test patterns, VU configurations, duration settings, threshold recommendations."""
        
        return await self.client.query_for_context(
            query=query,
            mode=QueryMode.MIX,
            hl_keywords=["performance testing", test_type, "scenario design"],
            ll_keywords=["k6", "virtual users", "thresholds", "stages"],
        )
# fmt: off  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002TWxSdE1RPT06YTExNTcxZDI=
    
    async def retrieve_script_patterns(
        self,
        api_type: str,
        endpoints: List[str],
        features: Optional[List[str]] = None,
    ) -> str:
        """Retrieve K6 script patterns and best practices.
        
        Args:
            api_type: Type of API (REST, GraphQL, gRPC, WebSocket).
            endpoints: List of endpoint descriptions.
            features: Optional list of required features (auth, data param, etc).
            
        Returns:
            Formatted knowledge context for script writing.
        """
        features_str = ", ".join(features) if features else "standard patterns"
        endpoints_str = ", ".join(endpoints[:5])
        
        query = f"""K6 script patterns for {api_type} API testing.
Endpoints: {endpoints_str}
Required features: {features_str}
Looking for: import statements, request patterns, check assertions, custom metrics."""
        
        return await self.client.query_for_context(
            query=query,
            mode=QueryMode.LOCAL,
            hl_keywords=["k6 script", api_type, "JavaScript"],
            ll_keywords=["http", "check", "group", "metrics", "scenarios"],
        )
    
    async def retrieve_analysis_methodology(
        self,
        metrics: List[str],
        anomalies: Optional[List[str]] = None,
    ) -> str:
        """Retrieve performance analysis methodology.
        
        Args:
            metrics: List of metric types to analyze.
            anomalies: Optional list of observed anomalies.
            
        Returns:
            Formatted knowledge context for result analysis.
        """
        metrics_str = ", ".join(metrics)
        anomalies_str = ", ".join(anomalies) if anomalies else "none detected"
        
        query = f"""Performance test result analysis methodology.
Metrics: {metrics_str}
Observed anomalies: {anomalies_str}
Looking for: analysis techniques, statistical methods, interpretation guidelines."""
# fmt: off  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002TWxSdE1RPT06YTExNTcxZDI=
        
        return await self.client.query_for_context(
            query=query,
            mode=QueryMode.HYBRID,
            hl_keywords=["performance analysis", "metrics", "interpretation"],
            ll_keywords=["percentile", "response time", "throughput", "error rate"],
        )
    
    async def retrieve_bottleneck_diagnosis(
        self,
        symptoms: List[str],
        system_components: Optional[List[str]] = None,
    ) -> str:
        """Retrieve bottleneck diagnosis knowledge.

        Args:
            symptoms: List of observed performance symptoms.
            system_components: Optional list of system components.

        Returns:
            Formatted knowledge context for bottleneck diagnosis.
        """
        symptoms_str = ", ".join(symptoms)
        components_str = ", ".join(system_components) if system_components else "unknown"

        query = f"""Performance bottleneck diagnosis and root cause analysis.
Symptoms: {symptoms_str}
System components: {components_str}
Looking for: diagnosis methods, common causes, resolution strategies."""

        return await self.client.query_for_context(
            query=query,
            mode=QueryMode.GLOBAL,
            hl_keywords=["bottleneck", "diagnosis", "root cause"],
            ll_keywords=["CPU", "memory", "network", "database", "latency"],
        )


# ============================================================================
# LangChain Tool Factories
# ============================================================================

class ScenarioDesignInput(BaseModel):
    """Input schema for scenario design knowledge retrieval."""
    test_type: str = Field(
        description="Type of performance test: load, stress, spike, soak, smoke, or breakpoint"
    )
    system_description: str = Field(
        description="Brief description of the system under test"
    )
    requirements: Optional[str] = Field(
        default=None,
        description="Optional performance requirements or SLOs"
    )


class ScriptOptimizationInput(BaseModel):
    """Input schema for script optimization knowledge retrieval."""
    api_type: str = Field(
        description="Type of API: REST, GraphQL, gRPC, WebSocket"
    )
    endpoints: List[str] = Field(
        description="List of endpoint descriptions to test"
    )
    features: Optional[List[str]] = Field(
        default=None,
        description="Required features like auth, data parameterization, etc"
    )


class AnalysisGuideInput(BaseModel):
    """Input schema for analysis methodology retrieval."""
    metrics: List[str] = Field(
        description="List of metric types to analyze"
    )
    anomalies: Optional[List[str]] = Field(
        default=None,
        description="List of observed anomalies or issues"
    )


class BottleneckDiagnosisInput(BaseModel):
    """Input schema for bottleneck diagnosis knowledge retrieval."""
    symptoms: List[str] = Field(
        description="List of observed performance symptoms"
    )
    system_components: Optional[List[str]] = Field(
        default=None,
        description="List of system components involved"
    )


def create_knowledge_retrieval_tool(client: KnowledgeClient) -> BaseTool:
    """Create a general knowledge retrieval tool."""
    retriever = KnowledgeRetriever(client)

    @tool
    async def retrieve_performance_knowledge(query: str) -> str:
        """Retrieve performance testing knowledge from the knowledge base.

        Use this tool to get expert knowledge, best practices, and reference
        materials for any performance testing topic.

        Args:
            query: Natural language query about performance testing.

        Returns:
            Relevant knowledge and references from the knowledge base.
        """
        return await client.query_for_context(query)
# type: ignore  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002TWxSdE1RPT06YTExNTcxZDI=

    return retrieve_performance_knowledge


def create_scenario_design_tool(client: KnowledgeClient) -> BaseTool:
    """Create a scenario design knowledge retrieval tool."""
    retriever = KnowledgeRetriever(client)

    @tool(args_schema=ScenarioDesignInput)
    async def retrieve_scenario_design_best_practices(
        test_type: str,
        system_description: str,
        requirements: Optional[str] = None,
    ) -> str:
        """Retrieve best practices for performance test scenario design.

        Use this tool when designing performance test scenarios to get
        expert recommendations on VU configurations, duration settings,
        threshold definitions, and stage configurations.

        Args:
            test_type: Type of test (load, stress, spike, soak, smoke, breakpoint).
            system_description: Description of the system under test.
            requirements: Optional performance requirements or SLOs.

        Returns:
            Best practices and recommendations for scenario design.
        """
        return await retriever.retrieve_scenario_design_knowledge(
            test_type, system_description, requirements
        )

    return retrieve_scenario_design_best_practices


def create_script_optimization_tool(client: KnowledgeClient) -> BaseTool:
    """Create a K6 script optimization knowledge retrieval tool."""
    retriever = KnowledgeRetriever(client)

    @tool(args_schema=ScriptOptimizationInput)
    async def retrieve_k6_script_patterns(
        api_type: str,
        endpoints: List[str],
        features: Optional[List[str]] = None,
    ) -> str:
        """Retrieve K6 script patterns and optimization techniques.

        Use this tool when writing K6 scripts to get expert patterns,
        import statements, request templates, and best practices for
        specific API types and features.

        Args:
            api_type: Type of API (REST, GraphQL, gRPC, WebSocket).
            endpoints: List of endpoint descriptions.
            features: Required features (auth, data param, etc).

        Returns:
            K6 script patterns and optimization recommendations.
        """
        return await retriever.retrieve_script_patterns(
            api_type, endpoints, features
        )

    return retrieve_k6_script_patterns


def create_analysis_guide_tool(client: KnowledgeClient) -> BaseTool:
    """Create a result analysis methodology retrieval tool."""
    retriever = KnowledgeRetriever(client)
# type: ignore  My80OmFIVnBZMlhtblk3a3ZiUG1yS002TWxSdE1RPT06YTExNTcxZDI=

    @tool(args_schema=AnalysisGuideInput)
    async def retrieve_analysis_methodology(
        metrics: List[str],
        anomalies: Optional[List[str]] = None,
    ) -> str:
        """Retrieve performance analysis methodology and guidelines.

        Use this tool when analyzing performance test results to get
        expert guidance on interpreting metrics, identifying patterns,
        and drawing conclusions from the data.

        Args:
            metrics: List of metric types to analyze.
            anomalies: Optional list of observed anomalies.

        Returns:
            Analysis methodology and interpretation guidelines.
        """
        return await retriever.retrieve_analysis_methodology(metrics, anomalies)

    return retrieve_analysis_methodology


def create_bottleneck_diagnosis_tool(client: KnowledgeClient) -> BaseTool:
    """Create a bottleneck diagnosis knowledge retrieval tool."""
    retriever = KnowledgeRetriever(client)

    @tool(args_schema=BottleneckDiagnosisInput)
    async def diagnose_performance_bottleneck(
        symptoms: List[str],
        system_components: Optional[List[str]] = None,
    ) -> str:
        """Retrieve bottleneck diagnosis knowledge and resolution strategies.

        Use this tool when identifying and diagnosing performance bottlenecks
        to get expert knowledge on common causes, diagnosis methods, and
        resolution strategies.

        Args:
            symptoms: List of observed performance symptoms.
            system_components: Optional list of system components.

        Returns:
            Bottleneck diagnosis knowledge and resolution strategies.
        """
        return await retriever.retrieve_bottleneck_diagnosis(
            symptoms, system_components
        )

    return diagnose_performance_bottleneck

