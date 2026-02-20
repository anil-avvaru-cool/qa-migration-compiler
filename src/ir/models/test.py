from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class StepIR(BaseModel):
    id: str
    type: str  # action | assertion
    name: str
    target: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = True


class TestIR(BaseModel):
    id: str = Field(..., description="Deterministic test ID")
    name: str
    suite_id: Optional[str] = None
    environment_id: Optional[str] = None
    data_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    steps: List[StepIR] = Field(default_factory=list)

    class Config:
        frozen = True
