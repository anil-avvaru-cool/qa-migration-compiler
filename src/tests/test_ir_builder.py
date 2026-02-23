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

    assert test_ir.name == "Valid Login"
    assert len(test_ir.steps) == 1
    assert test_ir.steps[0].name == "click"
    assert test_ir.steps[0].targetNameId == "login_button"
    assert test_ir.steps[0].targetNodeId == "node_5"
