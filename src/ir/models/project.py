from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class ProjectIR(BaseModel):
    """Enhanced Project IR model matching target schema."""
    irVersion: str = Field(default="2.0.0", description="IR schema version")
    projectName: str = Field(..., description="Project name")
    sourceFramework: str = Field(..., description="Source framework (e.g., Selenium-Java-TestNG)")
    targetFramework: str = Field(..., description="Target framework (e.g., Playwright-TS)")
    architecturePattern: str = Field(default="POM", description="Architecture pattern (e.g., POM, POJO)")
    supportsParallel: bool = Field(default=False, description="Whether parallel execution is supported")
    createdOn: str = Field(..., description="Creation date in YYYY-MM-DD format")

    model_config = ConfigDict(frozen=True)
