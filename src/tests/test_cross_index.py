from src.ast.models import ASTNode, ASTTree
from src.ast.cross_index import CrossASTIndex


def test_cross_index_basic():
    n1 = ASTNode(id="a1", type="suite", name="A", children=[])
    n2 = ASTNode(id="m1", type="node", name="m", children=[], parent_id="a1")
    n1.children.append(n2)

    tree1 = ASTTree(root=n1, language="java", file_path="A.java")

    idx = CrossASTIndex([tree1])
    assert idx.get("a1") is not None
    assert len(idx.by_type("node")) >= 1
