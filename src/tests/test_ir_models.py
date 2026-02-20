from src.ir.models.test import TestIR, StepIR


def test_test_ir_serialization():
    step = StepIR(
        id="step_1",
        type="action",
        name="click",
        target="login_button"
    )

    test = TestIR(
        id="TC_LOGIN_001",
        name="Valid Login",
        steps=[step]
    )

    json_output = test.model_dump_json()
    assert "TC_LOGIN_001" in json_output
    assert "click" in json_output
