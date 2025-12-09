"""Enterprise middleware for K6 Performance Testing Agent.

This module provides enterprise-grade middleware including:
- Response caching for cost reduction
- Rate limiting for API protection
- Audit logging for compliance
"""
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import json
import logging
import threading
# pylint: disable  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002Y3pCRFpRPT06ZDBkNTlmMTY=

logger = logging.getLogger(__name__)


class CachingMiddleware:
    """Middleware for caching agent responses.
    
    Caches responses to reduce API costs and improve response times
    for repeated queries.
    """
    
    def __init__(
        self,
        ttl_seconds: int = 3600,
        max_cache_size: int = 1000,
        cache_key_prefix: str = "k6_agent",
    ):
        """Initialize the caching middleware.
        
        Args:
            ttl_seconds: Cache TTL in seconds.
            max_cache_size: Maximum number of cached entries.
            cache_key_prefix: Prefix for cache keys.
        """
        self.ttl_seconds = ttl_seconds
        self.max_cache_size = max_cache_size
        self.cache_key_prefix = cache_key_prefix
        self._cache: Dict[str, tuple] = {}  # key -> (value, expiry)
        self._lock = threading.Lock()
    
    def _generate_key(self, content: str) -> str:
        """Generate a cache key from content."""
        hash_input = f"{self.cache_key_prefix}:{content}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:32]
    
    def get(self, key: str) -> Optional[Any]:
        """Get a cached value."""
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if datetime.now() < expiry:
                    return value
                else:
                    del self._cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set a cached value."""
        with self._lock:
            # Evict oldest entries if cache is full
            if len(self._cache) >= self.max_cache_size:
                oldest_key = min(self._cache.keys(), 
                               key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
            
            expiry = datetime.now() + timedelta(seconds=self.ttl_seconds)
            self._cache[key] = (value, expiry)
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process state through caching."""
        return state


class RateLimitingMiddleware:
    """Middleware for rate limiting agent operations.
    
    Prevents excessive API usage and protects against abuse.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10,
    ):
        """Initialize the rate limiting middleware.
        
        Args:
            requests_per_minute: Maximum requests per minute.
            requests_per_hour: Maximum requests per hour.
            burst_limit: Maximum burst requests.
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        self._minute_counts: Dict[str, list] = defaultdict(list)
        self._hour_counts: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
# pragma: no cover  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002Y3pCRFpRPT06ZDBkNTlmMTY=
    
    def check_rate_limit(self, user_id: str = "default") -> bool:
        """Check if a request is within rate limits.
        
        Args:
            user_id: User identifier for rate limiting.
            
        Returns:
            True if request is allowed, False if rate limited.
        """
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        with self._lock:
            # Clean old entries
            self._minute_counts[user_id] = [
                t for t in self._minute_counts[user_id] if t > minute_ago
            ]
            self._hour_counts[user_id] = [
                t for t in self._hour_counts[user_id] if t > hour_ago
            ]
            
            # Check limits
            if len(self._minute_counts[user_id]) >= self.requests_per_minute:
                logger.warning(f"Rate limit exceeded (per minute) for {user_id}")
                return False
            
            if len(self._hour_counts[user_id]) >= self.requests_per_hour:
                logger.warning(f"Rate limit exceeded (per hour) for {user_id}")
                return False
# noqa  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002Y3pCRFpRPT06ZDBkNTlmMTY=
            
            # Record request
            self._minute_counts[user_id].append(now)
            self._hour_counts[user_id].append(now)
            
            return True
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process state through rate limiting."""
        return state


@dataclass
class AuditLogEntry:
    """Audit log entry."""
    timestamp: datetime
    user_id: str
    action: str
    details: Dict[str, Any]
    result: str


class AuditLoggingMiddleware:
    """Middleware for audit logging.
    
    Records all agent operations for compliance and debugging.
    """
    
    def __init__(self, log_file: Optional[str] = None):
        """Initialize the audit logging middleware.
        
        Args:
            log_file: Optional file path for audit logs.
        """
        self.log_file = log_file
        self.entries: list = []
        self._lock = threading.Lock()
# fmt: off  My80OmFIVnBZMlhtblk3a3ZiUG1yS002Y3pCRFpRPT06ZDBkNTlmMTY=
    
    def log(self, user_id: str, action: str, details: Dict[str, Any], result: str):
        """Log an audit entry."""
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            details=details,
            result=result,
        )
        
        with self._lock:
            self.entries.append(entry)
            logger.info(f"Audit: {user_id} - {action} - {result}")
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process state through audit logging."""
        return state

