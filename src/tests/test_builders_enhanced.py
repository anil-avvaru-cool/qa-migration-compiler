"""Unit tests for IR builders with enhanced schema."""

import unittest
from datetime import datetime

from src.ir.builder.project_ir_builder import ProjectIRBuilder
from src.ir.builder.targets_ir_builder import TargetsIRBuilder
from src.ir.builder.test_ir_builder import TestIRBuilder
from src.ir.builder.suite_ir_builder import SuiteIRBuilder


class TestProjectIRBuilder(unittest.TestCase):
    """Test ProjectIRBuilder."""

    def setUp(self):
        self.builder = ProjectIRBuilder()

    def test_build_basic_project(self):
        """Test building a basic project IR."""
        project = self.builder.build(
            project_name="EcommerceAutomation",
            source_framework="Selenium-Java-TestNG",
            target_framework="Playwright-TS",
        )

        self.assertEqual(project.projectName, "EcommerceAutomation")
        self.assertEqual(project.sourceFramework, "Selenium-Java-TestNG")
        self.assertEqual(project.targetFramework, "Playwright-TS")
        self.assertEqual(project.irVersion, "2.0.0")

    def test_build_with_all_parameters(self):
        """Test building project with all parameters."""
        project = self.builder.build(
            project_name="TestProject",
            source_framework="Selenium-Java",
            target_framework="Playwright-Python",
            architecture_pattern="POJO",
            supports_parallel=False,
            created_on="2026-02-22",
        )

        self.assertEqual(project.architecturePattern, "POJO")
        self.assertFalse(project.supportsParallel)
        self.assertEqual(project.createdOn, "2026-02-22")

    def test_project_serialization(self):
        """Test project IR serializes correctly."""
        project = self.builder.build(
            project_name="TestProject",
            source_framework="Selenium-Java-TestNG",
            target_framework="Playwright-TS",
        )

        json_str = project.model_dump_json()
        self.assertIn("TestProject", json_str)
        self.assertIn("2.0.0", json_str)


class TestTargetsIRBuilder(unittest.TestCase):
    """Test TargetsIRBuilder."""

    def setUp(self):
        self.builder = TargetsIRBuilder()

    def test_build_single_target(self):
        """Test building a single target."""
        targets = self.builder.build(
            [
                {
                    "targetId": "LOGIN_USERNAME",
                    "type": "ui-element",
                    "context": {"page": "LoginPage"},
                    "semantic": {
                        "role": "textbox",
                        "businessName": "Username Input",
                    },
                    "selectorStrategies": [
                        {
                            "strategy": "css",
                            "value": "#username",
                            "stabilityScore": 0.96,
                        }
                    ],
                    "preferredStrategy": "css",
                }
            ]
        )

        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0].targetId, "LOGIN_USERNAME")
        self.assertEqual(targets[0].semantic.businessName, "Username Input")

    def test_build_multiple_targets(self):
        """Test building multiple targets."""
        targets = self.builder.build(
            [
                {
                    "targetId": "LOGIN_USERNAME",
                    "type": "ui-element",
                    "context": {"page": "LoginPage"},
                    "semantic": {
                        "role": "textbox",
                        "businessName": "Username Input",
                    },
                    "selectorStrategies": [
                        {
                            "strategy": "css",
                            "value": "#username",
                            "stabilityScore": 0.96,
                        }
                    ],
                },
                {
                    "targetId": "LOGIN_PASSWORD",
                    "type": "ui-element",
                    "context": {"page": "LoginPage"},
                    "semantic": {
                        "role": "textbox",
                        "businessName": "Password Input",
                    },
                    "selectorStrategies": [
                        {
                            "strategy": "css",
                            "value": "#password",
                            "stabilityScore": 0.97,
                        }
                    ],
                },
            ]
        )

        self.assertEqual(len(targets), 2)

    def test_build_target_serialization(self):
        """Test target IR serializes correctly."""
        targets = self.builder.build(
            [
                {
                    "targetId": "LOGIN_BUTTON",
                    "type": "ui-element",
                    "context": {"page": "LoginPage"},
                    "semantic": {
                        "role": "button",
                        "businessName": "Login Button",
                    },
                    "selectorStrategies": [
                        {
                            "strategy": "css",
                            "value": "#login-btn",
                            "stabilityScore": 0.94,
                        }
                    ],
                }
            ]
        )

        json_str = targets[0].model_dump_json()
        self.assertIn("LOGIN_BUTTON", json_str)
        self.assertIn("login-btn", json_str)


