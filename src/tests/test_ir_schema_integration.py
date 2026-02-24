"""
test_ir_schema_integration.py

Integration tests for end-to-end IR schema correctness.
"""

import pytest
import json
from src.extraction.locator_extractor import LocatorExtractor
from src.extraction.action_mapper import ActionMapper
from src.extraction.step_enricher import StepEnricher
from src.ir.builder.targets_ir_builder import TargetsIRBuilder
from src.ir.builder.test_ir_builder import TestIRBuilder


def test_integration_login_test_ir_schema():
    """
    Integration test: Simulate full flow from extraction to IR generation
    for a login test matching expected schema.
    """

    # Step 1: Simulate extracted targets from LoginPage.java
    extracted_targets = [
        {
            "targetId": "LOGIN_USERNAME",
            "name": "usernameInput",
            "type": "ui-element",
            "context": {"page": "LoginPage"},
            "semantic": {"role": "textbox", "businessName": "Username Input"},
            "selectorStrategies": [
                {"strategy": "css", "value": "#username", "stabilityScore": 0.96},
                {"strategy": "xpath", "value": "//*[@id='username']", "stabilityScore": 0.85},
            ],
            "preferredStrategy": "css",
        },
        {
            "targetId": "LOGIN_PASSWORD",
            "name": "passwordInput",
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
            "name": "loginBtn",
            "type": "ui-element",
            "context": {"page": "LoginPage"},
            "semantic": {"role": "button", "businessName": "Login Button"},
            "selectorStrategies": [
                {"strategy": "css", "value": "#login-btn", "stabilityScore": 0.94}
            ],
            "preferredStrategy": "css",
        },
        {
            "targetId": "WELCOME_MESSAGE",
            "name": "welcomeTxt",
            "type": "ui-element",
            "context": {"page": "HomePage"},
            "semantic": {"role": "label", "businessName": "Welcome Message"},
            "selectorStrategies": [
                {"strategy": "css", "value": "#welcome-msg", "stabilityScore": 0.98}
            ],
            "preferredStrategy": "css",
        },
    ]

    # Step 2: Build targets IR
    targets_builder = TargetsIRBuilder()
    targets_ir = targets_builder.build(extracted_targets)

    assert len(targets_ir) == 4
    for target in targets_ir:
        assert target.type == "ui-element"
        assert target.context.page in ("LoginPage", "HomePage")
        for strategy in target.selectorStrategies:
            # Verify no quotes in selector
            assert not strategy.value.startswith('"')
            assert not strategy.value.startswith("'")

    # Step 3: Simulate extracted steps from ActionMapper
    extracted_steps = [
        {
            "action": "navigate",
            "target": {"type": "url", "value": "qa:/login"},
        },
        {
            "action": "type",
            "target_name_id": "usernameInput",
            "input": {"source": "data", "field": "username"},
        },
        {
            "action": "type",
            "target_name_id": "passwordInput",
            "input": {"source": "data", "field": "password", "masked": True},
        },
        {
            "action": "click",
            "target_name_id": "loginBtn",
        },
    ]

    # Step 4: Enrich steps with target linking
    enricher = StepEnricher(extracted_targets)
    enriched_steps = enricher.enrich(extracted_steps)

    assert len(enriched_steps) == 4
    assert enriched_steps[0]["action"] == "navigate"
    assert enriched_steps[1]["targetId"] == "LOGIN_USERNAME"
    assert enriched_steps[2]["targetId"] == "LOGIN_PASSWORD"
    assert enriched_steps[3]["targetId"] == "LOGIN_BUTTON"

    # Step 5: Build test IR
    test_builder = TestIRBuilder()
    test_ir = test_builder.build(
        test_id="TC_LOGIN_VALID_001",
        suite_id="AUTH_SUITE",
        priority="P1",
        severity="Critical",
        data_binding={
            "dataSetId": "LOGIN_DATA",
            "iterationStrategy": "row-wise",
        },
        steps=enriched_steps,
        assertions=[
            {
                "type": "equals",
                "actual": {"source": "ui", "targetId": "WELCOME_MESSAGE"},
                "expected": {"source": "data", "field": "expectedMessage"},
            }
        ],
    )

    # Verify complete schema
    assert test_ir.testId == "TC_LOGIN_VALID_001"
    assert test_ir.suiteId == "AUTH_SUITE"
    assert test_ir.priority == "P1"
    assert test_ir.severity == "Critical"
    assert test_ir.dataBinding.dataSetId == "LOGIN_DATA"

    # Verify steps structure
    assert len(test_ir.steps) == 4
    assert test_ir.steps[0].action == "navigate"
    assert test_ir.steps[0].target is not None
    assert test_ir.steps[0].target.type == "url"

    assert test_ir.steps[1].action == "type"
    assert test_ir.steps[1].targetId == "LOGIN_USERNAME"
    assert test_ir.steps[1].input is not None
    assert test_ir.steps[1].input.source == "data"
    assert test_ir.steps[1].input.field == "username"

    assert test_ir.steps[3].targetId == "LOGIN_BUTTON"

    # Verify assertions
    assert len(test_ir.assertions) == 1
    assert test_ir.assertions[0].type == "equals"
    assert test_ir.assertions[0].actual.source == "ui"
    assert test_ir.assertions[0].actual.targetId == "WELCOME_MESSAGE"


