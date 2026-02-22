import logging
from typing import Dict, List, Optional

from src.ir.models.test import (
    TestIR,
    StepIR,
    StepInput,
    StepTarget,
    AssertionIR,
    DataBinding,
    DataSource,
)


logger = logging.getLogger(__name__)


class TestIRBuilder:
    """
    Builds TestIR from extracted test domain model with enhanced schema.
    """

    def build(
        self,
        test_id: Optional[str] = None,
        steps: Optional[List[Dict]] = None,
        suite_id: Optional[str] = None,
        priority: Optional[str] = None,
        severity: Optional[str] = None,
        data_binding: Optional[Dict] = None,
        assertions: Optional[List[Dict]] = None,
        tags: Optional[List[str]] = None,
        extracted_test: Optional[Dict] = None,
        target_name_to_id: Optional[Dict[str, str]] = None,
    ) -> TestIR:
        """
        Build TestIR with enhanced schema.
        
        Supports two calling patterns:
        1. Direct: build(test_id="T1", steps=[...], suite_id="S1", target_name_to_id={...})
        2. Backward-compatible: build(extracted_test={"name": "T1", "steps": [...]})
        3. Positional dict: build({"name": "T1", "steps": [...]})
        
        Args:
            test_id: Unique test identifier
            steps: List of step dicts
            suite_id: Parent suite ID
            priority: Test priority (P0, P1, P2, etc.)
            severity: Severity level (Blocker, Critical, Major, Minor)
            data_binding: Data binding configuration dict
            assertions: List of assertion dicts
            tags: List of test tags
            extracted_test: Optional extracted test dict (for backward compatibility)
            target_name_to_id: Optional mapping of target names to target IDs
        """
        # Handle backward compatibility: if test_id is a dict, treat it as extracted_test
        if isinstance(test_id, dict):
            extracted_test = test_id
            test_id = None
            steps = None
        
        logger.info("Building TestIR for test: %s", test_id)

        # Support backward compatibility with extracted_test
        if extracted_test:
            test_id = extracted_test.get("id") or extracted_test.get("name") or test_id
            steps = extracted_test.get("steps", steps or [])
            suite_id = extracted_test.get("suite_id", suite_id)
            priority = extracted_test.get("priority", priority)
            severity = extracted_test.get("severity", severity)
            data_binding = extracted_test.get("data_binding", data_binding)
            assertions = extracted_test.get("assertions", assertions)
            tags = extracted_test.get("tags", tags or [])

        # Ensure steps is a list
        steps = steps or []
        target_name_to_id = target_name_to_id or {}
        
        # Build steps
        step_irs: List[StepIR] = []
        for step in steps:
            step_input = None
            if step.get("input"):
                step_input = StepInput(
                    source=step["input"].get("source", "constant"),
                    field=step["input"].get("field"),
                    masked=step["input"].get("masked", False),
                )

            step_target = None
            if step.get("target"):
                step_target = StepTarget(
                    type=step["target"].get("type", "element"),
                    value=step["target"].get("value"),
                )

            # Resolve targetId: try direct targetId first, then use target_name_to_id mapping
            target_id = step.get("targetId")
            if not target_id and step.get("target_name_id"):
                # Map extracted target_name_id to actual targetId using the mapping
                target_id = target_name_to_id.get(step.get("target_name_id"))

            step_ir = StepIR(
                stepId=step.get("stepId", f"STEP_{len(step_irs) + 1:02d}"),
                action=step.get("action", "generic"),
                targetId=target_id,
                target=step_target,
                input=step_input,
                parameters=step.get("parameters", {}),
            )
            step_irs.append(step_ir)

        # Build assertions
        assertion_irs: List[AssertionIR] = []
        if assertions:
            for assertion in assertions:
                actual_src = assertion.get("actual", {})
                expected_src = assertion.get("expected", {})

                assertion_ir = AssertionIR(
                    assertId=assertion.get("assertId", f"ASSERT_{len(assertion_irs) + 1:02d}"),
                    type=assertion.get("type", "equals"),
                    actual=DataSource(
                        source=actual_src.get("source", "ui"),
                        field=actual_src.get("field"),
                        targetId=actual_src.get("targetId"),
                        value=actual_src.get("value"),
                        masked=actual_src.get("masked", False),
                    ),
                    expected=DataSource(
                        source=expected_src.get("source", "constant"),
                        field=expected_src.get("field"),
                        targetId=expected_src.get("targetId"),
                        value=expected_src.get("value"),
                        masked=expected_src.get("masked", False),
                    ),
                )
                assertion_irs.append(assertion_ir)

        # Build data binding
        data_binding_ir = None
        if data_binding:
            data_binding_ir = DataBinding(
                dataSetId=data_binding.get("dataSetId"),
                iterationStrategy=data_binding.get("iterationStrategy", "row-wise"),
            )

        test_ir = TestIR(
            testId=test_id,
            suiteId=suite_id,
            priority=priority,
            severity=severity,
            dataBinding=data_binding_ir,
            steps=step_irs,
            assertions=assertion_irs,
            tags=tags or [],
        )

        logger.info("Finished building TestIR: %s", test_id)
        return test_ir
