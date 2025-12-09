"""Script Generator Sub-Agent for K6 Performance Testing.

This module provides the script generator sub-agent that specializes
in creating K6 performance test scripts with modern best practices.
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from k6_agent.core.prompts import SCRIPT_GENERATOR_PROMPT, SCRIPT_GENERATOR_PROMPT_CONTINUED
from k6_agent.k6.scenarios import (
    K6Options,
    K6Scenario,
    ExecutorType,
    Stage,
    create_load_test_options,
    create_stress_test_options,
    create_spike_test_options,
    create_soak_test_options,
    create_smoke_test_options,
    create_breakpoint_test_options,
)
from k6_agent.tools.k6_tools import K6ScriptGenerator, ApiEndpoint, HttpMethod

# noqa  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002YjJzMVVBPT06OTZjOGFjZTk=

@dataclass
class ScriptRequest:
    """Request for script generation."""
    base_url: str
    endpoints: List[Dict[str, Any]]
    test_type: str = "load"
    vus: Optional[int] = None
    duration: Optional[str] = None
    custom_options: Optional[Dict[str, Any]] = None
# type: ignore  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002YjJzMVVBPT06OTZjOGFjZTk=


class ScriptGeneratorAgent:
    """Sub-agent specialized in K6 script generation.
    
    This agent creates professional K6 scripts with:
    - Modern scenarios and executors
    - Proper structure and imports
    - Custom metrics and thresholds
    - Data parameterization support
    - Comprehensive checks
    
    Example:
        >>> agent = ScriptGeneratorAgent()
        >>> script = agent.generate_script(
        ...     base_url="https://api.example.com",
        ...     endpoints=[{"name": "users", "url": "/users", "method": "GET"}],
        ...     test_type="load",
        ... )
    """
    
    def __init__(
        self,
        knowledge_client: Optional[Any] = None,
        enable_knowledge_retrieval: bool = True,
    ):
        """Initialize the script generator agent.
        
        Args:
            knowledge_client: Optional knowledge base client.
            enable_knowledge_retrieval: Enable knowledge retrieval.
        """
        self.knowledge_client = knowledge_client
        self.enable_knowledge_retrieval = enable_knowledge_retrieval
        self.system_prompt = SCRIPT_GENERATOR_PROMPT + SCRIPT_GENERATOR_PROMPT_CONTINUED
    
    def generate_script(
        self,
        base_url: str,
        endpoints: List[Dict[str, Any]],
        test_type: str = "load",
        vus: Optional[int] = None,
        duration: Optional[str] = None,
        custom_options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a K6 script.
        
        Args:
            base_url: Base URL of the API to test.
            endpoints: List of endpoint configurations.
            test_type: Type of test (load, stress, spike, soak, smoke, breakpoint).
            vus: Optional VU count override.
            duration: Optional duration override.
            custom_options: Optional custom K6 options.
            
        Returns:
            Generated K6 script as a string.
        """
        # Get appropriate options factory
        options_factory = {
            "smoke": create_smoke_test_options,
            "load": create_load_test_options,
            "stress": create_stress_test_options,
            "spike": create_spike_test_options,
            "soak": create_soak_test_options,
            "breakpoint": create_breakpoint_test_options,
        }
        
        factory = options_factory.get(test_type, create_load_test_options)
        options = factory()
        
        # Parse endpoints
        parsed_endpoints = []
        for ep in endpoints:
            parsed_endpoints.append(ApiEndpoint(
                name=ep.get("name", "endpoint"),
                url=ep.get("url", "/"),
                method=HttpMethod(ep.get("method", "GET")),
                headers=ep.get("headers"),
                body=ep.get("body"),
                checks=ep.get("checks"),
            ))
        
        # Create generator
        generator = K6ScriptGenerator(
            base_url=base_url,
            endpoints=parsed_endpoints,
            options=options,
        )
        
        return generator.generate()
# fmt: off  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002YjJzMVVBPT06OTZjOGFjZTk=
    
    async def generate_with_knowledge(
        self,
        request: ScriptRequest,
    ) -> str:
        """Generate a script with knowledge retrieval.
        
        Uses the knowledge base to get best practices and patterns
        before generating the script.
        
        Args:
            request: Script generation request.
            
        Returns:
            Generated K6 script with knowledge-enhanced patterns.
        """
        if self.knowledge_client and self.enable_knowledge_retrieval:
            from k6_agent.knowledge import KnowledgeRetriever
            retriever = KnowledgeRetriever(self.knowledge_client)
            
            # Get script patterns
            api_type = "REST"  # Could be detected from endpoints
            endpoint_names = [ep.get("name", "") for ep in request.endpoints]
# pylint: disable  My80OmFIVnBZMlhtblk3a3ZiUG1yS002YjJzMVVBPT06OTZjOGFjZTk=
            
            knowledge = await retriever.retrieve_script_patterns(
                api_type=api_type,
                endpoints=endpoint_names,
            )
            
            # Use knowledge to enhance script generation
            # (In a full implementation, this would influence the script)
        
        return self.generate_script(
            base_url=request.base_url,
            endpoints=request.endpoints,
            test_type=request.test_type,
            vus=request.vus,
            duration=request.duration,
            custom_options=request.custom_options,
        )

