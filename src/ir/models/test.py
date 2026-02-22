from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any


class StepIR(BaseModel):
    id: str
    type: str  # action | assertion
    name: str
    targetId: Optional[str] = None
    targetNameId: Optional[str] = None  # Variable/field name that holds the target
    targetNodeId: Optional[str] = None  # AST node ID of the target locator
    parameters: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)


class TestIR(BaseModel):
    id: str = Field(..., description="Deterministic test ID")
    name: str
    suite_id: Optional[str] = None
    environment_id: Optional[str] = None
    data_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    steps: List[StepIR] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)
