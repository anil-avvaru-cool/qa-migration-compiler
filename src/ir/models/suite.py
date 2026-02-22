from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class SuiteIR(BaseModel):
    """Enhanced Suite IR model."""
    suiteId: str = Field(..., description="Unique suite identifier")
    description: Optional[str] = Field(None, description="Suite description")
    tests: List[str] = Field(default_factory=list, description="List of test IDs in this suite")

    model_config = ConfigDict(frozen=True)