class TestTestIRBuilder(unittest.TestCase):
    """Test TestIRBuilder."""

    def setUp(self):
        self.builder = TestIRBuilder()

    def test_build_basic_test(self):
        """Test building a basic test."""
        test = self.builder.build(
            test_id="TC_LOGIN_001",
            steps=[
                {
                    "stepId": "STEP_01",
                    "action": "navigate",
                    "target": {"type": "url", "value": "qa:/login"},
                },
                {
                    "stepId": "STEP_02",
                    "action": "click",
                    "targetId": "LOGIN_BUTTON",
                },
            ],
            suite_id="AUTH_SUITE",
            priority="P1",
            severity="Critical",
        )

        self.assertEqual(test.testId, "TC_LOGIN_001")
        self.assertEqual(test.suiteId, "AUTH_SUITE")
        self.assertEqual(len(test.steps), 2)
        self.assertEqual(test.priority, "P1")

    def test_build_test_with_data_binding(self):
        """Test building test with data binding."""
        test = self.builder.build(
            test_id="TC_LOGIN_001",
            steps=[
                {
                    "stepId": "STEP_01",
                    "action": "type",
                    "targetId": "USERNAME",
                    "input": {"source": "data", "field": "username"},
                }
            ],
            data_binding={
                "dataSetId": "LOGIN_DATA",
                "iterationStrategy": "row-wise",
            },
        )

        self.assertIsNotNone(test.dataBinding)
        self.assertEqual(test.dataBinding.dataSetId, "LOGIN_DATA")

    def test_build_test_with_assertions(self):
        """Test building test with assertions."""
        test = self.builder.build(
            test_id="TC_LOGIN_001",
            steps=[
                {
                    "stepId": "STEP_01",
                    "action": "click",
                    "targetId": "LOGIN_BUTTON",
                }
            ],
            assertions=[
                {
                    "assertId": "ASSERT_01",
                    "type": "equals",
                    "actual": {"source": "ui", "targetId": "WELCOME_MSG"},
                    "expected": {"source": "data", "field": "expectedMessage"},
                }
            ],
        )

        self.assertEqual(len(test.assertions), 1)
        self.assertEqual(test.assertions[0].type, "equals")

    def test_test_serialization(self):
        """Test test IR serializes correctly."""
        test = self.builder.build(
            test_id="TC_TEST_001",
            steps=[
                {
                    "stepId": "STEP_01",
                    "action": "click",
                    "targetId": "BUTTON",
                }
            ],
        )

        json_str = test.model_dump_json()
        self.assertIn("TC_TEST_001", json_str)
        self.assertIn("STEP_01", json_str)


class TestSuiteIRBuilder(unittest.TestCase):
    """Test SuiteIRBuilder."""

    def setUp(self):
        self.builder = SuiteIRBuilder()

    def test_build_suite(self):
        """Test building a suite."""
        suite = self.builder.build(
            suite_id="AUTH_SUITE",
            tests=["TC_LOGIN_001", "TC_LOGOUT_001"],
            description="Authentication Tests",
        )

        self.assertEqual(suite.suiteId, "AUTH_SUITE")
        self.assertEqual(suite.description, "Authentication Tests")
        self.assertEqual(len(suite.tests), 2)

    def test_suite_serialization(self):
        """Test suite IR serializes correctly."""
        suite = self.builder.build(
            suite_id="TEST_SUITE",
            tests=["TC_001"],
            description="Test Suite",
        )

        json_str = suite.model_dump_json()
        self.assertIn("TEST_SUITE", json_str)
        self.assertIn("Test Suite", json_str)


class TestBuildersIntegration(unittest.TestCase):
    """Integration tests for builders working together."""

    def test_build_complete_test_structure(self):
        """Test building complete test structure."""
        project_builder = ProjectIRBuilder()
        suite_builder = SuiteIRBuilder()
        test_builder = TestIRBuilder()
        target_builder = TargetsIRBuilder()

        # Build project
        project = project_builder.build(
            project_name="EcommerceAutomation",
            source_framework="Selenium-Java-TestNG",
            target_framework="Playwright-TS",
        )

        # Build targets
        targets = target_builder.build(
            [
                {
                    "targetId": "LOGIN_BUTTON",
                    "type": "ui-element",
                    "context": {"page": "LoginPage"},
                    "semantic": {
                        "role": "button",
                        "businessName": "Login Button",
                    },
                    "selectorStrategies": [
                        {
                            "strategy": "css",
                            "value": "#login-btn",
                            "stabilityScore": 0.94,
                        }
                    ],
                }
            ]
        )

        # Build test
        test = test_builder.build(
            test_id="TC_LOGIN_001",
            steps=[
                {
                    "stepId": "STEP_01",
                    "action": "click",
                    "targetId": "LOGIN_BUTTON",
                }
            ],
            suite_id="AUTH_SUITE",
        )

        # Build suite
        suite = suite_builder.build(
            suite_id="AUTH_SUITE",
            tests=["TC_LOGIN_001"],
            description="Authentication Tests",
        )

        # Verify all structures are valid
        self.assertIsNotNone(project)
        self.assertEqual(len(targets), 1)
        self.assertEqual(test.testId, "TC_LOGIN_001")
        self.assertEqual(suite.suiteId, "AUTH_SUITE")


if __name__ == "__main__":
    unittest.main()
