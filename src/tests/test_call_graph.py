from src.ast.models import ASTNode, ASTTree
from src.analysis.call_graph import CallGraphBuilder


def test_call_graph_basic():
    # method foo calls bar
    bar = ASTNode(id="n_bar", type="node", name="bar", children=[])
    call = ASTNode(id="c1", type="node", properties={"member": "bar"}, children=[])
    foo = ASTNode(id="n_foo", type="node", name="foo", children=[])

    root = ASTNode(id="r", type="suite", name="Root", children=[])
    # attach using add_child to ensure parent_id is set
    root.add_child(foo)
    root.add_child(bar)
    foo.add_child(call)

    tree = ASTTree(root=root, language="java", file_path="Root.java")

    builder = CallGraphBuilder([tree])
    callees = builder.callees("foo")
    assert "bar" in callees
