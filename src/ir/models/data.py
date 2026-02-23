from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List


class DataRecord(BaseModel):
    """A single data record with key-value pairs."""
    # Allow arbitrary fields
    model_config = ConfigDict(extra="allow", frozen=True)


class TestDataIR(BaseModel):
    """Enhanced Test Data IR model for datasets."""
    dataSetId: str = Field(..., description="Unique dataset identifier")
    type: str = Field(default="inline", description="Data type: inline, csv, database, api")
    records: List[Dict[str, Any]] = Field(default_factory=list, description="List of data records")

    model_config = ConfigDict(frozen=True)
