from src.ir.models.test import TestIR, StepIR


def test_test_ir_serialization():
    step = StepIR(
        stepId="step_1",
        action="click",
        targetId="login_button"
    )

    test = TestIR(
        testId="TC_LOGIN_001",
        steps=[step]
    )

    json_output = test.model_dump_json()
    assert "TC_LOGIN_001" in json_output
    assert "click" in json_output
