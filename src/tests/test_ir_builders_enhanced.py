"""
test_ir_builders_enhanced.py

Unit tests for enhanced IR builders with proper schema output.
"""

import pytest
from src.ir.builder.targets_ir_builder import TargetsIRBuilder
from src.ir.builder.test_ir_builder import TestIRBuilder


class TestTargetsIRBuilder:
    """Tests for enhanced TargetsIRBuilder."""

    @pytest.fixture
    def builder(self):
        return TargetsIRBuilder()

    @pytest.fixture
    def sample_extracted_targets(self):
        """Create sample extracted targets with proper schema."""
        return [
            {
                "targetId": "LOGIN_USERNAME",
                "type": "ui-element",
                "context": {"page": "LoginPage"},
                "semantic": {"role": "textbox", "businessName": "Username Input"},
                "selectorStrategies": [
                    {"strategy": "css", "value": "#username", "stabilityScore": 0.96}
                ],
                "preferredStrategy": "css",
            },
            {
                "targetId": "LOGIN_PASSWORD",
                "type": "ui-element",
                "context": {"page": "LoginPage"},
                "semantic": {"role": "textbox", "businessName": "Password Input"},
                "selectorStrategies": [
                    {"strategy": "css", "value": "#password", "stabilityScore": 0.97}
                ],
                "preferredStrategy": "css",
            },
            {
                "targetId": "LOGIN_BUTTON",
                "type": "ui-element",
                "context": {"page": "LoginPage"},
                "semantic": {"role": "button", "businessName": "Login Button"},
                "selectorStrategies": [
                    {"strategy": "css", "value": "#login-btn", "stabilityScore": 0.94}
                ],
                "preferredStrategy": "css",
            },
        ]

    def test_targets_ir_builder_creates_target_irs(self, builder, sample_extracted_targets):
        """Test that builder creates TargetIR objects."""
        targets_ir = builder.build(sample_extracted_targets)

        assert len(targets_ir) == 3
        for target_ir in targets_ir:
            assert target_ir.targetId is not None
            assert target_ir.type == "ui-element"
            assert target_ir.context is not None
            assert target_ir.semantic is not None

    def test_targets_ir_builder_page_context(self, builder, sample_extracted_targets):
        """Test that page context is preserved."""
        targets_ir = builder.build(sample_extracted_targets)

        for target_ir in targets_ir:
            assert target_ir.context.page == "LoginPage"

    def test_targets_ir_builder_semantic_role(self, builder, sample_extracted_targets):
        """Test that semantic roles are preserved."""
        targets_ir = builder.build(sample_extracted_targets)

        username_target = next(t for t in targets_ir if t.targetId == "LOGIN_USERNAME")
        password_target = next(t for t in targets_ir if t.targetId == "LOGIN_PASSWORD")
        button_target = next(t for t in targets_ir if t.targetId == "LOGIN_BUTTON")

        assert username_target.semantic.role == "textbox"
        assert password_target.semantic.role == "textbox"
        assert button_target.semantic.role == "button"

    def test_targets_ir_builder_selector_normalization(self, builder):
        """Test selector value normalization (quote removal)."""
        targets = [
            {
                "targetId": "TEST_ELEMENT",
                "type": "ui-element",
                "context": {"page": "TestPage"},
                "semantic": {"role": "element", "businessName": "Test"},
                "selectorStrategies": [
                    {"strategy": "css", "value": '"#test-id"', "stabilityScore": 0.9}
                ],
                "preferredStrategy": "css",
            }
        ]

        targets_ir = builder.build(targets)

        # Selector should be normalized (quotes removed)
        assert targets_ir[0].selectorStrategies[0].value == "#test-id"

    def test_targets_ir_builder_stability_scores(self, builder, sample_extracted_targets):
        """Test that stability scores are valid."""
        targets_ir = builder.build(sample_extracted_targets)

        for target_ir in targets_ir:
            for strategy in target_ir.selectorStrategies:
                assert 0.0 <= strategy.stabilityScore <= 1.0


