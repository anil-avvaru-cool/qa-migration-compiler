import logging
from typing import Dict, List

from src.ir.models.test import TestIR, StepIR
from src.utils.hashing import deterministic_hash


logger = logging.getLogger(__name__)


class TestIRBuilder:
    """
    Builds TestIR from extracted test domain model.
    Responsibility: pure transformation only.
    """

    def build(self, extracted_test: Dict, suite_id: str | None = None, target_name_to_id: Dict[str, str] | None = None) -> TestIR:
        logger.info("Building TestIR for test: %s", extracted_test.get("name"))

        test_name = extracted_test["name"]
        test_id = deterministic_hash(f"test::{test_name}")

        steps: List[StepIR] = []
        for index, step in enumerate(extracted_test.get("steps", [])):
            step_id = deterministic_hash(f"{test_id}::step::{index}::{step['name']}")

            # Resolve target id using provided mapping if possible
            target_name = step.get("target_name_id") or step.get("target")
            target_id = None
            if target_name and target_name_to_id:
                target_id = target_name_to_id.get(target_name)

            step_ir = StepIR(
                id=step_id,
                type=step["type"],
                name=step["name"],
                targetId=target_id,
                targetNameId=step.get("target_name_id"),
                targetNodeId=step.get("target_node_id"),
                parameters=step.get("parameters", {})
            )
            steps.append(step_ir)

        test_ir = TestIR(
            id=test_id,
            name=test_name,
            suite_id=suite_id,
            environment_id=extracted_test.get("environment_id"),
            data_id=extracted_test.get("data_id"),
            tags=extracted_test.get("tags", []),
            steps=steps
        )

        logger.info("Finished building TestIR: %s", test_id)
        return test_ir
