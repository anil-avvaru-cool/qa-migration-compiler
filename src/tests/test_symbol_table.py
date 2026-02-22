import pytest
from src.ast.models import ASTNode, ASTTree, ASTLocation
from src.analysis.symbol_table import SymbolTable


def test_symbol_table_field_initialization():
    """Test that symbol table records field initializers with By.* locators."""

    # Build a minimal AST representing:
    # private By username = By.cssSelector("#username");

    by_locator_node = ASTNode(
        id="node_locator_1",
        type="node",
        properties={"qualifier": "By", "member": "cssSelector"},
        location=ASTLocation(start_line=3)
    )

    field_node = ASTNode(
        id="node_field_1",
        type="field",
        name="username",
        children=[by_locator_node],
        location=ASTLocation(start_line=3)
    )

    class_node = ASTNode(
        id="suite_1",
        type="suite",
        name="LoginPage",
        children=[field_node],
        location=ASTLocation(start_line=1)
    )

    ast_tree = ASTTree(
        root=class_node,
        language="java",
        file_path="LoginPage.java"
    )

    # Build symbol table
    symbol_table = SymbolTable()
    symbol_table.build_from_tree(ast_tree)

    # Verify mapping
    assert "username" in symbol_table.symbols
    assert symbol_table.symbols["username"].id == "node_locator_1"


def test_symbol_table_resolve_reference():
    """Test that symbol table resolves variable references to their initializers."""

    by_locator = ASTNode(
        id="node_locator_2",
        type="node",
        properties={"qualifier": "By", "member": "xpath"},
    )

    field_node = ASTNode(
        id="node_field_2",
        type="field",
        name="password",
        children=[by_locator],
    )

    class_node = ASTNode(
        id="suite_2",
        type="suite",
        name="LoginPage",
        children=[field_node],
    )

    ast_tree = ASTTree(
        root=class_node,
        language="java",
        file_path="LoginPage.java"
    )

    symbol_table = SymbolTable()
    symbol_table.build_from_tree(ast_tree)

    # Create a reference node
    ref_node = ASTNode(
        id="node_ref_1",
        type="node",
        name="password",
        properties={"name": "password"}
    )

    # Resolve the reference
    result = symbol_table.resolve_reference(ref_node)
    assert result is not None
    var_name, init_node = result
    assert var_name == "password"
    assert init_node.id == "node_locator_2"


def test_symbol_table_resolve_step_target():
    """Test step target resolution from a method call statement."""

    by_locator = ASTNode(
        id="node_locator_3",
        type="node",
        properties={"qualifier": "By", "member": "id"},
    )

    field_node = ASTNode(
        id="node_field_3",
        type="field",
        name="loginButton",
        children=[by_locator],
    )

    class_node = ASTNode(
        id="suite_3",
        type="suite",
        name="LoginPage",
        children=[field_node],
    )

    ast_tree = ASTTree(
        root=class_node,
        language="java",
        file_path="LoginPage.java"
    )

    symbol_table = SymbolTable()
    symbol_table.build_from_tree(ast_tree)

    # Create a statement node with a reference to loginButton
    ref_node = ASTNode(
        id="node_ref_2",
        type="node",
        name="loginButton",
        properties={"name": "loginButton"}
    )

    action_node = ASTNode(
        id="node_action_1",
        type="node",
        properties={"member": "click"},
        children=[ref_node]
    )

    # Resolve the target
    result = symbol_table.resolve_step_target(action_node)
    assert result is not None
    target_name, target_node_id = result
    assert target_name == "loginButton"
    assert target_node_id == "node_locator_3"


def test_symbol_table_multiple_fields():
    """Test symbol table with multiple field initializers."""

    fields = [
        ASTNode(
            id=f"node_field_{i}",
            type="field",
            name=name,
            children=[
                ASTNode(
                    id=f"node_locator_{i}",
                    type="node",
                    properties={"qualifier": "By", "member": strategy},
                )
            ]
        )
        for i, (name, strategy) in enumerate([
            ("username", "cssSelector"),
            ("password", "xpath"),
            ("loginBtn", "id"),
        ])
    ]

    class_node = ASTNode(
        id="suite_4",
        type="suite",
        name="LoginPage",
        children=fields,
    )

    ast_tree = ASTTree(
        root=class_node,
        language="java",
        file_path="LoginPage.java"
    )

    symbol_table = SymbolTable()
    symbol_table.build_from_tree(ast_tree)

    # Verify all symbols are recorded
    assert len(symbol_table.symbols) == 3
    assert "username" in symbol_table.symbols
    assert "password" in symbol_table.symbols
    assert "loginBtn" in symbol_table.symbols
