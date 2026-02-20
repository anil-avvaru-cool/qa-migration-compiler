from pydantic import BaseModel, Field
from typing import Optional


class TargetIR(BaseModel):
    id: str = Field(..., description="Deterministic target ID")
    name: str
    type: str = Field(..., description="page | api | component")
    locator: Optional[str] = None
    metadata: Optional[dict] = None

    class Config:
        frozen = True
