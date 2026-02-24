from src.ast.models import ASTNode, ASTTree
from src.analysis.wrapper_expansion import WrapperExpander


def test_wrapper_chain_multi_level():
    # a -> b -> c
    c = ASTNode(id="n_c", type="node", name="c", children=[])
    call_b = ASTNode(id="call_b", type="node", properties={"member": "b"}, children=[])
    b = ASTNode(id="n_b", type="node", name="b", children=[ASTNode(id="call_c", type="node", properties={"member": "c"})])
    a = ASTNode(id="n_a", type="node", name="a", children=[call_b])

    root = ASTNode(id="r", type="suite", name="Root", children=[a, b, c])
    tree = ASTTree(root=root, language="java", file_path="Root.java")

    expander = WrapperExpander([tree])
    chain = expander.find_wrapper_chain("a", depth_limit=5)
    assert chain[0] == "a"
    assert "c" in chain
