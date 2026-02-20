from pydantic import BaseModel, Field
from typing import Dict, Optional


class EnvironmentIR(BaseModel):
    id: str = Field(..., description="Deterministic environment ID")
    name: str
    base_url: Optional[str] = None
    variables: Dict[str, str] = Field(default_factory=dict)

    class Config:
        frozen = True
