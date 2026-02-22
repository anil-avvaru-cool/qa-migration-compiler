"""
Unit tests for enhanced IR models with new JSON schema.

Tests cover:
- Project IR with version, frameworks, architecture
- Environment IR with timeouts, retry policy, browsers
- Target IR with selector strategies and stability scores
- Test IR with steps, assertions, and data binding
- Suite IR with descriptions
- Data IR for datasets
"""

import unittest
from datetime import datetime

from src.ir.models.project import ProjectIR
from src.ir.models.environment import (
    EnvironmentIR,
    TimeoutConfig,
    RetryPolicy,
)
from src.ir.models.targets import (
    TargetIR,
    TargetContext,
    SemanticInfo,
    SelectorStrategy,
)
from src.ir.models.data import TestDataIR
from src.ir.models.test import (
    TestIR,
    StepIR,
    StepInput,
    StepTarget,
    AssertionIR,
    DataBinding,
    DataSource,
)
from src.ir.models.suite import SuiteIR


class TestProjectIR(unittest.TestCase):
    """Test ProjectIR model."""

    def test_project_ir_creation(self):
        """Test creating a ProjectIR object."""
        project = ProjectIR(
            projectName="EcommerceAutomation",
            sourceFramework="Selenium-Java-TestNG",
            targetFramework="Playwright-TS",
            architecturePattern="POM",
            supportsParallel=True,
            createdOn="2026-02-12",
        )

        self.assertEqual(project.projectName, "EcommerceAutomation")
        self.assertEqual(project.sourceFramework, "Selenium-Java-TestNG")
        self.assertEqual(project.targetFramework, "Playwright-TS")
        self.assertEqual(project.architecturePattern, "POM")
        self.assertTrue(project.supportsParallel)
        self.assertEqual(project.irVersion, "2.0.0")

    def test_project_ir_json_serialization(self):
        """Test ProjectIR serializes to valid JSON."""
        project = ProjectIR(
            projectName="TestProject",
            sourceFramework="Selenium-Java",
            targetFramework="Playwright-Python",
            createdOn="2026-02-22",
        )

        json_output = project.model_dump_json()
        self.assertIn("TestProject", json_output)
        self.assertIn("2.0.0", json_output)
        self.assertIn("Selenium-Java", json_output)

    def test_project_ir_dict_serialization(self):
        """Test ProjectIR converts to dict correctly."""
        project = ProjectIR(
            projectName="DictTest",
            sourceFramework="Selenium-Java-TestNG",
            targetFramework="Playwright-TS",
            createdOn="2026-02-22",
        )

        result_dict = project.model_dump()
        self.assertEqual(result_dict["projectName"], "DictTest")
        self.assertEqual(result_dict["irVersion"], "2.0.0")


class TestEnvironmentIR(unittest.TestCase):
    """Test EnvironmentIR model."""

    def test_timeout_config_creation(self):
        """Test creating TimeoutConfig."""
        timeouts = TimeoutConfig(
            implicit=5000,
            explicit=10000,
            pageLoad=30000,
        )

        self.assertEqual(timeouts.implicit, 5000)
        self.assertEqual(timeouts.explicit, 10000)
        self.assertEqual(timeouts.pageLoad, 30000)

    def test_retry_policy_creation(self):
        """Test creating RetryPolicy."""
        policy = RetryPolicy(enabled=True, maxRetries=2)

        self.assertTrue(policy.enabled)
        self.assertEqual(policy.maxRetries, 2)

    def test_environment_ir_creation(self):
        """Test creating EnvironmentIR object."""
        env = EnvironmentIR(
            baseUrls={"qa": "https://qa.example.com"},
            executionMode="parallel",
            browsers=["chrome", "firefox"],
            timeouts=TimeoutConfig(),
            retryPolicy=RetryPolicy(),
        )

        self.assertEqual(env.baseUrls["qa"], "https://qa.example.com")
        self.assertEqual(env.executionMode, "parallel")
        self.assertIn("chrome", env.browsers)

    def test_environment_ir_json_serialization(self):
        """Test EnvironmentIR serializes to JSON."""
        env = EnvironmentIR(
            baseUrls={"qa": "https://qa.example.com"},
            executionMode="parallel",
            browsers=["chrome"],
        )

        json_output = env.model_dump_json()
        self.assertIn("qa.example.com", json_output)
        self.assertIn("parallel", json_output)