def test_integration_order_test_ir_schema():
    """
    Integration test for order/checkout flow matching expected schema.
    """

    # Extracted targets for order flow
    extracted_targets = [
        {
            "targetId": "ORDER_PRODUCT_SEARCH",
            "name": "searchInput",
            "type": "ui-element",
            "context": {"page": "OrderPage"},
            "semantic": {"role": "textbox", "businessName": "Product Search Input"},
            "selectorStrategies": [
                {"strategy": "css", "value": "#search-product", "stabilityScore": 0.93}
            ],
            "preferredStrategy": "css",
        },
        {
            "targetId": "ORDER_ADD_TO_CART",
            "name": "addToCartBtn",
            "type": "ui-element",
            "context": {"page": "OrderPage"},
            "semantic": {"role": "button", "businessName": "Add To Cart Button"},
            "selectorStrategies": [
                {"strategy": "css", "value": ".add-to-cart", "stabilityScore": 0.91}
            ],
            "preferredStrategy": "css",
        },
        {
            "targetId": "ORDER_CONFIRMATION_MSG",
            "name": "confirmMsg",
            "type": "ui-element",
            "context": {"page": "OrderConfirmationPage"},
            "semantic": {"role": "label", "businessName": "Order Confirmation Message"},
            "selectorStrategies": [
                {"strategy": "css", "value": "#order-confirm-msg", "stabilityScore": 0.97}
            ],
            "preferredStrategy": "css",
        },
    ]

    # Build targets
    targets_builder = TargetsIRBuilder()
    targets_ir = targets_builder.build(extracted_targets)
    assert len(targets_ir) == 3

    # Extracted steps
    extracted_steps = [
        {"action": "navigate", "target": {"type": "url", "value": "qa:/orders"}},
        {
            "action": "type",
            "target_name_id": "searchInput",
            "input": {"source": "data", "field": "productName"},
        },
        {
            "action": "click",
            "target_name_id": "addToCartBtn",
        },
    ]

    # Enrich steps
    enricher = StepEnricher(extracted_targets)
    enriched_steps = enricher.enrich(extracted_steps)

    assert len(enriched_steps) == 3
    assert enriched_steps[1]["targetId"] == "ORDER_PRODUCT_SEARCH"
    assert enriched_steps[2]["targetId"] == "ORDER_ADD_TO_CART"

    # Build test IR
    test_builder = TestIRBuilder()
    test_ir = test_builder.build(
        test_id="TC_ORDER_CREATE_001",
        suite_id="ORDER_SUITE",
        priority="P1",
        severity="High",
        data_binding={
            "dataSetId": "ORDER_DATA",
            "iterationStrategy": "row-wise",
        },
        steps=enriched_steps,
        assertions=[
            {
                "type": "equals",
                "actual": {"source": "ui", "targetId": "ORDER_CONFIRMATION_MSG"},
                "expected": {"source": "data", "field": "expectedConfirmation"},
            }
        ],
    )

    # Verify schema
    assert test_ir.testId == "TC_ORDER_CREATE_001"
    assert test_ir.suiteId == "ORDER_SUITE"
    assert len(test_ir.steps) == 3
    assert test_ir.steps[0].action == "navigate"
    assert test_ir.steps[1].input.field == "productName"


def test_targets_json_schema_compliance():
    """Test that generated targets match expected JSON schema."""

    targets_config = [
        {
            "targetId": "LOGIN_USERNAME",
            "type": "ui-element",
            "context": {"page": "LoginPage"},
            "semantic": {"role": "textbox", "businessName": "Username Input"},
            "selectorStrategies": [
                {"strategy": "css", "value": "#username", "stabilityScore": 0.96}
            ],
            "preferredStrategy": "css",
        }
    ]

    builder = TargetsIRBuilder()
    targets_ir = builder.build(targets_config)

    target = targets_ir[0]

    # Verify all expected fields
    assert hasattr(target, "targetId")
    assert hasattr(target, "type")
    assert hasattr(target, "context")
    assert hasattr(target, "semantic")
    assert hasattr(target, "selectorStrategies")
    assert hasattr(target, "preferredStrategy")

    # Verify context structure
    assert target.context.page == "LoginPage"

    # Verify semantic structure
    assert target.semantic.role == "textbox"
    assert target.semantic.businessName == "Username Input"

    # Verify strategies
    assert len(target.selectorStrategies) == 1
    strategy = target.selectorStrategies[0]
    assert strategy.strategy == "css"
    assert strategy.value == "#username"
    assert strategy.stabilityScore == 0.96


def test_test_json_schema_compliance():
    """Test that generated tests match expected JSON schema."""

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
    ]

    assertions = [
        {
            "type": "equals",
            "actual": {"source": "ui", "targetId": "WELCOME_MESSAGE"},
            "expected": {"source": "data", "field": "expectedMessage"},
        }
    ]

    builder = TestIRBuilder()
    test_ir = builder.build(
        test_id="TC_LOGIN_VALID_001",
        suite_id="AUTH_SUITE",
        priority="P1",
        severity="Critical",
        data_binding={"dataSetId": "LOGIN_DATA", "iterationStrategy": "row-wise"},
        steps=steps,
        assertions=assertions,
    )

    # Verify all expected fields
    assert hasattr(test_ir, "testId")
    assert hasattr(test_ir, "suiteId")
    assert hasattr(test_ir, "priority")
    assert hasattr(test_ir, "severity")
    assert hasattr(test_ir, "dataBinding")
    assert hasattr(test_ir, "steps")
    assert hasattr(test_ir, "assertions")

    # Verify step structure
    first_step = test_ir.steps[0]
    assert hasattr(first_step, "stepId")
    assert hasattr(first_step, "action")
    assert hasattr(first_step, "target")

    # Verify assertion structure
    first_assertion = test_ir.assertions[0]
    assert hasattr(first_assertion, "assertId")
    assert hasattr(first_assertion, "type")
    assert hasattr(first_assertion, "actual")
    assert hasattr(first_assertion, "expected")
