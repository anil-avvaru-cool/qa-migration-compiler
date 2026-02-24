from src.ast.models import ASTNode, ASTTree
from src.analysis.type_hierarchy import TypeHierarchyResolver


def test_type_hierarchy_simple():
    # class B extends A
    a = ASTNode(id="suite_a", type="suite", name="A", children=[])
    b = ASTNode(id="suite_b", type="suite", name="B", children=[], properties={"extends": "A"})

    tree = ASTTree(root=a, language="java", file_path="A.java")
    # attach B as separate root for the test harness
    tree2 = ASTTree(root=b, language="java", file_path="B.java")

    resolver = TypeHierarchyResolver([tree, tree2])
    assert resolver.get_parents("B") == ["A"]
    assert resolver.get_children("A") == ["B"]
    assert "B" in resolver.linearized_mro("B")
