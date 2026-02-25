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
    Builds TestIR from extracted and enriched test data with proper schema.
    
    Handles:
    - Semantic action types (navigate, type, click, etc.)
    - Target ID linking to targets.json
    - Data source binding (data fields, constants, UI elements)
    - Input/output specifications
    - Assertions extraction
    - Priority/severity assignment
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
        Build TestIR with proper schema.
        
        Args:
            test_id: Unique test identifier
            steps: List of enriched step dicts with action, targetId, input
            suite_id: Parent suite ID
            priority: Test priority (P0, P1, P2, etc.)
            severity: Severity level (Blocker, Critical, Major, Minor)
            data_binding: Data binding configuration dict
            assertions: List of assertion dicts
            tags: List of test tags
            extracted_test: Optional extracted test dict (backward compatibility)
            target_name_to_id: Optional mapping of target names to target IDs
        """
        # Handle backward compatibility: if test_id is a dict, treat as extracted_test
        if isinstance(test_id, dict):
            extracted_test = test_id
            test_id = None
            steps = None

        logger.info("Building TestIR for test: %s", test_id)

        # Support backward compatibility with extracted_test
        if extracted_test:
            test_id = extracted_test.get("id") or extracted_test.get("name") or extracted_test.get("testId") or test_id
            steps = extracted_test.get("steps", steps or [])
            suite_id = extracted_test.get("suite_id") or extracted_test.get("suiteId") or suite_id
            priority = extracted_test.get("priority", priority)
            severity = extracted_test.get("severity", severity)
            data_binding = extracted_test.get("data_binding") or extracted_test.get("dataBinding") or data_binding
            assertions = extracted_test.get("assertions", assertions)
            tags = extracted_test.get("tags", tags or [])

        # Ensure steps is a list
        steps = steps or []
        target_name_to_id = target_name_to_id or {}

        # Assign default priority/severity based on suite or method name
        if not priority:
            priority = self._infer_priority(test_id, suite_id)
        if not severity:
            severity = self._infer_severity(test_id, suite_id)

        # Build steps with proper StepIR structure
        step_irs: List[StepIR] = []
        for i, step in enumerate(steps, 1):
            step_ir = self._build_step(step, i, target_name_to_id)
            if step_ir:
                step_irs.append(step_ir)

        # Build assertions
        assertion_irs: List[AssertionIR] = []
        if assertions:
            for i, assertion in enumerate(assertions, 1):
                assertion_ir = self._build_assertion(assertion, i)
                if assertion_ir:
                    assertion_irs.append(assertion_ir)

        # Build data binding
        data_binding_ir = None
        if data_binding:
            data_binding_ir = DataBinding(
                dataSetId=data_binding.get("dataSetId"),
                iterationStrategy=data_binding.get("iterationStrategy", "row-wise"),
            )

        # Build TestIR
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

    def _build_step(self, step: Dict, step_index: int, target_name_to_id: Dict[str, str]) -> Optional[StepIR]:
        """Build a single StepIR object."""

        # Extract step components
        # Backward-compatible: older extraction used 'name' for the action verb
        action = step.get("action") or step.get("name") or "generic"
        step_id = step.get("stepId") or f"STEP_{step_index:02d}"

        # Resolve targetId
        target_id = step.get("targetId")
        if not target_id and step.get("target_name_id"):
            # Try mapping via provided name->id map, otherwise fall back to using
            # the name directly (backward compatibility for tests using simple
            # names as IDs).
            target_id = target_name_to_id.get(step["target_name_id"]) or step.get("target_name_id")

        # Build step input
        step_input = None
        if step.get("input"):
            input_data = step["input"]
            step_input = StepInput(
                source=input_data.get("source", "constant"),
                field=input_data.get("field"),
                masked=input_data.get("masked", False),
            )

        # Build step target (for navigation)
        step_target = None
        if step.get("target"):
            target_data = step["target"]
            step_target = StepTarget(
                type=target_data.get("type", "element"),
                value=target_data.get("value"),
            )

        # Create StepIR
        step_ir = StepIR(
            stepId=step_id,
            action=action,
            targetId=target_id,
            target=step_target,
            input=step_input,
            parameters=step.get("parameters", {}),
        )

        return step_ir

    def _build_assertion(self, assertion: Dict, assertion_index: int) -> Optional[AssertionIR]:
        """Build a single AssertionIR object."""

        assertion_id = assertion.get("assertId") or f"ASSERT_{assertion_index:02d}"
        assertion_type = assertion.get("type", "equals")

        # Build actual datasource
        actual_data = assertion.get("actual", {})
        actual = DataSource(
            source=actual_data.get("source", "ui"),
            field=actual_data.get("field"),
            targetId=actual_data.get("targetId"),
            value=actual_data.get("value"),
            masked=actual_data.get("masked", False),
        )

        # Build expected datasource
        expected_data = assertion.get("expected", {})
        expected = DataSource(
            source=expected_data.get("source", "constant"),
            field=expected_data.get("field"),
            targetId=expected_data.get("targetId"),
            value=expected_data.get("value"),
            masked=expected_data.get("masked", False),
        )

        # Create AssertionIR
        assertion_ir = AssertionIR(
            assertId=assertion_id,
            type=assertion_type,
            actual=actual,
            expected=expected,
        )

        return assertion_ir

    def _infer_priority(self, test_id: Optional[str], suite_id: Optional[str]) -> str:
        """
        Infer test priority from test ID or suite.
        
        Patterns:
        - *Smoke*, *Critical* → P0
        - *Login*, *Auth* → P1
        - *Edge*, *Corner* → P2
        Default: P1
        """
        if not test_id:
            return "P1"

        test_lower = test_id.lower()

        if any(kw in test_lower for kw in ["smoke", "critical", "core", "essential"]):
            return "P0"
        elif any(kw in test_lower for kw in ["login", "auth", "valid"]):
            return "P1"
        elif any(kw in test_lower for kw in ["edge", "corner", "boundary", "invalid"]):
            return "P2"

        return "P1"

    def _infer_severity(self, test_id: Optional[str], suite_id: Optional[str]) -> str:
        """
        Infer test severity from test ID or suite.
        
        Patterns:
        - *Smoke*, *Critical*, *Login*, *Auth* → Critical
        - General tests → Major
        - *Edge*, *Corner* → Minor
        """
        if not test_id:
            return "Major"

        test_lower = test_id.lower()

        if any(kw in test_lower for kw in ["smoke", "critical", "core", "login", "auth", "payment"]):
            return "Critical"
        elif any(kw in test_lower for kw in ["edge", "corner", "boundary", "negative"]):
            return "Minor"

        return "Major"
