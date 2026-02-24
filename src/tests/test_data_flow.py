from src.ast.models import ASTNode, ASTTree
from src.analysis.data_flow import DataFlowAnalyzer


def test_data_flow_locator_find():
    locator = ASTNode(id="loc1", type="node", properties={"qualifier": "By", "member": "id"})
    field = ASTNode(id="f1", type="field", name="loginBtn", children=[locator])
    root = ASTNode(id="r", type="suite", name="Page", children=[field])
    tree = ASTTree(root=root, language="java", file_path="Page.java")

    dfa = DataFlowAnalyzer([tree])
    found = dfa.find_locator_for_symbol("loginBtn")
    assert found is not None
    assert found.id == "loc1"