class TestTargetIR(unittest.TestCase):
    """Test TargetIR model with selector strategies."""

    def test_semantic_info_creation(self):
        """Test creating SemanticInfo."""
        semantic = SemanticInfo(
            role="textbox",
            businessName="Username Input",
        )

        self.assertEqual(semantic.role, "textbox")
        self.assertEqual(semantic.businessName, "Username Input")

    def test_selector_strategy_creation(self):
        """Test creating SelectorStrategy."""
        strategy = SelectorStrategy(
            strategy="css",
            value="#username",
            stabilityScore=0.96,
        )

        self.assertEqual(strategy.strategy, "css")
        self.assertEqual(strategy.value, "#username")
        self.assertEqual(strategy.stabilityScore, 0.96)

    def test_target_context_creation(self):
        """Test creating TargetContext."""
        context = TargetContext(page="LoginPage", component=None)

        self.assertEqual(context.page, "LoginPage")
        self.assertIsNone(context.component)

    def test_target_ir_creation(self):
        """Test creating TargetIR object."""
        target = TargetIR(
            targetId="LOGIN_USERNAME",
            type="ui-element",
            context=TargetContext(page="LoginPage"),
            semantic=SemanticInfo(
                role="textbox",
                businessName="Username Input",
            ),
            selectorStrategies=[
                SelectorStrategy(
                    strategy="css",
                    value="#username",
                    stabilityScore=0.96,
                ),
                SelectorStrategy(
                    strategy="xpath",
                    value="//input[@id='username']",
                    stabilityScore=0.88,
                ),
            ],
            preferredStrategy="css",
        )

        self.assertEqual(target.targetId, "LOGIN_USERNAME")
        self.assertEqual(len(target.selectorStrategies), 2)
        self.assertEqual(target.preferredStrategy, "css")

    def test_target_ir_json_serialization(self):
        """Test TargetIR serializes correctly."""
        target = TargetIR(
            targetId="LOGIN_BUTTON",
            type="ui-element",
            context=TargetContext(page="LoginPage"),
            semantic=SemanticInfo(
                role="button",
                businessName="Login Button",
            ),
            selectorStrategies=[
                SelectorStrategy(
                    strategy="css",
                    value="#login-btn",
                    stabilityScore=0.94,
                )
            ],
        )

        json_output = target.model_dump_json()
        self.assertIn("LOGIN_BUTTON", json_output)
        self.assertIn("login-btn", json_output)
        self.assertIn("0.94", json_output)


class TestTestDataIR(unittest.TestCase):
    """Test TestDataIR model."""

    def test_test_data_ir_creation(self):
        """Test creating TestDataIR object."""
        data = TestDataIR(
            dataSetId="LOGIN_DATA",
            type="inline",
            records=[
                {
                    "username": "testuser1",
                    "password": "Password123",
                    "expectedMessage": "Welcome testuser1",
                }
            ],
        )

        self.assertEqual(data.dataSetId, "LOGIN_DATA")
        self.assertEqual(data.type, "inline")
        self.assertEqual(len(data.records), 1)
        self.assertEqual(data.records[0]["username"], "testuser1")

    def test_test_data_ir_multiple_records(self):
        """Test TestDataIR with multiple records."""
        data = TestDataIR(
            dataSetId="ORDER_DATA",
            type="inline",
            records=[
                {"productName": "Laptop", "expectedConfirmation": "Order placed successfully"},
                {
                    "productName": "Mouse",
                    "expectedConfirmation": "Order placed successfully",
                },
            ],
        )

        self.assertEqual(len(data.records), 2)


