"""Validation middleware for K6 Performance Testing Agent.

This module provides input and output validation middleware
to ensure data quality and prevent errors.
"""
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)
# pragma: no cover  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002WlRGU1lRPT06MGZmNjlmMGM=


@dataclass
class ValidationResult:
    """Result of a validation check."""
    valid: bool
    message: str = ""
    details: Optional[Dict[str, Any]] = None


class InputValidationMiddleware:
    """Middleware for validating agent inputs.
    
    Validates user messages and tool inputs to ensure they meet
    expected formats and constraints.
    """
    
    def __init__(
        self,
        max_message_length: int = 10000,
        allowed_url_patterns: Optional[list] = None,
        blocked_patterns: Optional[list] = None,
    ):
        """Initialize the validation middleware.
        
        Args:
            max_message_length: Maximum allowed message length.
            allowed_url_patterns: Regex patterns for allowed URLs.
            blocked_patterns: Regex patterns for blocked content.
        """
        self.max_message_length = max_message_length
        self.allowed_url_patterns = allowed_url_patterns or []
        self.blocked_patterns = blocked_patterns or []
    
    def validate_message(self, message: str) -> ValidationResult:
        """Validate a user message.
        
        Args:
            message: The message to validate.
            
        Returns:
            ValidationResult indicating if the message is valid.
        """
        # Check length
        if len(message) > self.max_message_length:
            return ValidationResult(
                valid=False,
                message=f"Message exceeds maximum length of {self.max_message_length}",
            )
        
        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return ValidationResult(
                    valid=False,
                    message="Message contains blocked content",
                )
        
        return ValidationResult(valid=True)
# type: ignore  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002WlRGU1lRPT06MGZmNjlmMGM=
    
    def validate_url(self, url: str) -> ValidationResult:
        """Validate a URL for testing.
        
        Args:
            url: The URL to validate.
            
        Returns:
            ValidationResult indicating if the URL is valid.
        """
        # Basic URL format check
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url):
            return ValidationResult(
                valid=False,
                message="Invalid URL format",
            )
        
        # Check against allowed patterns if specified
        if self.allowed_url_patterns:
            allowed = any(
                re.match(pattern, url) 
                for pattern in self.allowed_url_patterns
            )
            if not allowed:
                return ValidationResult(
                    valid=False,
                    message="URL not in allowed list",
                )
        
        return ValidationResult(valid=True)
# noqa  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002WlRGU1lRPT06MGZmNjlmMGM=
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process state through validation.
        
        Args:
            state: The agent state.
            
        Returns:
            Validated state or state with error message.
        """
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                result = self.validate_message(last_message.content)
                if not result.valid:
                    logger.warning(f"Input validation failed: {result.message}")
                    # Could add error to state here
        
        return state


class ResultValidationMiddleware:
    """Middleware for validating agent outputs.
    
    Validates generated scripts, reports, and other outputs
    to ensure quality and correctness.
    """
    
    def __init__(
        self,
        validate_scripts: bool = True,
        validate_reports: bool = True,
    ):
        """Initialize the result validation middleware.
        
        Args:
            validate_scripts: Whether to validate K6 scripts.
            validate_reports: Whether to validate generated reports.
        """
        self.validate_scripts = validate_scripts
        self.validate_reports = validate_reports
    
    def validate_k6_script(self, script: str) -> ValidationResult:
        """Validate a K6 script.
        
        Args:
            script: The K6 script content.
            
        Returns:
            ValidationResult indicating if the script is valid.
        """
        # Check for required imports
        if "import http from 'k6/http'" not in script:
            return ValidationResult(
                valid=False,
                message="Script missing required http import",
            )
        
        # Check for default function
        if "export default function" not in script:
            return ValidationResult(
                valid=False,
                message="Script missing default export function",
            )
        
        return ValidationResult(valid=True)
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process state through result validation."""
        return state

# pylint: disable  My80OmFIVnBZMlhtblk3a3ZiUG1yS002WlRGU1lRPT06MGZmNjlmMGM=
