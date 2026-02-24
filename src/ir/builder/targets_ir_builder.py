import logging
from typing import Dict, List, Optional

from src.ir.models.targets import (
    TargetIR,
    TargetContext,
    SemanticInfo,
    SelectorStrategy,
)


logger = logging.getLogger(__name__)


class TargetsIRBuilder:
    """
    Builds TargetIR objects with enhanced schema support.
    
    Converts extracted targets to IR with proper:
    - page context from source class
    - semantic role inference
    - selector normalization
    - stability scores
    - multiple selector strategies
    """

    def build(self, extracted_targets: List[Dict]) -> List[TargetIR]:
        """
        Build list of TargetIR objects from extracted targets.
        
        Args:
            extracted_targets: List of extracted target dicts with:
                - targetId: unique identifier
                - type: "ui-element"
                - context: {page, component, frame}
                - semantic: {role, businessName}
                - selectorStrategies: list of strategies with stability scores
                - preferredStrategy: preferred selector type
        
        Returns:
            List of TargetIR objects matching expected schema
        """
        logger.info("Building TargetIR list from %d extracted targets", len(extracted_targets))

        targets_ir: List[TargetIR] = []

        for target in extracted_targets:
            target_ir = self._build_single_target(target)
            if target_ir:
                targets_ir.append(target_ir)

        logger.info("Built %d TargetIR objects", len(targets_ir))
        return targets_ir

    def _build_single_target(self, target: Dict) -> Optional[TargetIR]:
        """Build a single TargetIR object."""

        # Validate required fields
        target_id = target.get("targetId") or target.get("id")
        if not target_id:
            logger.warning("Target missing targetId: %s", target)
            return None

        # Build context with proper structure
        context_data = target.get("context", {})
        context = TargetContext(
            page=context_data.get("page"),
            component=context_data.get("component"),
            frame=context_data.get("frame"),
        )

        # Build semantic info
        semantic_data = target.get("semantic", {})
        if not semantic_data.get("role"):
            semantic_data["role"] = "element"  # Fallback
        if not semantic_data.get("businessName"):
            semantic_data["businessName"] = target_id

        semantic = SemanticInfo(
            role=semantic_data.get("role"),
            businessName=semantic_data.get("businessName"),
        )

        # Build selector strategies - normalize and deduplicate
        strategies_data = target.get("selectorStrategies", [])
        if not strategies_data and target.get("locator"):
            # Backward compatibility: create strategy from single locator
            strategies_data = [
                {
                    "strategy": "css",
                    "value": target.get("locator"),
                    "stabilityScore": 0.85,
                }
            ]

        strategies = self._build_selector_strategies(strategies_data)

        # Get preferred strategy, default to first or "css"
        preferred = target.get("preferredStrategy", "css")
        if not any(s.strategy == preferred for s in strategies):
            preferred = strategies[0].strategy if strategies else "css"

        # Build TargetIR
        target_ir = TargetIR(
            targetId=target_id,
            type=target.get("type", "ui-element"),
            context=context,
            semantic=semantic,
            selectorStrategies=strategies,
            preferredStrategy=preferred,
        )

        logger.debug("Built TargetIR: %s", target_id)
        return target_ir

    def _build_selector_strategies(self, strategies_data: List[Dict]) -> List[SelectorStrategy]:
        """
        Build normalized selector strategies.
        
        Ensures:
        - No duplicate strategies
        - Proper stability scores (0.0 - 1.0)
        - Clean selector values (no extra quotes)
        """
        seen = set()
        strategies = []

        for s in strategies_data:
            strategy_type = s.get("strategy", "css")
            value = s.get("value", "")

            # Normalize value (remove extra quotes)
            value = self._normalize_selector_value(value)

            if not value:
                continue

            # Skip duplicates
            key = (strategy_type, value)
            if key in seen:
                continue
            seen.add(key)

            # Normalize stability score
            stability = float(s.get("stabilityScore", 0.85))
            stability = max(0.0, min(1.0, stability))

            strategies.append(
                SelectorStrategy(
                    strategy=strategy_type,
                    value=value,
                    stabilityScore=stability,
                )
            )

        return strategies

    def _normalize_selector_value(self, value: str) -> str:
        """Normalize selector value by removing extra quotes."""
        if not value:
            return ""

        value = str(value).strip()

        # Remove wrapping quotes
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]

        # Remove escaped quotes
        value = value.replace('\\"', '"').replace("\\'", "'")
        value = value.strip()

        return value