class TestStepAndAssertionIR(unittest.TestCase):
    """Test StepIR and AssertionIR models."""

    def test_step_input_creation(self):
        """Test creating StepInput."""
        step_input = StepInput(
            source="data",
            field="username",
            masked=False,
        )

        self.assertEqual(step_input.source, "data")
        self.assertEqual(step_input.field, "username")
        self.assertFalse(step_input.masked)

    def test_step_target_creation(self):
        """Test creating StepTarget."""
        target = StepTarget(
            type="url",
            value="qa:/login",
        )

        self.assertEqual(target.type, "url")
        self.assertEqual(target.value, "qa:/login")

    def test_step_ir_creation(self):
        """Test creating StepIR object."""
        step = StepIR(
            stepId="STEP_01",
            action="type",
            targetId="LOGIN_USERNAME",
            input=StepInput(
                source="data",
                field="username",
            ),
        )

        self.assertEqual(step.stepId, "STEP_01")
        self.assertEqual(step.action, "type")
        self.assertEqual(step.targetId, "LOGIN_USERNAME")

    def test_step_with_navigate_action(self):
        """Test StepIR with navigate action."""
        step = StepIR(
            stepId="STEP_01",
            action="navigate",
            target=StepTarget(type="url", value="qa:/login"),
        )

        self.assertEqual(step.action, "navigate")
        self.assertEqual(step.target.value, "qa:/login")

    def test_data_source_creation(self):
        """Test creating DataSource."""
        source = DataSource(
            source="data",
            field="expectedMessage",
        )

        self.assertEqual(source.source, "data")
        self.assertEqual(source.field, "expectedMessage")

    def test_assertion_ir_creation(self):
        """Test creating AssertionIR object."""
        assertion = AssertionIR(
            assertId="ASSERT_01",
            type="equals",
            actual=DataSource(
                source="ui",
                targetId="WELCOME_MESSAGE",
            ),
            expected=DataSource(
                source="data",
                field="expectedMessage",
            ),
        )

        self.assertEqual(assertion.assertId, "ASSERT_01")
        self.assertEqual(assertion.type, "equals")
        self.assertEqual(assertion.actual.source, "ui")
        self.assertEqual(assertion.expected.source, "data")


class TestDataBindingAndTestIR(unittest.TestCase):
    """Test DataBinding and TestIR models."""

    def test_data_binding_creation(self):
        """Test creating DataBinding."""
        binding = DataBinding(
            dataSetId="LOGIN_DATA",
            iterationStrategy="row-wise",
        )

        self.assertEqual(binding.dataSetId, "LOGIN_DATA")
        self.assertEqual(binding.iterationStrategy, "row-wise")

    def test_test_ir_creation_basic(self):
        """Test creating basic TestIR object."""
        test = TestIR(
            testId="TC_LOGIN_VALID_001",
            suiteId="AUTH_SUITE",
            priority="P1",
            severity="Critical",
        )

        self.assertEqual(test.testId, "TC_LOGIN_VALID_001")
        self.assertEqual(test.suiteId, "AUTH_SUITE")
        self.assertEqual(test.priority, "P1")
        self.assertEqual(test.severity, "Critical")

    def test_test_ir_with_steps_and_assertions(self):
        """Test creating TestIR with steps and assertions."""
        test = TestIR(
            testId="TC_LOGIN_VALID_001",
            suiteId="AUTH_SUITE",
            priority="P1",
            severity="Critical",
            dataBinding=DataBinding(
                dataSetId="LOGIN_DATA",
                iterationStrategy="row-wise",
            ),
            steps=[
                StepIR(
                    stepId="STEP_01",
                    action="navigate",
                    target=StepTarget(type="url", value="qa:/login"),
                ),
                StepIR(
                    stepId="STEP_02",
                    action="type",
                    targetId="LOGIN_USERNAME",
                    input=StepInput(
                        source="data",
                        field="username",
                    ),
                ),
                StepIR(
                    stepId="STEP_03",
                    action="type",
                    targetId="LOGIN_PASSWORD",
                    input=StepInput(
                        source="data",
                        field="password",
                        masked=True,
                    ),
                ),
            ],
            assertions=[
                AssertionIR(
                    assertId="ASSERT_01",
                    type="equals",
                    actual=DataSource(
                        source="ui",
                        targetId="WELCOME_MESSAGE",
                    ),
                    expected=DataSource(
                        source="data",
                        field="expectedMessage",
                    ),
                )
            ],
        )

        self.assertEqual(len(test.steps), 3)
        self.assertEqual(len(test.assertions), 1)
        self.assertIsNotNone(test.dataBinding)
        self.assertEqual(test.dataBinding.dataSetId, "LOGIN_DATA")

    def test_test_ir_json_serialization(self):
        """Test TestIR serializes to JSON."""
        test = TestIR(
            testId="TC_TEST_001",
            suiteId="TEST_SUITE",
            steps=[
                StepIR(
                    stepId="STEP_01",
                    action="click",
                    targetId="BUTTON_01",
                )
            ],
        )

        json_output = test.model_dump_json()
        self.assertIn("TC_TEST_001", json_output)
        self.assertIn("STEP_01", json_output)


