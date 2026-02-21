from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ProjectMetadata(BaseModel):
    name: str
    version: str = "1.0.0"
    generated_at: str
    source_language: str
    compiler_version: str


class ProjectIR(BaseModel):
    id: str = Field(..., description="Deterministic project ID")
    metadata: ProjectMetadata
    environments: List[str] = Field(default_factory=list)
    suites: List[str] = Field(default_factory=list)
    tests: List[str] = Field(default_factory=list)

    class Config:
        frozen = True
