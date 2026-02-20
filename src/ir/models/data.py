from pydantic import BaseModel, Field
from typing import Dict, Any


class TestDataIR(BaseModel):
    id: str = Field(..., description="Deterministic data ID")
    name: str
    values: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = True
