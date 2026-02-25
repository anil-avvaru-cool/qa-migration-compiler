"""
test_step_enricher.py

Unit tests for StepEnricher with step-to-target linking and input resolution.
"""

import pytest
from src.extraction.step_enricher import StepEnricher


@pytest.fixture
def sample_targets():
    """Create sample extracted targets."""
    return [
        {
            "targetId": "LOGIN_USERNAME",
            "name": "usernameInput",
            "type": "ui-element",
            "context": {"page": "LoginPage"},
            "semantic": {"role": "textbox", "businessName": "Username Input"},
            "selectorStrategies": [
                {"strategy": "css", "value": "#username", "stabilityScore": 0.96}
            ],
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
        },
    ]


@pytest.fixture
def enricher(sample_targets):
    """Create a StepEnricher instance with sample targets."""
    return StepEnricher(sample_targets)


def test_step_enricher_initialization(enricher, sample_targets):
    """Test StepEnricher initialization with target mapping."""
    assert len(enricher.targets_by_id) == 3
    assert len(enricher.targets_by_name) == 3
    assert "LOGIN_USERNAME" in enricher.targets_by_id
    assert "usernameInput" in enricher.targets_by_name


def test_step_enricher_resolve_target_id_direct(enricher):
    """Test target ID resolution when already present."""
    step = {"action": "type", "targetId": "LOGIN_USERNAME"}

    resolved_id = enricher._resolve_target_id(step)
    assert resolved_id == "LOGIN_USERNAME"


def test_step_enricher_resolve_target_id_by_name(enricher):
    """Test target ID resolution from target name."""
    step = {"action": "type", "target_name_id": "usernameInput"}

    resolved_id = enricher._resolve_target_id(step)
    assert resolved_id == "LOGIN_USERNAME"


def test_step_enricher_resolve_target_id_fuzzy(enricher):
    """Test fuzzy target ID resolution (camelCase to SNAKE_CASE)."""
    step = {"action": "type", "target_name_id": "passwordInput"}

    resolved_id = enricher._resolve_target_id(step)
    assert resolved_id == "LOGIN_PASSWORD"


def test_step_enricher_build_step_input_data_source(enricher):
    """Test building step input with data source."""
    step = {
        "action": "type",
        "input": {"source": "data", "field": "username", "masked": False},
    }

    input_spec = enricher._build_step_input(step)

    assert input_spec is not None
    assert input_spec["source"] == "data"
    assert input_spec["field"] == "username"
    assert input_spec["masked"] == False


def test_step_enricher_build_step_input_constant(enricher):
    """Test building step input with constant value."""
    step = {
        "action": "type",
        "input": {"source": "constant", "value": "default_value"},
    }

    input_spec = enricher._build_step_input(step)

    assert input_spec is not None
    assert input_spec["source"] == "constant"


def test_step_enricher_infer_data_field_by_target_name(enricher):
    """Test inferring data field from target ID."""
    step = {"targetId": "LOGIN_USERNAME", "action": "type"}
    test_data = {"username": "testuser", "password": "testpass"}

    field = enricher._infer_data_field(step, test_data)
    assert field == "username"


def test_step_enricher_infer_data_field_password(enricher):
    """Test inferring password field."""
    step = {"targetId": "LOGIN_PASSWORD", "action": "type"}
    test_data = {"username": "testuser", "password": "testpass"}

    field = enricher._infer_data_field(step, test_data)
    assert field == "password"


def test_step_enricher_should_mask_field_password(enricher):
    """Test that sensitive fields are marked for masking."""
    assert enricher._should_mask_field("password") == True
    assert enricher._should_mask_field("cvv") == True
    assert enricher._should_mask_field("username") == False
    assert enricher._should_mask_field("email") == False


def test_step_enricher_enrich_single_step(enricher):
    """Test enriching a single step."""
    step = {
        "action": "type",
        "target_name_id": "usernameInput",
        "input": {"source": "data", "field": "username"},
    }

    enriched = enricher._enrich_step(step, step_index=1)

    assert enriched is not None
    assert enriched["stepId"] == "STEP_01"
    assert enriched["action"] == "type"
    assert enriched["targetId"] == "LOGIN_USERNAME"
    assert enriched["input"]["source"] == "data"


def test_step_enricher_enrich_navigate_step(enricher):
    """Test enriching a navigate step."""
    step = {
        "action": "navigate",
        "target": {"type": "url", "value": "qa:/login"},
    }

    enriched = enricher._enrich_step(step, step_index=1)

    assert enriched is not None
    assert enriched["action"] == "navigate"
    assert enriched["target"]["type"] == "url"
    assert "login" in enriched["target"]["value"].lower()


def test_step_enricher_enrich_click_step(enricher):
    """Test enriching a click step."""
    step = {
        "action": "click",
        "target_name_id": "loginBtn",
    }

    enriched = enricher._enrich_step(step, step_index=3)

    assert enriched is not None
    assert enriched["stepId"] == "STEP_03"
    assert enriched["action"] == "click"
    assert enriched["targetId"] == "LOGIN_BUTTON"


def test_step_enricher_enrich_multiple_steps(enricher):
    """Test enriching a sequence of steps."""
    steps = [
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
            "input": {"source": "data", "field": "password"},
        },
        {
            "action": "click",
            "target_name_id": "loginBtn",
        },
    ]

    enriched_steps = enricher.enrich(steps)

    assert len(enriched_steps) == 4
    assert enriched_steps[0]["action"] == "navigate"
    assert enriched_steps[1]["targetId"] == "LOGIN_USERNAME"
    assert enriched_steps[2]["targetId"] == "LOGIN_PASSWORD"
    assert enriched_steps[3]["targetId"] == "LOGIN_BUTTON"


def test_step_enricher_step_numbering(enricher):
    """Test that steps are numbered correctly."""
    steps = [
        {"action": "navigate", "target": {"type": "url", "value": "qa:/login"}},
        {"action": "type", "target_name_id": "usernameInput"},
        {"action": "click", "target_name_id": "loginBtn"},
    ]

    enriched_steps = enricher.enrich(steps)

    for i, step in enumerate(enriched_steps, 1):
        assert step["stepId"] == f"STEP_{i:02d}"


def test_step_enricher_match_test_data_fields(enricher):
    """Test matching step inputs to test data."""
    steps = [
        {
            "stepId": "STEP_01",
            "action": "type",
            "targetId": "LOGIN_USERNAME",
            "input": {"source": "constant", "value": "testuser"},
        },
        {
            "stepId": "STEP_02",
            "action": "type",
            "targetId": "LOGIN_PASSWORD",
            "input": {"source": "constant", "value": "testpass"},
        },
    ]

    test_data = {"username": "testuser", "password": "testpass"}

    matched_steps = enricher.match_test_data_fields(steps, test_data)

    # First step should match to username
    assert matched_steps[0]["input"]["source"] == "data"
    assert matched_steps[0]["input"]["field"] == "username"

    # Second step should be masked
    assert matched_steps[1]["input"]["masked"] == True