class TestTestIRBuilder:
    """Tests for enhanced TestIRBuilder."""

    @pytest.fixture
    def builder(self):
        return TestIRBuilder()

    def test_test_ir_builder_basic_structure(self, builder):
        """Test building basic TestIR."""
        test_ir = builder.build(
            test_id="TC_LOGIN_VALID_001",
            suite_id="AUTH_SUITE",
            steps=[
                {
                    "action": "navigate",
                    "target": {"type": "url", "value": "qa:/login"},
                }
            ],
        )

        assert test_ir.testId == "TC_LOGIN_VALID_001"
        assert test_ir.suiteId == "AUTH_SUITE"
        assert len(test_ir.steps) == 1

    def test_test_ir_builder_steps_with_action_types(self, builder):
        """Test building test with semantic action types."""
        steps = [
            {
                "action": "navigate",
                "target": {"type": "url", "value": "qa:/login"},
            },
            {
                "action": "type",
                "targetId": "LOGIN_USERNAME",
                "input": {"source": "data", "field": "username"},
            },
            {
                "action": "click",
                "targetId": "LOGIN_BUTTON",
            },
        ]

        test_ir = builder.build(
            test_id="TC_LOGIN_001",
            steps=steps,
        )

        assert test_ir.steps[0].action == "navigate"
        assert test_ir.steps[1].action == "type"
        assert test_ir.steps[1].targetId == "LOGIN_USERNAME"
        assert test_ir.steps[2].action == "click"
        assert test_ir.steps[2].targetId == "LOGIN_BUTTON"

    def test_test_ir_builder_step_input_data_source(self, builder):
        """Test building step with data source."""
        steps = [
            {
                "action": "type",
                "targetId": "USERNAME_INPUT",
                "input": {
                    "source": "data",
                    "field": "username",
                    "masked": False,
                },
            }
        ]

        test_ir = builder.build(test_id="TC_INPUT_001", steps=steps)

        step = test_ir.steps[0]
        assert step.input is not None
        assert step.input.source == "data"
        assert step.input.field == "username"
        assert step.input.masked == False

    def test_test_ir_builder_priority_inference(self, builder):
        """Test priority inference from test name."""
        test_ir = builder.build(
            test_id="TC_LOGIN_SMOKE_CRITICAL",
            steps=[],
        )

        assert test_ir.priority == "P0"  # Should infer from "smoke" keyword

        test_ir = builder.build(
            test_id="TC_LOGIN_VALID_001",
            steps=[],
        )

        assert test_ir.priority == "P1"  # "login" keyword

    def test_test_ir_builder_severity_inference(self, builder):
        """Test severity inference from test name."""
        test_ir = builder.build(
            test_id="TC_LOGIN_SMOKE_CRITICAL",
            steps=[],
        )

        assert test_ir.severity == "Critical"

        test_ir = builder.build(
            test_id="TC_EDGE_CASE_001",
            steps=[],
        )

        assert test_ir.severity == "Minor"

    def test_test_ir_builder_data_binding(self, builder):
        """Test building test with data binding."""
        test_ir = builder.build(
            test_id="TC_LOGIN_001",
            data_binding={
                "dataSetId": "LOGIN_DATA",
                "iterationStrategy": "row-wise",
            },
            steps=[],
        )

        assert test_ir.dataBinding is not None
        assert test_ir.dataBinding.dataSetId == "LOGIN_DATA"
        assert test_ir.dataBinding.iterationStrategy == "row-wise"

    def test_test_ir_builder_assertions(self, builder):
        """Test building test with assertions."""
        assertions = [
            {
                "assertId": "ASSERT_01",
                "type": "equals",
                "actual": {"source": "ui", "targetId": "WELCOME_MESSAGE"},
                "expected": {"source": "data", "field": "expectedMessage"},
            }
        ]

        test_ir = builder.build(
            test_id="TC_LOGIN_001",
            assertions=assertions,
            steps=[],
        )

        assert len(test_ir.assertions) == 1
        assertion = test_ir.assertions[0]
        assert assertion.type == "equals"
        assert assertion.actual.source == "ui"
        assert assertion.expected.source == "data"

    def test_test_ir_builder_backward_compatibility(self, builder):
        """Test backward compatibility with extracted_test dict."""
        extracted = {
            "name": "TC_LOGIN_001",
            "steps": [
                {
                    "action": "type",
                    "targetId": "LOGIN_USERNAME",
                }
            ],
        }

        test_ir = builder.build(extracted_test=extracted)

        assert test_ir.testId == "TC_LOGIN_001"
        assert len(test_ir.steps) == 1

    def test_test_ir_builder_step_numbering(self, builder):
        """Test that steps are numbered correctly."""
        steps = [
            {"action": "navigate", "target": {"type": "url", "value": "qa:/login"}},
            {"action": "type", "targetId": "USERNAME"},
            {"action": "click", "targetId": "BUTTON"},
        ]

        test_ir = builder.build(test_id="TC_001", steps=steps)

        for i, step in enumerate(test_ir.steps, 1):
            assert step.stepId == f"STEP_{i:02d}"

    def test_test_ir_builder_navigate_target_structure(self, builder):
        """Test that navigate step target is properly structured."""
        steps = [
            {
                "action": "navigate",
                "target": {"type": "url", "value": "qa:/login"},
            }
        ]

        test_ir = builder.build(test_id="TC_NAV_001", steps=steps)

        step = test_ir.steps[0]
        assert step.target is not None
        assert step.target.type == "url"
        assert "login" in step.target.value.lower()

    def test_test_ir_builder_complete_test(self, builder):
        """Test building a complete login test matching expected schema."""
        steps = [
            {
                "action": "navigate",
                "target": {"type": "url", "value": "qa:/login"},
            },
            {
                "action": "type",
                "targetId": "LOGIN_USERNAME",
                "input": {"source": "data", "field": "username"},
            },
            {
                "action": "type",
                "targetId": "LOGIN_PASSWORD",
                "input": {"source": "data", "field": "password", "masked": True},
            },
            {
                "action": "click",
                "targetId": "LOGIN_BUTTON",
            },
        ]

        assertions = [
            {
                "type": "equals",
                "actual": {"source": "ui", "targetId": "WELCOME_MESSAGE"},
                "expected": {"source": "data", "field": "expectedMessage"},
            }
        ]

        test_ir = builder.build(
            test_id="TC_LOGIN_VALID_001",
            suite_id="AUTH_SUITE",
            priority="P1",
            severity="Critical",
            data_binding={
                "dataSetId": "LOGIN_DATA",
                "iterationStrategy": "row-wise",
            },
            steps=steps,
            assertions=assertions,
            tags=["smoke", "auth"],
        )

        # Verify complete structure
        assert test_ir.testId == "TC_LOGIN_VALID_001"
        assert test_ir.suiteId == "AUTH_SUITE"
        assert test_ir.priority == "P1"
        assert test_ir.severity == "Critical"
        assert test_ir.dataBinding.dataSetId == "LOGIN_DATA"
        assert len(test_ir.steps) == 4
        assert len(test_ir.assertions) == 1
        assert "smoke" in test_ir.tags
