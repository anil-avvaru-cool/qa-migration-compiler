from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional


class SemanticInfo(BaseModel):
    """Semantic information about a target element."""
    role: str = Field(..., description="ARIA role or element role (e.g., button, textbox, label)")
    businessName: str = Field(..., description="Business-friendly name (e.g., 'Login Button')")

    model_config = ConfigDict(frozen=True)


class SelectorStrategy(BaseModel):
    """Alternative selector strategy for a target."""
    strategy: str = Field(..., description="Strategy type (css, xpath, id, uipath-selector, etc.)")
    value: str = Field(..., description="Selector value/expression")
    stabilityScore: float = Field(default=0.9, description="Stability score (0.0-1.0)")

    model_config = ConfigDict(frozen=True)


class TargetContext(BaseModel):
    """Context where the target is located."""
    page: Optional[str] = Field(None, description="Page/screen name (e.g., LoginPage)")
    component: Optional[str] = Field(None, description="Component name if nested")
    frame: Optional[str] = Field(None, description="Frame name if in iframe")

    model_config = ConfigDict(frozen=True)


class TargetIR(BaseModel):
    """Enhanced Target IR model with multiple selector strategies."""
    targetId: str = Field(..., description="Unique target identifier")
    type: str = Field(default="ui-element", description="Target type (ui-element, api-endpoint, data-field)")
    context: TargetContext = Field(default_factory=TargetContext, description="Context/location of target")
    semantic: SemanticInfo = Field(..., description="Semantic information for accessibility")
    selectorStrategies: List[SelectorStrategy] = Field(default_factory=list, description="List of selector strategies")
    preferredStrategy: str = Field(default="css", description="Preferred selector strategy")

    model_config = ConfigDict(frozen=True)
