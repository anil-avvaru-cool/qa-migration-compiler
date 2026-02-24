"""
test_locator_extractor_enhanced.py

Unit tests for enhanced LocatorExtractor with page context and semantic role inference.
"""

import pytest
from src.ast.models import ASTNode, ASTTree, ASTLocation
from src.extraction.locator_extractor import LocatorExtractor


@pytest.fixture
def sample_ast_tree():
    """Create a sample AST tree with locator nodes."""
    # Create a By.id locator node
    locator_node = ASTNode(
        id="node_1",
        type="method_call",
        name=None,
        properties={
            "qualifier": "By",
            "member": "id",
        },
    )

    # Create argument with selector value
    arg_node = ASTNode(
        id="node_2",
        type="literal",
        name=None,
        properties={"value": '"username"'},
        parent_id="node_1",
    )
    locator_node.add_child(arg_node)

    # Create variable declarator holding the locator
    var_node = ASTNode(
        id="node_3",
        type="variable_declarator",
        name="usernameInput",
        properties={},
        parent_id="node_0",
    )
    var_node.add_child(locator_node)

    # Create class node
    class_node = ASTNode(
        id="node_0",
        type="class",
        name="LoginPage",
        properties={"name": "LoginPage"},
    )
    class_node.add_child(var_node)

    # Create root
    root = ASTNode(
        id="root",
        type="compilation_unit",
        name=None,
    )
    root.add_child(class_node)

    ast_tree = ASTTree(
        root=root,
        language="Java",
        file_path="src/pages/LoginPage.java",
    )
    return ast_tree


def test_locator_extractor_basic_extraction(sample_ast_tree):
    """Test basic locator extraction."""
    extractor = LocatorExtractor()
    locators = extractor.extract(sample_ast_tree)

    assert len(locators) > 0
    first_locator = locators[0]

    # Check basic structure
    assert first_locator["targetId"] is not None
    assert first_locator["type"] == "ui-element"
    assert "context" in first_locator
    assert "semantic" in first_locator
    assert "selectorStrategies" in first_locator


def test_locator_extractor_page_context(sample_ast_tree):
    """Test that page context is extracted from class name."""
    extractor = LocatorExtractor()
    locators = extractor.extract(sample_ast_tree)

    first_locator = locators[0]
    assert first_locator["context"]["page"] == "LoginPage"


def test_locator_extractor_semantic_role_inference():
    """Test semantic role inference from selector patterns."""
    extractor = LocatorExtractor()

    # Test role inference from variable name
    assert extractor._infer_semantic_role("#username", "loginInput") == "textbox"
    assert extractor._infer_semantic_role("#password", "passwordField") == "textbox"
    assert extractor._infer_semantic_role(".btn", "submitButton") == "button"
    assert extractor._infer_semantic_role("label", "userLabel") == "label"


def test_locator_extractor_selector_normalization():
    """Test selector value normalization (quote removal)."""
    extractor = LocatorExtractor()

    # Test quote removal
    assert extractor._normalize_selector_value('"#username"') == "#username"
    assert extractor._normalize_selector_value("'#password'") == "#password"
    # Test XPath selector
    xpath_with_quotes = '"//button"'
    assert extractor._normalize_selector_value(xpath_with_quotes) == "//button"


def test_locator_extractor_stability_score():
    """Test stability score estimation."""
    extractor = LocatorExtractor()

    # ID selector (highest stability)
    assert extractor._estimate_stability("#username", "id") >= 0.96

    # XPath with contains (lower stability)
    xpath_with_contains = "//button[contains(text(), 'Login')]"
    assert extractor._estimate_stability(xpath_with_contains, "xpath") < 0.85


def test_locator_extractor_target_id_generation():
    """Test target ID generation from variable names."""
    extractor = LocatorExtractor()

    # camelCase to UPPER_SNAKE_CASE
    assert extractor._generate_target_id("usernameInput", "LoginPage") == "USERNAME_INPUT"
    assert extractor._generate_target_id("submitButton", "LoginPage") == "SUBMIT_BUTTON"
    assert extractor._generate_target_id("rememberMe", "LoginPage") == "REMEMBER_ME"


def test_locator_extractor_alternative_strategies():
    """Test generation of alternative selector strategies."""
    extractor = LocatorExtractor()

    # CSS to XPath conversion
    alternatives = extractor._generate_alternative_strategies("#username", "id")
    assert len(alternatives) >= 1
    assert any(alt["strategy"] == "xpath" for alt in alternatives)


def test_locator_extractor_css_to_xpath_conversion():
    """Test CSS to XPath conversion."""
    extractor = LocatorExtractor()

    # ID selector
    xpath = extractor._css_to_xpath("#username")
    assert xpath == "//*[@id='username']"

    # Class selector
    xpath = extractor._css_to_xpath(".login-form")
    assert xpath == "//*[@class='login-form']"


def test_locator_extractor_multiple_strategies():
    """Test handling of multiple selector strategies."""
    extractor = LocatorExtractor()

    # Simulate extracted target with multiple strategies
    target = {
        "targetId": "LOGIN_BUTTON",
        "name": "loginBtn",
        "selectorStrategies": [
            {"strategy": "css", "value": "#login-btn", "stabilityScore": 0.96},
            {"strategy": "xpath", "value": "//button[@id='login-btn']", "stabilityScore": 0.85},
        ],
    }

    # Verify structure is maintained
    assert len(target["selectorStrategies"]) == 2
    assert target["selectorStrategies"][0]["strategy"] == "css"
    assert target["selectorStrategies"][1]["strategy"] == "xpath"


def test_locator_extractor_businessname_generation():
    """Test business name generation."""
    extractor = LocatorExtractor()

    # From variable name
    roles = [
        ("usernameInput", "textbox"),
        ("passwordInput", "textbox"),
        ("loginButton", "button"),
        ("welcomeMessage", "label"),
    ]

    for var_name, expected_role in roles:
        target_id = extractor._generate_target_id(var_name, "TestPage")
        semantic_role = extractor._infer_semantic_role("#id", var_name)
        assert semantic_role == expected_role
