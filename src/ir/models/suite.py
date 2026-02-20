from pydantic import BaseModel, Field
from typing import List, Optional


class SuiteIR(BaseModel):
    id: str = Field(..., description="Deterministic suite ID")
    name: str
    parent_id: Optional[str] = None
    tests: List[str] = Field(default_factory=list)

    class Config:
        frozen = True
