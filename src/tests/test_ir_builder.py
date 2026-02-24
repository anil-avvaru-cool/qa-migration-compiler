from src.ir.builder.test_ir_builder import TestIRBuilder


def test_test_ir_builder():
    extracted = {
        "name": "Valid Login",
        "steps": [
            {
                "type": "action",
                "name": "click",
                "target_name_id": "login_button",
                "target_node_id": "node_5",
                "parameters": {"timeout": 5}
            }
        ],
        "tags": ["smoke"]
    }

    builder = TestIRBuilder()
    test_ir = builder.build(extracted)

    assert test_ir.name == "Valid Login"  # Uses the @property alias for testId
    assert len(test_ir.steps) == 1
    assert test_ir.steps[0].action == "click"  # StepIR has "action" not "name"
    assert test_ir.steps[0].targetId == "login_button"  # Resolved from target_name_id mapping
    assert test_ir.tags == ["smoke"]
