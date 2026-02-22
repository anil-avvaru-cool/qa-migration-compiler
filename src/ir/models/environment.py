from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional


class TimeoutConfig(BaseModel):
    """Timeout configuration for wait strategies."""
    implicit: int = Field(default=5000, description="Implicit wait in milliseconds")
    explicit: int = Field(default=10000, description="Explicit wait in milliseconds")
    pageLoad: int = Field(default=30000, description="Page load timeout in milliseconds")

    model_config = ConfigDict(frozen=True)


class RetryPolicy(BaseModel):
    """Retry configuration for failed steps."""
    enabled: bool = Field(default=True, description="Whether retries are enabled")
    maxRetries: int = Field(default=2, description="Maximum number of retries")

    model_config = ConfigDict(frozen=True)


class EnvironmentIR(BaseModel):
    """Enhanced Environment IR model matching target schema."""
    baseUrls: Dict[str, str] = Field(default_factory=dict, description="Base URLs by environment (e.g., qa, staging, prod)")
    executionMode: str = Field(default="sequential", description="Execution mode: sequential or parallel")
    browsers: List[str] = Field(default_factory=lambda: ["chrome"], description="List of browsers to test on")
    timeouts: TimeoutConfig = Field(default_factory=TimeoutConfig, description="Timeout configuration")
    retryPolicy: RetryPolicy = Field(default_factory=RetryPolicy, description="Retry policy configuration")

    model_config = ConfigDict(frozen=True)
