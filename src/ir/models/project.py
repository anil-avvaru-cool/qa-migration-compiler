from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class ProjectMetadata(BaseModel):
    """Project metadata nested within ProjectIR."""
    name: str = Field(..., description="Project name")
    source_language: str = Field(default="java", description="Source language/framework")
    target_language: Optional[str] = Field(None, description="Target language/framework")
    version: Optional[str] = Field(None, description="Project version")
    generated_at: Optional[str] = Field(None, description="Timestamp when IR was generated")
    compiler_version: Optional[str] = Field(None, description="Compiler version that generated the IR")

    model_config = ConfigDict(frozen=True)


class ProjectIR(BaseModel):
    """Enhanced Project IR model matching target schema."""
    id: Optional[str] = Field(None, description="Project ID")
    irVersion: str = Field(default="2.0.0", description="IR schema version")
    projectName: str = Field(..., description="Project name")
    sourceFramework: str = Field(..., description="Source framework (e.g., Selenium-Java-TestNG)")
    targetFramework: str = Field(..., description="Target framework (e.g., Playwright-TS)")
    architecturePattern: str = Field(default="POM", description="Architecture pattern (e.g., POM, POJO)")
    supportsParallel: bool = Field(default=False, description="Whether parallel execution is supported")
    createdOn: str = Field(..., description="Creation date in YYYY-MM-DD format")
    metadata: Optional[ProjectMetadata] = Field(None, description="Project metadata")
    suites: List[Dict[str, Any]] = Field(default_factory=list, description="Test suites")
    tests: List[Dict[str, Any]] = Field(default_factory=list, description="Tests")
    environments: List[Dict[str, Any]] = Field(default_factory=list, description="Execution environments")

    model_config = ConfigDict(frozen=True)