class TestSuiteIR(unittest.TestCase):
    """Test SuiteIR model."""

    def test_suite_ir_creation(self):
        """Test creating SuiteIR object."""
        suite = SuiteIR(
            suiteId="AUTH_SUITE",
            description="Authentication Tests",
            tests=["TC_LOGIN_VALID_001"],
        )

        self.assertEqual(suite.suiteId, "AUTH_SUITE")
        self.assertEqual(suite.description, "Authentication Tests")
        self.assertIn("TC_LOGIN_VALID_001", suite.tests)

    def test_suite_ir_multiple_tests(self):
        """Test SuiteIR with multiple tests."""
        suite = SuiteIR(
            suiteId="ORDER_SUITE",
            description="Order Tests",
            tests=["TC_ORDER_CREATE_001", "TC_ORDER_CANCEL_002"],
        )

        self.assertEqual(len(suite.tests), 2)

    def test_suite_ir_json_serialization(self):
        """Test SuiteIR serializes correctly."""
        suite = SuiteIR(
            suiteId="TEST_SUITE",
            description="Test Suite",
            tests=["TC_001"],
        )

        json_output = suite.model_dump_json()
        self.assertIn("TEST_SUITE", json_output)
        self.assertIn("Test Suite", json_output)


class TestComplexScenarios(unittest.TestCase):
    """Test complex IR scenarios."""

    def test_e_commerce_login_test(self):
        """Test full e-commerce login test structure."""
        test = TestIR(
            testId="TC_LOGIN_VALID_001",
            suiteId="AUTH_SUITE",
            priority="P1",
            severity="Critical",
            dataBinding=DataBinding(
                dataSetId="LOGIN_DATA",
                iterationStrategy="row-wise",
            ),
            steps=[
                StepIR(
                    stepId="STEP_01",
                    action="navigate",
                    target=StepTarget(type="url", value="qa:/login"),
                ),
                StepIR(
                    stepId="STEP_02",
                    action="type",
                    targetId="LOGIN_USERNAME",
                    input=StepInput(source="data", field="username"),
                ),
                StepIR(
                    stepId="STEP_03",
                    action="type",
                    targetId="LOGIN_PASSWORD",
                    input=StepInput(
                        source="data",
                        field="password",
                        masked=True,
                    ),
                ),
                StepIR(
                    stepId="STEP_04",
                    action="click",
                    targetId="LOGIN_BUTTON",
                ),
                StepIR(
                    stepId="STEP_05",
                    action="waitForVisible",
                    targetId="WELCOME_MESSAGE",
                ),
            ],
            assertions=[
                AssertionIR(
                    assertId="ASSERT_01",
                    type="equals",
                    actual=DataSource(
                        source="ui",
                        targetId="WELCOME_MESSAGE",
                    ),
                    expected=DataSource(
                        source="data",
                        field="expectedMessage",
                    ),
                )
            ],
        )

        self.assertEqual(len(test.steps), 5)
        self.assertEqual(test.steps[0].action, "navigate")
        self.assertEqual(test.steps[1].action, "type")
        self.assertEqual(len(test.assertions), 1)

    def test_target_repository_structure(self):
        """Test target repository with multiple targets."""
        targets = [
            TargetIR(
                targetId="LOGIN_USERNAME",
                type="ui-element",
                context=TargetContext(page="LoginPage"),
                semantic=SemanticInfo(
                    role="textbox",
                    businessName="Username Input",
                ),
                selectorStrategies=[
                    SelectorStrategy(
                        strategy="css",
                        value="#username",
                        stabilityScore=0.96,
                    ),
                    SelectorStrategy(
                        strategy="xpath",
                        value="//input[@id='username']",
                        stabilityScore=0.88,
                    ),
                ],
                preferredStrategy="css",
            ),
            TargetIR(
                targetId="LOGIN_PASSWORD",
                type="ui-element",
                context=TargetContext(page="LoginPage"),
                semantic=SemanticInfo(
                    role="textbox",
                    businessName="Password Input",
                ),
                selectorStrategies=[
                    SelectorStrategy(
                        strategy="css",
                        value="#password",
                        stabilityScore=0.97,
                    )
                ],
                preferredStrategy="css",
            ),
        ]

        self.assertEqual(len(targets), 2)
        self.assertEqual(targets[0].targetId, "LOGIN_USERNAME")
        self.assertEqual(targets[0].semantic.businessName, "Username Input")


if __name__ == "__main__":
    unittest.main()
