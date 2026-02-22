from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any


class DataSource(BaseModel):
    """Reference to data source (data field, UI element, etc.)."""
    source: str = Field(..., description="Source type: data, ui, constant, expression")
    field: Optional[str] = Field(None, description="Field name for data source")
    targetId: Optional[str] = Field(None, description="Target ID for UI source")
    value: Optional[str] = Field(None, description="Value for constant source")
    masked: Optional[bool] = Field(False, description="Whether value should be masked in logs")

    model_config = ConfigDict(frozen=True)


class StepInput(BaseModel):
    """Input data for a step."""
    source: str = Field(..., description="Source type: data, ui, constant")
    field: Optional[str] = Field(None, description="Field name from data source")
    masked: Optional[bool] = Field(False, description="Whether to mask in logs")

    model_config = ConfigDict(frozen=True)


class StepTarget(BaseModel):
    """Target reference in a step."""
    type: str = Field(..., description="Target type: element, url, api, etc.")
    value: Optional[str] = Field(None, description="Target value (URL, endpoint, etc.)")

    model_config = ConfigDict(frozen=True)


class StepIR(BaseModel):
    """Enhanced Step IR model with action/assertion structure."""
    stepId: str = Field(..., description="Unique step identifier")
    action: str = Field(..., description="Action type (click, type, select, navigate, waitForVisible, etc.)")
    targetId: Optional[str] = Field(None, description="Reference to target element")
    target: Optional[StepTarget] = Field(None, description="Target specification (for urls, etc.)")
    input: Optional[StepInput] = Field(None, description="Input data for the step")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional step parameters")

    model_config = ConfigDict(frozen=True)


class AssertionIR(BaseModel):
    """Enhanced Assertion IR model."""
    assertId: str = Field(..., description="Unique assertion identifier")
    type: str = Field(..., description="Assertion type (equals, contains, exists, visible, etc.)")
    actual: DataSource = Field(..., description="Actual value source")
    expected: DataSource = Field(..., description="Expected value source")

    model_config = ConfigDict(frozen=True)


class DataBinding(BaseModel):
    """Data binding configuration for parameterized tests."""
    dataSetId: str = Field(..., description="Reference to dataset")
    iterationStrategy: str = Field(default="row-wise", description="Iteration strategy: row-wise, column-wise")

    model_config = ConfigDict(frozen=True)


class TestIR(BaseModel):
    """Enhanced Test IR model with full test structure."""
    testId: str = Field(..., description="Unique test identifier")
    suiteId: Optional[str] = Field(None, description="Parent suite ID")
    priority: Optional[str] = Field(None, description="Test priority (P0, P1, P2, etc.)")
    severity: Optional[str] = Field(None, description="Severity level (Blocker, Critical, Major, Minor)")
    dataBinding: Optional[DataBinding] = Field(None, description="Data binding configuration")
    steps: List[StepIR] = Field(default_factory=list, description="Test steps")
    assertions: List[AssertionIR] = Field(default_factory=list, description="Test assertions")
    tags: List[str] = Field(default_factory=list, description="Test tags/labels")

    model_config = ConfigDict(frozen=True)
