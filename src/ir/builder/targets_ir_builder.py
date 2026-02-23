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
    Builds TargetIR objects with multiple selector strategies.
    """

    def build(self, extracted_targets: List[Dict]) -> List[TargetIR]:
        """
        Build list of TargetIR objects from extracted targets.
        
        Args:
            extracted_targets: List of extracted target dicts
        
        Returns:
            List of TargetIR objects
        """
        logger.info("Building TargetIR list")

        targets_ir: List[TargetIR] = []

        for target in extracted_targets:
            target_id = target.get("targetId") or target.get("id")
            if not target_id:
                raise ValueError(f"Target must have targetId or id: {target}")

            # Build context
            context = TargetContext(
                page=target.get("context", {}).get("page"),
                component=target.get("context", {}).get("component"),
                frame=target.get("context", {}).get("frame"),
            )

            # Build semantic info
            semantic_data = target.get("semantic", {})
            if not semantic_data.get("role") or not semantic_data.get("businessName"):
                # Fallback for backward compatibility
                semantic_data = {
                    "role": semantic_data.get("role", "element"),
                    "businessName": semantic_data.get("businessName", target.get("name", target_id)),
                }

            semantic = SemanticInfo(
                role=semantic_data["role"],
                businessName=semantic_data["businessName"],
            )

            # Build selector strategies
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

            strategies = [
                SelectorStrategy(
                    strategy=s.get("strategy", "css"),
                    value=s.get("value", ""),
                    stabilityScore=float(s.get("stabilityScore", 0.85)),
                )
                for s in strategies_data
            ]

            preferred = target.get("preferredStrategy", "css")

            target_ir = TargetIR(
                targetId=target_id,
                type=target.get("type", "ui-element"),
                context=context,
                semantic=semantic,
                selectorStrategies=strategies,
                preferredStrategy=preferred,
            )

            targets_ir.append(target_ir)

        logger.info("Finished building %d TargetIR objects", len(targets_ir))
        return targets_ir
