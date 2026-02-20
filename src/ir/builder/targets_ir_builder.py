import logging
from typing import Dict, List

from src.ir.models.targets import TargetIR
from src.utils.hashing import deterministic_hash


logger = logging.getLogger(__name__)


class TargetsIRBuilder:
    """
    Builds TargetIR objects from extracted targets.
    """

    def build(self, extracted_targets: List[Dict]) -> List[TargetIR]:
        logger.info("Building TargetIR list")

        targets_ir: List[TargetIR] = []

        for target in extracted_targets:
            target_id = deterministic_hash(
                f"target::{target['type']}::{target['name']}"
            )

            target_ir = TargetIR(
                id=target_id,
                name=target["name"],
                type=target["type"],
                locator=target.get("locator"),
                metadata=target.get("metadata")
            )

            targets_ir.append(target_ir)

        logger.info("Finished building %d TargetIR objects", len(targets_ir))
        return targets_ir
