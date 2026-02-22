import pytest
from src.parser.java.java_ast_adapter import JavaASTAdapter


# ------------------------------------------
# Fake Java Parser Nodes
# ------------------------------------------

class FakeAnnotation:
    def __init__(self, name):
        self.name = name


class MethodDeclaration:
    def __init__(self, name, annotations=None, line=None):
        self.name = name
        self.annotations = annotations or []
        self.line = line


class ClassDeclaration:
    def __init__(self, name, methods=None, line=None):
        self.name = name
        self.methods = methods or []
        self.line = line


# ------------------------------------------
# Test
# ------------------------------------------

def test_java_ast_adapter_suite_and_test_types():

    test_method = MethodDeclaration(
        name="shouldLogin",
        annotations=[FakeAnnotation("Test")],
        line=10
    )

    normal_method = MethodDeclaration(
        name="helperMethod",
        annotations=[],
        line=20
    )

    clazz = ClassDeclaration(
        name="LoginTest",
        methods=[test_method, normal_method],
        line=1
    )

    adapter = JavaASTAdapter()
    root = adapter.adapt(clazz)

    nodes = root.walk()

    # 1️⃣ Root should be suite
    assert root.type == "suite"

    # 2️⃣ Exactly one test node
    test_nodes = [n for n in nodes if n.type == "test"]
    assert len(test_nodes) == 1
    assert test_nodes[0].name == "shouldLogin"

    # 3️⃣ IDs must be unique
    ids = [n.id for n in nodes]
    assert len(ids) == len(set(ids))

    # 4️⃣ Parent integrity
    for node in nodes:
        for child in node.children:
            assert child.parent_id == node.id
            assert child.id != node.id

    # 5️⃣ Structure validation
    for node in nodes:
        node.validate_structure()
